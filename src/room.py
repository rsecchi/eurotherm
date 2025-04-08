from ezdxf.entities.lwpolyline import LWPolyline
from element import Element
from geometry import dist
from reference_frame import ReferenceFrame
from settings import Config
from lines import Panel, LinesManager
from typing import Optional
from engine.panels import panel_map
from ezdxf.math import Vec2, intersection_line_line_2d
from math import sqrt

MAX_DIST  = 1e20


def is_gate(line, target):
	
	(xa0,ya0), (xa1,ya1) = line
	(xb0,yb0), (xb1,yb1) = target

	# reference on target
	(ux, uy) = (xb1-xb0, yb1-yb0)
	u = sqrt(ux*ux + uy*uy)
	if (u==0):
		return (False, (None, None))
	(uvx, uvy) = (ux/u, uy/u)
	(uox, uoy) = (-uvy, uvx)
	
	# change of reference for p and q
	(px, py) = (xa0-xb0, ya0-yb0)
	(qx, qy) = (xa1-xb0, ya1-yb0)
	(npx, npy) = (uvx*px+uvy*py, uox*px+uoy*py)
	(nqx, nqy) = (uvx*qx+uvy*qy, uox*qx+uoy*qy)

	w = abs(npx - nqx)

	if ((w <= Config.min_dist) or
		(npx<=0 and nqx<=0) or (npx>=u and nqx>=u)):
		return (False, (None, None))

	if (npx<0):
		p1 = (xb0,yb0)
		l1 = 0
	else:
		if (npx>u):
			p1 = (xb1,yb1)
			l1 = u
		else:
			p1 = (xb0+uvx*npx, yb0+uvy*npx)
			l1 = npx

	if (nqx<0):
		p2 = (xb0,yb0)
		l2 = 0
	else:
		if (nqx>u):
			p2 = (xb1,yb1)
			l2 = u
		else:
			p2 = (xb0+uvx*nqx, yb0+uvy*nqx)
			l2 = nqx

	if (abs(l1-l2)<=Config.min_dist):
		return (False, (None, None))

	d1 = abs((npy*(nqx-l1) - (npx-l1)*nqy)/w)
	d2 = abs((npy*(nqx-l2) - (npx-l2)*nqy)/w)
	
	if (d1<= Config.wall_depth and d2<=Config.wall_depth):
		return (True, (p1, p2))

	return (False, (None, None))



class Room(Element):

	def __init__(self, poly:LWPolyline, output):

		Element.__init__(self, poly)
		self.pindex = 0
		self.output = output
		self.ignore = False
		self.error = False
		self.errorstr = ""
		self.contained_in = None
		self.obstacles = list()
		self.gates = list()
		self.links = list()
		self.bridges = list()
		self.joined_lines = list()
		self.total_lines = 0
		self.sup = 0
		self.inf = 0
		self.fixed_collector = None
		self.vector = False

		self.leader = None
		self.zone = None
		self.user_zone = None
		self.uplink = None
		self.walk = MAX_DIST
		self.links = list()

		self.orient = 0
		self.boxes = list()
		self.coord = list()

		if type(poly) == LWPolyline:
			self.points = list(poly.vertices())	
		else:
			self.points = poly

		self.frame = ReferenceFrame(self)

		# Add a final point to closed polylines
		p = self.points
		if (type(poly) == LWPolyline and poly.is_closed):
			self.points.append((p[0][0], p[0][1]))

		# Check if the polyine is open with large final gap
		tol = Config.tolerance
		n = len(p)-1
		if (abs(p[0][0]-p[n][0])>tol or abs(p[0][1]-p[n][1])>tol):
			self.ignore = True
			return

		# Straighten up walls
		finished = False
		while not finished:
			for i in range(1, len(p)):
				if (abs(p[i][0]-p[i-1][0]) < tol):
					p[i] = (p[i-1][0], p[i][1])

				if (abs(p[i][1]-p[i-1][1]) < tol):
					p[i] = (p[i][0], p[i-1][1])

			if (p[0] == p[n]):
				finished = True
			else:
				p[0] = p[n]


		# feeds/flow estimates
		self.feeds_eff = 0.0
		self.feeds_max = 0.0
		self.flow_eff = 0.0
		self.flow_max = 0.0
		self.feeds = 0
		self.flow = 0.0

		if type(poly) == LWPolyline:
			self.color = poly.dxf.color
		else:
			self.color = Config.color_obstacle

		# self.arrangement = PanelArrangement(self)
		self.panels: list[Panel] = list()
		self.panel_register: list[int] = []
		self.quarters = 0
		self.lines_manager = LinesManager()
		self.bounding_box()
		self.area = self._area()
		self.active_m2 = 0.0
		self.ratio = 0.0
		self.pos = self._barycentre()
		self.perimeter = self._perimeter()

		# collector related variables
		self.collector: Optional[Room] = None
		self.number = 0
		self.zone_num = 0
		self.inputs = 0 
		self.name = ""

		self.panel_record = dict()
		for panel in panel_map:
			self.panel_record[panel+"_classic"] = 0
			self.panel_record[panel+"_hydro"] = 0

	def _area(self):
		a = 0
		p = self.points
		for i in range(0, len(p)-1):
			a += (p[i+1][0]-p[i][0])*(p[i+1][1] + p[i][1])/2
		return abs(a/10000)

	def area_m2(self):
		scale = self.frame.scale
		return self.area*scale*scale

	def _centre(self):
		(cx, cy) = (0, 0)
		p = self.points
		n = len(p)-1
		for i in range(0,n):
			p = self.points[i]
			(cx, cy) = (cx+p[0], cy+p[1])

		return (cx/n, cy/n)
		

	def _perimeter(self):
		p = self.points
		d = 0
		for i in range(0, len(p)-1):
			d += sqrt(pow(p[i+1][0]-p[i][0],2)+pow(p[i+1][1]-p[i][1],2))
		return d

	def _barycentre(self):
		
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

	def bounding_box(self):

		# Projections of coordinates on x and y
		self.xcoord = sorted(set([p[0] for p in self.points]))	
		self.ycoord = sorted(set([p[1] for p in self.points]))	

		self.ax = min(self.xcoord)
		self.bx = max(self.xcoord)
		self.ay = min(self.ycoord)
		self.by = max(self.ycoord)


	def is_point_inside(self, point):

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


	def embeds(self, room):
		for point in room.points:
			if (not self.is_point_inside(point)):
				return False

		return True


	def contains(self, room):
		for point in room.points:
			if (self.is_point_inside(point)):
				return True

		return False


	def collides_with(self, room):

		# check if BBs overlap
		if (self.ax > room.bx or
			self.bx < room.ax or
			self.ay > room.by or
			self.by < room.ay):
			return False

		# check if room contains self or is contained
		if (room.contains(self) or self.contains(room)):
			return True

		# check if polylines cross each other
		p = self.points
		q = room.points
		for i in range(0, len(p)-1):
			line1 = (Vec2(p[i]), Vec2(p[i+1]))
			for j in range(0, len(q)-1):
				line2 = (Vec2(q[j]), Vec2(q[j+1]))
				if (intersection_line_line_2d(line1, line2, virtual=False)):
					return True

		return False
	

	def add_gates(self, room):
		p1 = self.points
		p2 = room.points
		for i in range(0, len(p1)-1):
			line1 = (p1[i], p1[i+1]) 
			for j in range(0, len(p2)-1):
				line2 = (p2[j], p2[j+1]) 
				cond, wall = is_gate(line2, line1)
				if (cond):
					self.gates.append((room, wall))

	def set_as_root(self, queue, collector):
		self.visited = True

		for room, _ in self.gates:
			if (not room.visited):
				if (collector.contained_in == self):
					pos = collector.pos
				else:
					pos = self.pos
				distance = dist(pos, room.pos)
				walk = self.walk + distance
				if (walk < room.walk):
					room.walk = walk
					room.uplink = self

		# select next room
		if (len(queue)>0):
			queue.sort(key=lambda x: x.walk)
			next_room = queue.pop(0)
			next_room.set_as_root(queue, collector)

	def contains_vector(self, v):
		p1 = (v.dxf.start[0], v.dxf.start[1])
		p2 = (v.dxf.end[0], v.dxf.end[1])
		if (p1 == p2):
			return False
		return self.is_point_inside(p1) and self.is_point_inside(p2)



