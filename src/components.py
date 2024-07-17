from engine.planner import RoomPlanner


class ComponentManager:
	
	def __init__(self):
		self.num_panels = 0
		self.panels = list()


	def get_components(self, model):

		self.num_panels = 0
		for room in model.processed:

			room_outline = room.frame.room_outline()

			planner = RoomPlanner(room_outline)
			room.panels = planner.get_panels()
			self.panels += room.panels
			self.num_panels += len(room.panels)
