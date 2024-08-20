from engine.panels import panel_map
from engine.planner import Planner

from ezdxf.document import Drawing
from model import Model
from settings import Config, panel_sizes


class Components:
	
	def __init__(self, model: Model):
		self.num_panels = 0
		self.panels = list()
		self.block_stats = dict()
		self.panel_type = dict()
		self.panel_record = dict()

		for panel in panel_map:
			self.panel_record[panel+"_classic"] = 0
			self.panel_record[panel+"_hydro"] = 0
		self.model = model


	def get_panels(self):

		for room in self.model.processed:

			room_outline = room.frame.room_outline()

			planner = Planner(room_outline)
			room.panels = planner.get_panels()

			self.panels += room.panels
			self.num_panels += len(room.panels)


	def get_lines(self):
		for room in self.model.processed:

			room.lines.get_dorsals(room.panels)
			room.lines.get_lines()


	def get_components(self):
		self.get_panels()
		self.get_lines()


	def count_panels(self, doc: Drawing):
		msp = doc.modelspace() 
		
		self.inserts = msp.query(f'INSERT[layer=="%s"]'
				% Config.layer_panel)

		blocks = Config.panel_handlers()
		block_names = list(blocks.keys())

		for insert in self.inserts:
			name = insert.dxf.get("name")
			if not name in block_names:
				continue

			# update block statistics
			if name in self.panel_record:
				self.block_stats[name] += 1
			else:
				self.block_stats[name] = 1

			block_pos = insert.dxf.get("insert")
			block_pos = (block_pos[0], block_pos[1])

			# update room record
			for room in self.model.processed:
				if not room.is_point_inside(block_pos):
					continue

				handler = blocks[name]
				room.panel_record[handler] += 1
				room.active_m2 += panel_sizes[handler]
				room.ratio = room.active_m2/room.area_m2()
				self.panel_record[handler] += 1
				break

		for room in self.model.processed:
			self.model.active_area += room.active_m2


	def count_components(self, doc:Drawing):
		self.count_panels(doc)
