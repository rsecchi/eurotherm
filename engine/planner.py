import os
from ctypes import POINTER, CDLL, Structure, pointer

from panels import EngineRoom, EnginePolygon, EnginePoint, EnginePanel
from panels import Panel
from ctypes import pointer, c_int

from settings import Config

# Load the shared library
current_file = os.path.abspath(__file__) 
current_path = os.path.dirname(current_file)
libname = current_path + '/libplanner.so'


# Enginee configuration interface
class EngineConfig(Structure):
	_fields_ = [
		("debug", c_int),
		("enable_fulls", c_int),
		("enable_lux", c_int),
		("enable_splits", c_int),
		("enable_halves", c_int),
		("enable_quarters", c_int),
		("max_row_debug", c_int),
		("debug_animation", c_int),
		("one_direction", c_int),
		("lux_width", c_int),
		("lux_height", c_int)
	]

engine_config = EngineConfig()
engine_config.debug = 0
engine_config.enable_fulls = 1
engine_config.enable_lux = 1
engine_config.enable_splits = 1
engine_config.enable_halves = 1
engine_config.enable_quarters = 1
engine_config.max_row_debug = 10000
engine_config.debug_animation = 0
engine_config.one_direction = 0
engine_config.lux_width = 147
engine_config.lux_height = 24


mylib = CDLL(libname)

# Define the functions
null_config = POINTER(EngineConfig)()
mylib.planner.argtypes = [POINTER(EngineRoom), POINTER(EngineConfig)]
mylib.planner.restype = POINTER(EnginePanel) 

mylib.free_list.argtypes = [POINTER(EnginePanel)]
mylib.free_list.restype = None


# Configuration functions
mylib.set_one_direction.argtypes = [c_int]
mylib.set_one_direction.restype = None

mylib.set_debug.argtypes = [c_int]
mylib.set_debug.restype = None


mylib.disable_fulls.argtypes = [] 
mylib.disable_fulls.restype = None
mylib.disable_lux.argtypes = []
mylib.disable_lux.restype = None
mylib.disable_splits.argtypes = []
mylib.disable_splits.restype = None
mylib.disable_halves.argtypes = []
mylib.disable_halves.restype = None
mylib.disable_quarters.argtypes = []
mylib.disable_quarters.restype = None
mylib.set_lux_width.argtypes = [c_int]
mylib.set_lux_width.restype = None
mylib.set_lux_height.argtypes = [c_int]
mylib.set_lux_height.restype = None

class Planner:
	def __init__(self, room_outline):

		self.panels: list[Panel] = []
		self.room = EngineRoom()

		room = self.room 
		room.walls = EnginePolygon(room_outline.points)

		room.obs_num = len(room_outline.obstacles)
		room.obstacles = (room.obs_num*EnginePolygon)()

		for j, obs in enumerate(room_outline.obstacles):
			room.obstacles[j] = EnginePolygon(obs.points)


	def get_panels(self):

		_panels = mylib.planner(pointer(self.room), pointer(engine_config))

		current = _panels 
		while current:
			self.panels.append(Panel(current))
			current = current.contents.next
		mylib.free_list(_panels)

		return self.panels 


	def set_one_direction(self, direction):
		mylib.set_one_direction(direction)

	def set_debug(self, debug):
		mylib.set_debug(debug)

	def disable_quarter(self):
		mylib.disable_quarters()

	def disable_lux(self):
		mylib.disable_lux()

	def disable_full(self):
		mylib.disable_fulls()

	def disable_half(self):
		mylib.disable_halves()

	def disable_split(self):
		mylib.disable_splits()

	def set_lux_width(self, width):
		mylib.set_lux_width(width)
	
	def set_lux_height(self, height):
		mylib.set_lux_height(height)

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
	

