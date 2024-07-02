import os
from ctypes import Structure, POINTER, c_double, c_int, CDLL, pointer

#from ezdxf.filemanagement import new

class Pnl(Structure):
	pass

Pnl._fields_ = [
	("type", c_int),
	("x", c_double),
	("y", c_double),
	("iso_flgs", c_int),
	("next", POINTER(Pnl))
]


##### Room definition #####
class Point(Structure):
	_fields_ = [
		("x", c_double),
		("y", c_double),
	]


class Polygon(Structure):
	_fields_ = [
		("poly", POINTER(Point)),
		("len", c_int),
	]


class Room(Structure):
	_fields_ = [
		("walls", Polygon),
		("obstacles", POINTER(Polygon)),
		("obs_num", c_int),
		("collector_pos", Point)
	]


# Load the shared library
current_file = os.path.abspath(__file__) 
current_path = os.path.dirname(current_file)
libname = current_path + '/libplanner.so'

mylib = CDLL(libname)

# Define the functions
mylib.planner.argtypes = [POINTER(Room)]
mylib.planner.restype = POINTER(Pnl) 

mylib.free_list.argtypes = [POINTER(Pnl)]
mylib.free_list.restype = None


class Panel:

	corner = 10	
	size = [(200,120), (200,120), (200,60), (100,120), (100,60)]
	rotate = [ [1,0,0,1], [0,-1,1,0], [-1,0,0,-1], [0,1,-1,0] ]

	def __init__(self, panel: Pnl):
		self.pos = (panel.contents.x, panel.contents.y)
		self.rot = panel.contents.iso_flgs
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

	def draw_panel(self, msp, scale):
		self.polyline()
		poly = list()
		for i, _ in enumerate(self.poly):
			poly.append((self.poly[i][0]/scale, self.poly[i][1]/scale))
		msp.add_lwpolyline(poly)
		

class Planner:
	def __init__(self, contour):

		room = self.room = Room()
		walls = Polygon()
		walls.poly = (len(contour)*Point)()

		i = 0
		for point in contour:
			walls.poly[i].x = point[0]
			walls.poly[i].y = point[1]
			i += 1

		walls.len = len(contour)
		room.walls = walls

		room.obs_num = 0
		room.obstacles = None

	def get_panels(self):

		self.panels = list()
		_panels = mylib.planner(pointer(self.room))

		current = _panels 
		while current:
			self.panels.append(Panel(current))
			current = current.contents.next
		mylib.free_list(_panels)

		return self.panels 

######### TESTING #########################

def RectangularRoom(base, height):
	
	room = Room()
	walls = Polygon()
	walls.poly = (5*Point)()
	walls.poly[0].x = 0; walls.poly[0].y = 0;
	walls.poly[1].x = 0; walls.poly[1].y = height;
	walls.poly[2].x = base; walls.poly[2].y = height;
	walls.poly[3].x = base; walls.poly[3].y = 0;
	walls.poly[4].x = 0; walls.poly[3].y = 0;
	walls.len = 5

	room.walls = walls
	room.obs_num = 0
	room.obstacles = None

	return room


def print_list(panels):
	current = panels 
	while current:
		pos = (current.contents.x, current.contents.y)
		print(pos)
	
		current = current.contents.next	
	

######### PLANNER INTERFACE TEST #############################
# from ezdxf.filemanagement import new

# room = RectangularRoom(400, 600)

# print_list(panels)

# b = 400
# h = 600


# contour = [(25.85691014875588, -426.3320670724359), (21.43940990902879, -426.3320670724359), (21.43940990902879, -429.8970711923089), (24.60191047038842, -429.8970711923089), (24.60191047038842, -429.337085163202), (25.85691014875588, -429.337085163202), (25.85691014875588, -426.3320670724359)]

# for i, p in enumerate(contour):
# 	contour[i] = (contour[i][0]*100, contour[i][1]*100)

# # contour = [(0,0), (b,0), (b,h), (0,h), (0,0)]
# planner = Planner(contour)

# panels = planner.get_panels()


# # Create a new DXF document
# doc = new(dxfversion='R2010')
# modelspace = doc.modelspace()

# modelspace.add_lwpolyline(contour)
# for panel in panels:
# 	panel.draw_panel(modelspace)


# # Save the DXF document to a file
# doc.saveas("example.dxf")

# print("DXF file created successfully.")


