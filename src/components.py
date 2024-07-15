import os, sys
local_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(local_dir)
sys.path.append('..')

from engine.planner import RoomPlanner


class ComponentManager:
	
	def __init__(self):
		self.num_panels = 0
		self.panels = list()

	def get_components(self, model):

		self.num_panels = 0
		for room in model.processed:
			planner = RoomPlanner(room, model.scale)
			room.panels = planner.get_panels()
			self.panels += room.panels
			self.num_panels += len(room.panels)
