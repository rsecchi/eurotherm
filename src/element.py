from functools import cached_property
from math import ceil, cos, pi, sin, sqrt
from typing import Optional
from ezdxf.entities.lwpolyline import LWPolyline
from ezdxf.math import Vec2, intersection_line_line_2d
from geometry import dist, poly_t
from reference_frame import ReferenceFrame
from settings import Config


class Element:
	def __init__(self, poly:LWPolyline):

		self.color = poly.dxf.color
		self.poly = poly
		self.clockwise = False

		if poly.has_arc:
			p = self.points = []
			next_point = next(poly.vertices())

			for entity in poly.virtual_entities():

				if entity.dxftype() == "LINE":
					point = entity.dxf.start[0], entity.dxf.start[1]
					p.append(point)
					next_point = entity.dxf.end[0], entity.dxf.end[1]

				if entity.dxftype() == "ARC":

					angle1 = entity.dxf.start_angle
					angle2 = entity.dxf.end_angle
					radius = entity.dxf.radius
					cx, cy = entity.dxf.center.x, entity.dxf.center.y
					arc = angle2 - angle1
					while arc < 0:
						arc += 360
					arc = arc % 360
					num_points = ceil(arc/Config.arc_step_deg) + 1

					start = entity.start_point[0], entity.start_point[1]
					end = entity.end_point[0], entity.end_point[1]

					angles = list(entity.angles(num_points))

					if dist(next_point, start) > dist(next_point, end):
						angles.reverse()
					
					for angle in angles[:-1]:
						x = radius*cos(angle/180*pi) + cx
						y = radius*sin(angle/180*pi) + cy
						point = (x, y)
						p.append((x, y))
						next_point = point

		else:
			p = self.points = list(poly.vertices())	

		if (poly.is_closed):
			self.points.append((p[0][0], p[0][1]))

		self.initialize()


	@classmethod
	def from_points(cls, points: poly_t) -> "Element":

		obj = cls.__new__(cls)
		obj.points = points
		obj.color = 0
		cls.initialize(obj)

		return obj


	def initialize(self):
		# Check if the polyine is open with large final gap
		p = self.points
		tol = Config.tolerance
		n = len(p)-1
		self.ignore = False
		if (abs(p[0][0]-p[n][0])>tol or abs(p[0][1]-p[n][1])>tol):
			self.ignore = True
			return

		self.frame = ReferenceFrame(self)
		self.contained_in: Optional["Element"] = None
		self.bounding_box
		self.area

		self.user_zone: Optional["Element"] = None
		self.zone: Optional["Zone"] = None

	@cached_property
	def area(self):
		_area = 0
		p = self.points
		for i in range(0, len(p)-1):
			_area += (p[i+1][0]-p[i][0])*(p[i+1][1] + p[i][1])/2

		if _area < 0:
			self.clockwise = True

		return abs(_area/10000)

	def area_m2(self):
		scale = self.frame.scale
		return self.area*scale*scale

	@cached_property
	def _centre(self):
		(cx, cy) = (0, 0)
		p = self.points
		n = len(p)-1
		for i in range(0,n):
			p = self.points[i]
			(cx, cy) = (cx+p[0], cy+p[1])

		return (cx/n, cy/n)		


	@cached_property
	def perimeter(self):
		p = self.points
		d = 0
		for i in range(0, len(p)-1):
			d += sqrt(pow(p[i+1][0]-p[i][0],2)+pow(p[i+1][1]-p[i][1],2))
		return d


	@cached_property
	def pos(self):
		
		p = self.points
		(xb, yb) = (0, 0)
		Ax = Ay = 0
		for i in range(len(p)-1):
			(x0, y0) = p[i]
			(x1, y1) = p[i+1]
			xb += (y1-y0)*(x0*x0+x0*x1+x1*x1)/6
			yb += (x1-x0)*(y0*y0+y0*y1+y1*y1)/6
			Ax += (y1-y0)*(x0+x1)/2
			Ay += (x1-x0)*(y0+y1)/2
		
		if (Ax!=0 and Ay!=0):
			return (xb/Ax, yb/Ay)
		else:
			return (0, 0)


	@cached_property
	def bounding_box(self):

		# Projections of coordinates on x and y
		self.xcoord = sorted(set([p[0] for p in self.points]))	
		self.ycoord = sorted(set([p[1] for p in self.points]))	

		self.ax = min(self.xcoord)
		self.bx = max(self.xcoord)
		self.ay = min(self.ycoord)
		self.by = max(self.ycoord)


	def is_point_inside(self, point:tuple[float, float]):

		p = self.points
		x, y = point
		ints = 0

		for i in range(0, len(p)-1):
	
			if (p[i][0]==x and p[i+1][0]==x):
				if (max(p[i][1], p[i+1][1]) >= y
				  and min(p[i][1], p[i+1][1]) <=y):
					return True

			if (p[i][0] == p[i+1][0]):
				continue	

			if (p[i][0] < p[i+1][0]):
				x0, y0 = p[i][0], p[i][1]
				x1, y1 = p[i+1][0], p[i+1][1]
			else:
				x0, y0 = p[i+1][0], p[i+1][1]
				x1, y1 = p[i][0], p[i][1]

			
			if (x0<=x and x<x1):
				if (y0==y1 and y0==y):
					return True

				delta = x1 - x0
				py = (y0*(x1-x) - y1*(x0-x))/delta
				if (py>=y):
					ints += 1

		return (ints % 2 == 1)


	def embeds(self, elem: "Element"):
		for point in elem.points:
			if (not self.is_point_inside(point)):
				return False

		return True


	def contains(self, elem: "Element"):
		for point in elem.points:
			if (self.is_point_inside(point)):
				return True

		return False


	def collides_with(self, elem: "Element"):

		# check if BBs overlap
		if (self.ax > elem.bx or
			self.bx < elem.ax or
			self.ay > elem.by or
			self.by < elem.ay):
			return False

		# check if room contains self or is contained
		if (elem.contains(self) or self.contains(elem)):
			return True

		# check if polylines cross each other
		p = self.points
		q = elem.points
		for i in range(0, len(p)-1):
			line1 = (Vec2(p[i]), Vec2(p[i+1]))
			for j in range(0, len(q)-1):
				line2 = (Vec2(q[j]), Vec2(q[j+1]))
				if (intersection_line_line_2d(line1, line2, virtual=False)):
					return True

		return False


	def local_points(self) -> poly_t:
		"""Returns the points of the element in local coordinates."""
		p = self.points
		if (self.frame is None):
			return p

		return self.frame.local_coord(self.points)
