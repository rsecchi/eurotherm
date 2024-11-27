from math import ceil
from pprint import pprint
from typing import Dict, List
from ezdxf.entities import lwpolyline
from ezdxf.entities.mtext import MText
from engine.panels import panel_map
from engine.planner import Planner

from ezdxf.document import Drawing
from model import Model
from settings import Config, panel_sizes
from geometry import dist
import settings
from model import Room


def point_in_box(pos: tuple, box: tuple) -> bool:
	x, y = pos
	x0, y0, x1, y1 = box
	return x0 <= x <= x1 and y0 <= y <= y1


class Components:
	
	def __init__(self, model: Model):
		self.num_panels = 0
		self.panels = list()
		self.panel_counters = dict()
		self.panel_type = dict()
		self.panel_record = dict()
		self.fittings = dict()
		self.room_icons = dict()
		self.collectors: List[Dict[str, str|int]] = []
		self.probes = list()
		self.num_lines = 0
		self.num_probes_t = 0
		self.num_probes_th = 0
		self.smartbases = 0
		self.smartcomforts = 0
		self.air_handlers = []

		for panel in panel_map:
			self.panel_record[panel+"_classic"] = 0
			self.panel_record[panel+"_hydro"] = 0
		self.model = model
		self.data = model.data


	def get_panels(self):

		for room in self.model.processed:
			room_outline = room.frame.room_outline()

			planner = Planner(room_outline)
			room.panels = planner.get_panels()

			self.panels += room.panels
			self.num_panels += len(room.panels)


	def get_lines(self):
		for room in self.model.processed:
			ptype = self.model.data["ptype"]
			room.lines_manager.get_dorsals(room.panels, ptype)
			room.lines_manager.get_lines(ptype)


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

	def count_probes(self, doc: Drawing):

		msp = doc.modelspace() 		
		probes = msp.query(f'INSERT[layer=="{Config.layer_probes}"]')
		for probe in probes:
			x, y, _ = probe.dxf.insert
			pos = x, y
			self.probes.append(pos)

			if probe.dxf.name == settings.leo_icons["probe_T"]["name"]:
				self.num_probes_t += 1

			if probe.dxf.name == settings.leo_icons["probe_TH"]["name"]:
				self.num_probes_th += 1


		zones = msp.query(f'LWPOLYLINE[layer=="{Config.layer_text}"]')

		for zone in zones:
			if not isinstance(zone, lwpolyline.LWPolyline):
				continue

			# determine the bounding box of the zone polyline
			polyline = list(zone.vertices())
			x0, y0 = polyline[0]
			x1, y1 = polyline[2]
			bbox = (x0, y0, x1, y1)	

			probes_in_zone = 0
			for probe in self.probes:
				if point_in_box(probe, bbox):
					probes_in_zone += 1
	
			smartbases = ceil(probes_in_zone/8)
			self.smartbases += ceil(smartbases)
			self.smartcomforts += ceil(smartbases/8)


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
			self.collectors.append(
					{"name": tags.text,
					 "count": count//2})

			self.num_lines += count//2


	def count_lines_from_room(self, doc:Drawing):
	
		msp = doc.modelspace()
		polylines = msp.query(f'LWPOLYLINE[layer=="{Config.layer_link}"]')

		for room in self.model.processed:
			if not isinstance(room.collector, Room):
				continue

			count = 0
			for poly in polylines:
				if not isinstance(poly, lwpolyline.LWPolyline):
					continue
				points = list(poly.vertices())
			
				if room.is_point_inside(points[0]):
					count += 1

			room.total_lines += count//2


	def count_components(self, doc:Drawing):
		self.count_panels(doc)
		self.count_fittings(doc)
		self.size_collectors(doc)
		self.count_probes(doc)
		self.count_lines_from_room(doc)


	def air_handling(self):

		mount = 'V' if self.data["inst"] == "vert" else 'O'
		regulator = self.data["regulator"]

		for clt in self.model.collectors:
			if not clt.is_leader:
				continue
			
			# Zone handling
			zone_area = 0
			for room in clt.zone_rooms:
				zone_area += room.area_m2()
			volume = float(self.data["height"]) * zone_area

			air = []
			for ac in settings.air_handlers:
				if (regulator == ac['type'] and 
					  mount == ac['mount']):
					air.append(ac)

			l = len(air)
			air.sort(key= lambda x: x["flow_m3h"]);
			max_ac = ceil(volume/air[0]["flow_m3h"])
		
			num_ac = [0]*l
			best_ac = [0]*l
			best_flow = settings.MAX_COST
			for i in range((max_ac+1) ** l):
				flowtot = 0
				count = i
				for k in range(l):
					val = count % (max_ac+1)
					count = count//(max_ac+1)
					num_ac[k] = val
					flowtot += val * air[k]["flow_m3h"]
				if (flowtot >= volume and flowtot < best_flow):
					best_flow = flowtot
					for k, val in enumerate(num_ac):
						best_ac[k] = num_ac[k]

			item = {
				"zone": clt.zone_num,
				"air_handler": air,
				"best_ac": best_ac,
				"best_flow": best_flow,
				"coverage": volume,
			}
			self.air_handlers.append(item)


