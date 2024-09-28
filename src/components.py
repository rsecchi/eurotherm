from ezdxf.entities import lwpolyline
from ezdxf.entities.mtext import MText
from engine.panels import panel_map
from engine.planner import Planner

from ezdxf.document import Drawing
from model import Model
from settings import Config, panel_sizes
from geometry import dist
import settings

class Components:
	
	def __init__(self, model: Model):
		self.num_panels = 0
		self.panels = list()
		self.panel_counters = dict()
		self.panel_type = dict()
		self.panel_record = dict()
		self.fittings = dict()
		self.room_icons = dict()

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

			room.lines_manager.get_dorsals(room.panels)
			room.lines_manager.get_lines()


	def get_components(self):
		self.get_panels()
		self.get_lines()


	def count_panels(self, doc: Drawing):
		msp = doc.modelspace() 
		
		inserts = msp.query(f'INSERT[layer=="%s"]'
				% Config.layer_panel)

		blocks = Config.panel_handlers()
		block_names = list(blocks.keys())

		for insert in inserts:
			name = insert.dxf.get("name")
			if not name in block_names:
				continue

			# update block statistics
			if name in self.panel_counters.keys():
				self.panel_counters[name] += 1
			else:
				self.panel_counters[name] = 1

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


	def count_fittings(self, doc: Drawing):

		msp = doc.modelspace() 		
		fittings = msp.query(f'INSERT[layer=="%s"]' 
				% Config.layer_fittings)

		for fitting in fittings:
			name = fitting.dxf.name
			blocks = (x["name"] for x in settings.leo_icons.values())
			if not name in blocks:
				continue

			x, y, _ = fitting.dxf.insert
			pos = x, y

			if not name in self.fittings.keys():
				self.fittings[name] = 0

			self.fittings[name] += 1
			for room in self.model.processed:
				if not room.is_point_inside(pos):
					continue

				index = str(room.pindex)
				if not index in self.room_icons:
					self.room_icons[index] = dict()

				if not name in self.room_icons[index].keys():
					self.room_icons[index][name] = 0

				self.room_icons[index][name] += 1


	def size_collectors(self, doc:Drawing):

		msp = doc.modelspace() 		
		coll_tags = msp.query(f'MTEXT[layer=="%s"]'
				% Config.layer_collector)

		polylines = msp.query(f'LWPOLYLINE[layer=="{Config.layer_link}"]')

		margin = Config.leeway/self.model.scale + 1
		for tags in coll_tags:
			assert isinstance(tags, MText)
			x, y, _ = tags.dxf.insert
			pos = x,y

			count = 0
			for poly in polylines:
				assert isinstance(poly, lwpolyline.LWPolyline) 
				head = dist(poly[0], pos)
				tail = dist(poly[-1], pos)
				if head<margin or tail<margin:
					count += 1

			tags.text += " (%d+%d)" % (count//2, count//2)


	def count_components(self, doc:Drawing):
		self.count_panels(doc)
		self.count_fittings(doc)
		self.size_collectors(doc)




