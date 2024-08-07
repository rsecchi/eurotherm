# from model import Room
from ctypes import Structure, POINTER, c_double, c_int, CDLL
from settings import Config

#from ezdxf.filemanagement import new


class EnginePanel(Structure):
	pass

EnginePanel._fields_ = [
	("type", c_int),
	("x", c_double),
	("y", c_double),
	("iso_flgs", c_int),
	("dorsal_id", c_int),
	("next", POINTER(EnginePanel))
]


##### Planner Room is an Interface for engine #####
class EnginePoint(Structure):
	_fields_ = [
		("x", c_double),
		("y", c_double),
	]


class EnginePolygon(Structure):
	_fields_ = [
		("poly", POINTER(EnginePoint)),
		("len", c_int),
	]

	def __init__(self, points):

		self.len = len(points)
		self.poly = (self.len*EnginePoint)()

		for i, point in enumerate(points):
			self.poly[i].x = point[0]
			self.poly[i].y = point[1]


class EngineRoom(Structure):
	_fields_ = [
		("walls", EnginePolygon),
		("obstacles", POINTER(EnginePolygon)),
		("obs_num", c_int),
		("collector_pos", EnginePoint)
	]



class Dorsal:
	pass


class Panel:

	corner = 10	
	size = [(200,120), (200,120), (200,60), (100,120), (100,60)]
	rotate = [ [1,0,0,1], [0,-1,1,0], [-1,0,0,-1], [0,1,-1,0] ]

	def __init__(self, panel: EnginePanel):
		self.pos = (panel.contents.x, panel.contents.y)
		self.rot = panel.contents.iso_flgs
		self.dorsal_id = panel.contents.dorsal_id
		self.type = panel.contents.type


	def polyline(self):
		poly = self.poly = list()
		t = self.type
		x0, y0 = self.pos[0], self.pos[1]
		b = Panel.size[t][0]
		h = Panel.size[t][1]
		c = Panel.corner

		poly.append((-b, -h))
		poly.append((-b, -c))
		poly.append((-b+c, -c))
		poly.append((-b+c, 0))
		poly.append((-c, 0))
		poly.append((-c, -c))
		poly.append((0, -c))
		poly.append((0, -h))
		poly.append((-b, -h))

		rot = Panel.rotate[self.rot]
		for i, _ in enumerate(self.poly):
			x, y = poly[i]
			xn = x*rot[0] + y*rot[1]
			yn = x*rot[2] + y*rot[3]
			poly[i] = (xn, yn)

		for i, _ in enumerate(self.poly):
			poly[i] = (x0+poly[i][0], y0+poly[i][1])

	def draw_panel(self, msp, frame):
		self.polyline()
		poly = frame.real_coord(self.poly)
		pline = msp.add_lwpolyline(poly)
		pline.dxf.layer = Config.layer_panel

