from ctypes import Structure, POINTER, c_double, c_int
from math import cos, pi, sin

from ezdxf.entities.insert import Insert

from settings import Config


panel_map = {

	"full": {
		"width_cm":  200,
		"height_cm": 120,
		"area_m2":   2.4,
		"tracks":    5,
		"in_quarters": 4
	}, 

	"lux": {
		"width_cm":  200,
		"height_cm": 120,
		"area_m2":   2.4,
		"tracks":    5,
		"in_quarters": 4
	}, 

	"split": { 
		"width_cm": 200,
		"height_cm": 60,
		"area_m2":  1.2,
		"tracks":    5,
		"in_quarters": 2
	},

	"half": {
		"width_cm":  100,
		"height_cm": 120,
		"area_m2":   1.2,
		"tracks":    3,
		"in_quarters": 2
	}, 

	"quarter": {
		"width_cm":  100,
		"height_cm":  60,
		"area_m2":   0.6,
		"tracks":    3,
		"in_quarters": 1
	}, 
}

panel_names = list(panel_map.keys())


class EnginePanel(Structure):
	pass

EnginePanel._fields_ = [
	("type", c_int),
	("x", c_double),
	("y", c_double),
	("iso_flgs", c_int),
	("dorsal_row", c_int),
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



class Panel:

	corner = 10	
	rotate = [ [1,0,0,1], [0,-1,1,0], [-1,0,0,-1], [0,1,-1,0] ]

	def __init__(self, panel: EnginePanel):
		self.pos = (panel.contents.x, panel.contents.y)
		self.rot = panel.contents.iso_flgs
		self.dorsal_row = panel.contents.dorsal_row
		self.type = panel.contents.type
		self.name = name = panel_names[self.type]
		self.width = panel_map[name]["width_cm"]
		self.height = panel_map[name]["height_cm"]
		self.area_m2 = panel_map[name]["area_m2"]

		if self.rot == 0 or self.rot == 3:
			self.rear_corner = self.pos
			self.rear_side = self.panel_to_local((0,-self.height))
			self.front_corner = self.panel_to_local((-self.width, 0))
			self.front_side = self.panel_to_local((-self.width, -self.height))
		else:
			self.rear_corner = self.panel_to_local((-self.width, 0))
			self.rear_side = self.panel_to_local((-self.width, -self.height))
			self.front_corner = self.pos
			self.front_side = self.panel_to_local((0, -self.height))


	def panel_to_local(self, point):

		x0, y0 = self.pos[0], self.pos[1]
		rot = Panel.rotate[self.rot]
		x, y = point
		xn = x*rot[0] + y*rot[1] + x0
		yn = x*rot[2] + y*rot[3] + y0
		return (xn, yn)


	@classmethod 
	def versor(cls, insert: Insert):
		attribs = insert.dxfattribs()
		angle = attribs['rotation']
		return cos(pi*angle/180), sin(pi*angle/180)


	def polyline(self) -> list[tuple[float,float]]:
	
		b = self.width 
		h = self.height 
		c = Panel.corner

		contour = [
			(-b, -h),
			(-b, -c),
			(-b+c, -c),
			(-b+c, 0),
			(-c, 0),
			(-c, -c),
			(0, -c),
			(0, -h),
			(-b, -h)
		]

		poly = list()

		for point in contour:
			poly.append(self.panel_to_local(point))

		return poly


	def contour(self) -> list[tuple[float,float]]:

		b = self.width 
		h = self.height 
		edges = [(-b, -h), (-b, 0.), (0., 0.), 	(0, -h), (-b, -h)]

		poly = list()
		for point in edges:
			poly.append(self.panel_to_local(point))

		return poly


	def lux_poly(self) -> list[tuple[float,float]]:

		if not (self.name=="full" or self.name=="lux"):
			return []

		pline = []

		lux_width = Config.lux_hole_width
		lux_height = Config.lux_hole_height

		ax = (self.width - lux_width)/2 
		bx = ax + lux_width
		ay = (self.height - lux_height)/2
		by = ay + lux_height
		pline = [(-ax,-ay),(-ax,-by),(-bx,-by),(-bx,-ay),(-ax,-ay)]

		poly = list()
		for point in pline:
			poly.append(self.panel_to_local(point))

		return poly

	def draw_panel(self, msp, frame):
		poly = self.polyline()
		poly = frame.real_coord(poly)
		pline = msp.add_lwpolyline(poly)
		pline.dxf.layer = Config.layer_panel


