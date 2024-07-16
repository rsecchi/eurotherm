from ezdxf.math import convex_hull_2d
from math import pi, atan2, sqrt

MAX_DIST  = 1e20
MAX_DIST2 = 1e20

def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)

class ReferenceFrame:
	def __init__(self, room):
		self.room = room
		self.points = room.points
		self.vector = None
		self.rot_orig = None
		self.rot_angle = None

	def get_local(self):
		pass

	def orient_room(self):

		uv = (uvx, uvy) = (1, 0)
		self.vector = uv
		max_rot_orig = 0
		vtx = [(p[0],p[1],0) for p in self.points]
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
				max_rot_orig = p0

		angle = min(abs(uvx),abs(uvy))/max(abs(uvx),abs(uvy))
		if (angle > 0.01):
			self.vector = uv
			self.rot_orig = max_rot_orig
			self.rot_angle = -atan2(max_uv[1], -max_uv[0])*180/pi


