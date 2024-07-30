from engine.planner import RoomPlanner
from ezdxf.document import Drawing
from model import Model
from settings import Config


class ComponentManager:
	
	def __init__(self):
		self.num_panels = 0
		self.panels = list()
		self.panel_record = dict()
		self.panel_type = dict()

	def get_components(self, model):

		self.num_panels = 0
		for room in model.processed:

			room_outline = room.frame.room_outline()

			planner = RoomPlanner(room_outline)
			room.panels = planner.get_panels()
			self.panels += room.panels
			self.num_panels += len(room.panels)


	def count_panels(self, model: Model, doc: Drawing):
		msp = doc.modelspace() 
		
		self.inserts = msp.query(f'INSERT[layer=="%s"]'
				% Config.layer_panel)

		blocks = Config.available_panels()
		block_names = list(blocks.keys())

		for insert in self.inserts:
			name = insert.dxf.get("name")
			if name in block_names:
				if name in self.panel_record:
					self.panel_record[name] += 1
				else:
					self.panel_record[name] = 1

				block_pos = insert.dxf.get("insert")
				block_pos = (block_pos[0], block_pos[1])

				for room in model.processed:
					if room.is_point_inside(block_pos):
						room.panel_record[blocks[name]] += 1


	def count_components(self, model:Model, doc:Drawing):
		self.count_panels(model, doc)
