import os
from ctypes import POINTER, CDLL, Structure, pointer

from panels import EngineRoom, EnginePolygon, EnginePoint, EnginePanel
from panels import Panel
from ctypes import pointer, c_int


# Load the shared library
current_file = os.path.abspath(__file__) 
current_path = os.path.dirname(current_file)
libname = current_path + '/libplanner.so'


# Enginee configuration interface
class EngineConfig(Structure):
	_fields_ = [
		("enable_fulls", c_int),
		("enable_lux", c_int),
		("enable_splits", c_int),
		("enable_halves", c_int),
		("enable_quarters", c_int),
		("debug", c_int),
		("max_row_debug", c_int),
		("debug_animation", c_int),
		("one_direction", c_int),
		("lux_width", c_int),
		("lux_height", c_int)
	]

	def __init__(self):
		self.enable_fulls = 1
		self.enable_lux = 1
		self.enable_splits = 1
		self.enable_halves = 1
		self.enable_quarters = 1
		self.debug = 0
		self.max_row_debug = 10000
		self.debug_animation = 0
		self.one_direction = 0
		self.lux_width = 147
		self.lux_height = 24


mylib = CDLL(libname)

# Define the functions
null_config = POINTER(EngineConfig)()
mylib.planner.argtypes = [POINTER(EngineRoom), POINTER(EngineConfig)]
mylib.planner.restype = POINTER(EnginePanel) 

mylib.free_list.argtypes = [POINTER(EnginePanel)]
mylib.free_list.restype = None


class Planner:
	def __init__(self, room_outline, engine_config: EngineConfig):

		self.panels: list[Panel] = []
		self.room = EngineRoom()
		self.config = engine_config

		room = self.room 
		room.walls = EnginePolygon(room_outline.points)

		room.obs_num = len(room_outline.obstacles)
		room.obstacles = (room.obs_num*EnginePolygon)()

		for j, obs in enumerate(room_outline.obstacles):
			room.obstacles[j] = EnginePolygon(obs.points)


	def get_panels(self):

		_panels = mylib.planner(pointer(self.room), pointer(self.config))

		current = _panels 
		while current:
			self.panels.append(Panel(current))
			current = current.contents.next
		mylib.free_list(_panels)

		return self.panels 


######### TESTING #########################

def RectangularRoom(base, height):
	
	room = EngineRoom()
	walls = EnginePolygon(room.points)
	walls.poly = (5*EnginePoint)()
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
	

