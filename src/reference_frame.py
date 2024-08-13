from ezdxf.math import convex_hull_2d
from math import pi, atan2, sqrt

MAX_DIST  = 1e20
MAX_DIST2 = 1e20

def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)
	

class Outline:
	def __init__(self):
		self.points = list()
		self.obstacles = list()


class ReferenceFrame:
	def __init__(self, room):
		self.room = room
		self.vector = tuple() 
		self.rot_orig = tuple()
		self.rot_angle = int()
		self.scale = 1.
		self.outline = Outline() 
		self.horizontal_flip = False
		self.vertical_flip = False


	def block_rotation(self, rot: int):
		x = self.vector[0]
		y = self.vector[1]
		rot_angle = atan2(y,x)*180/pi
		rotation = rot * 90  + rot_angle
		return rotation


	def real_from_local(self, point):
		orig = self.rot_orig
		(ux, uy) = self.vector
		(vx, vy) = (-uy, ux)
		scale = self.scale

		bx = (ux*point[0] + vx*point[1])/scale
		by = (uy*point[0] + vy*point[1])/scale

		return (bx+orig[0], by+orig[1])
	

	def local_from_real(self, point):
		orig = self.rot_orig
		(ux, uy) = self.vector
		(vx, vy) = (-uy, ux)
		scale = self.scale

		(ax, ay) = (point[0]-orig[0], point[1]-orig[1]) 
		bx = (ux*ax + uy*ay)*scale
		by = (vx*ax + vy*ay)*scale
		return (bx, by)


	def real_coord(self, points):

		rotated_points = list()
		for point in points:
			rotated_points.append(self.real_from_local(point))
	
		return rotated_points


	def local_coord(self, points):

		rotated_points = list()
		for point in points:	
			rotated_points.append(self.local_from_real(point))

		return rotated_points


	def room_outline(self):
		if not self.vector:
			return None

		room = self.room
		outline = self.outline
		obstacles = self.outline.obstacles

		outline.points = self.local_coord(room.points)
		for obs in room.obstacles:
			out_obs = Outline()
			out_obs.points = self.local_coord(obs.points)
			obstacles.append(out_obs)

		return outline


	def flip_frame(self, pos):
		deltax = self.room.pos[0] - pos[0]
		deltay = self.room.pos[1] - pos[1]
		if deltax < 0:
			self.horizontal_flip = True

		if deltay < 0:
			self.vertical_flip = True


	def orient_frame(self):

		uv = (uvx, uvy) = (1, 0)
		self.vector = uv

		self.rot_orig = ((self.room.ax+self.room.bx)/2, 
						 (self.room.ay+self.room.by)/2)

		vtx = [(p[0],p[1],0) for p in self.room.points]
		conv_hull = convex_hull_2d(vtx)
		ch = [(s.x, s.y) for s in conv_hull]
		ch = [*ch, ch[0]]

		max_area = MAX_DIST2
		max_uv = (1,0)
		for i in range(len(ch)-1):
			p0, p1 = ch[i], ch[i+1]
			norm_uv = dist(p0, p1)
			if (norm_uv == 0):
				continue
			uvx, uvy = uv = (p1[0]-p0[0])/norm_uv, (p1[1]-p0[1])/norm_uv
			bxm = bxM = 0; by = 0
			for p in ch[:-1]:
				px =  uvx*(p[0]-p0[0]) + uvy*(p[1]-p0[1])
				py = abs(-uvy*(p[0]-p0[0]) + uvx*(p[1]-p0[1]))
				if (py > by):
					by = py

				if (px < bxm):
					bxm = px
				if (px > bxM):
					bxM = px

			Ar = (bxM - bxm)*by
			if ( Ar < max_area ):
				max_area = Ar
				max_uv = uv

		angle = min(abs(uvx),abs(uvy))/max(abs(uvx),abs(uvy))
		if (angle > 0.01):
			self.vector = max_uv
			self.rot_angle = -atan2(max_uv[1], -max_uv[0])*180/pi


	def small_square(self, local_point):

		size = 10
		p = local_point

		poly = [
			(p[0] + size, p[1] + size),
			(p[0] - size, p[1] + size),
			(p[0] - size, p[1] - size),
			(p[0] + size, p[1] - size),
			(p[0] + size, p[1] + size),
		]

		return self.real_coord(poly)

