from math import ceil
from typing import Dict, List
from ezdxf.entities import lwpolyline
from ezdxf.entities.insert import Insert
from ezdxf.entities.mtext import MText
from collector import Collector
from engine.panels import panel_map
from engine.planner import EngineConfig, Planner

from ezdxf.document import Drawing
from ezdxf.entities.insert import Insert
from leo_object import LeoObject
from model import Model
from settings import Config, panel_sizes
from geometry import dist
import settings
from model import Room


def point_in_box(pos: tuple, box: tuple) -> bool:
	x, y = pos
	x0, y0, x1, y1 = box
	return x0 <= x <= x1 and y0 <= y <= y1


def get_nonzero(register: list[int]) -> int:
	for i in range(4,-1,-1):
		if register[i] > 0:
			return i 
	return -1


class DxfDorsal():
	"""This class is used to identify the panels on the DXF drawing
	which belong to the same dorsal. """

	def __init__(self, pos: float, panel: Insert):
		self.pos = pos
		self.panels = [panel]

	def add_panel(self, panel: Insert):
		self.panels.append(panel)

def get_attrib(insert: Insert, tag: str) -> str:
	"""Get the value of an attribute by its tag from an INSERT entity."""
	for attrib in insert.attribs:
		if attrib.dxf.tag == tag:
			return attrib.dxf.text
	return ""


class Components(LeoObject):
	
	def __init__(self, model: Model):
		LeoObject.__init__(self)
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
		self.dxfdorsals: List[DxfDorsal] = []

		for panel in panel_map:
			self.panel_record[panel+"_classic"] = 0
			self.panel_record[panel+"_hydro"] = 0
		self.model = model
		self.data = model.data


	def config_planner(self, room: Room, config: EngineConfig):

		config.lux_width = Config.lux_hole_width
		config.lux_height = Config.lux_hole_height

		if "full" in self.data:
			config.enable_fulls = 0
			
		if "lux" in self.data:
			config.enable_lux = 0

		if "split" in self.data:
			config.enable_splits = 0

		if "half" in self.data:
			config.enable_halves = 0

		if "quarter" in self.data:
			config.enable_quarters = 0

		if room.vector:
			config.one_direction = 1


	def get_panels(self):

		for room in self.model.processed:

			if room.color == Config.color_disabled_room:
				continue

			room_outline = room.frame.room_outline()

			engine_config = EngineConfig()
			self.config_planner(room, engine_config)


			planner = Planner(room_outline, engine_config)
			room.panels = planner.get_panels()

			self.panels += room.panels
			self.num_panels += len(room.panels)


	def get_lines(self):
		for room in self.model.processed:
			ptype = self.model.data["ptype"]
			room.lines_manager.get_dorsals(room.panels, ptype)
			room.lines_manager.get_lines(ptype)


	def redistribute_lines(self):
		flow_m2 = self.model.flow_per_m2

		for collector in self.model.collectors:

			if collector != collector.backup[0]:
				continue

			backup = collector.backup
			num_clt = len(backup)
			cap = Config.flow_per_collector * num_clt
			
			# select room in collector group
			room_group = []
			for room in self.model.processed:
				if room.collector == collector:
					room_group.append(room)
					if room.prefer_collector == None:
						room.prefer_collector = collector

			# calculate required flow
			required_flow = 0.
			for room in room_group:
				room.flow = room.lines_manager.area_m2() * flow_m2
				required_flow += room.flow

			# assign the same flow to all collectors in the group
			for clt in backup:
				clt.freeflow = Config.feeds_per_collector

			if required_flow > cap:
				# distribute excess to all collectors
				excess = (required_flow - cap) / num_clt
				for clt in backup:
					clt.overflow = True
					clt.freeflow += excess

			room_group.sort(key=lambda x: x.flow, reverse=True)
			for room in room_group:
			
				for line in room.lines_manager.lines:
					line_flow = line.area_m2 * flow_m2
					k = backup.index(room.prefer_collector)
					i = k - num_clt 
					while i < k:
						if backup[i].freeflow > 0:
							backup[i].freeflow -= line_flow
							line.collector = backup[i]
							break
						i += 1
					# if no collector is available, assign to the last one
					if i == k:
						backup[k].freeflow -= line_flow
						line.collector = backup[k]



	def get_components(self):
		self.get_panels()

		if "enable_target" in self.data.keys():
			self.drop_excess_panels()

		self.get_lines()
		self.redistribute_lines()


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
				if type(insert) == Insert:
					room.panel_dxf.append(insert)
				handler = blocks[name]
				room.panel_record[handler] += 1
				room.active_m2 += panel_sizes[handler]
				room.ratio = room.active_m2/room.area_m2()
				room.flow = self.model.flow_per_m2 * room.active_m2
				self.panel_record[handler] += 1
				
				collector = get_attrib(insert, "collector")
				locale = self.model.get_locale(room, collector)
				locale.flow_per_m2 = self.model.flow_per_m2
				locale.add_panel(handler)

				if room.collector:
					locale.zone = room.collector.zone_num 
				
				break
		
		# assign names to locales
		self.model.locales.sort(key=lambda x: x.pindex)

		loc = self.model.locales
		for pindex in range(1,loc[-1].pindex+1):
			list_locales = []
			for locale in loc:
				if locale.pindex == pindex:
					list_locales.append(locale)

			if len(list_locales) == 0:
				continue

			if len(list_locales) == 1:
				locale = list_locales[0]
				locale.name = str(locale.room.pindex)
				continue

			for i, locale in enumerate(list_locales):
				locale.name = str(locale.room.pindex) + "." + chr(65+i)


		for room in self.model.processed:
			self.model.active_area += room.active_m2

	def zone_flow(self):
		
		for zone in self.model.zones:
			for room in zone.zone_rooms:
				zone.flow += room.flow


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

		margin = (Config.leeway+1)/self.model.scale
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

		for poly in polylines:

			if (not (isinstance(poly, lwpolyline.LWPolyline) and
					poly.dxf.color == Config.color_supply_red)):
				continue
			points = list(poly.vertices())

			endpoint1 = endpoint2 = None
			for room in self.model.processed:
				if room.is_point_inside(points[0]):
					endpoint1 = room
					break

			for collector in self.model.collectors:
				if collector.is_point_inside(points[-1]):
					endpoint2 = collector
					break

			if type(endpoint1) == Room and type(endpoint2) == Collector:
				endpoint1.collectors.add(endpoint2)
				endpoint1.total_lines += 1


	def muliple_collector_rooms(self):

		self.model.scale

		for room in self.model.processed:
			if len(room.collectors) <= 1:
				continue

			if len(room.panel_dxf) == 0:
				continue

			frame = room.frame
			for panel in room.panel_dxf:
				pos = panel.dxf.insert
				pos = (pos[0], pos[1])
				pos = frame.local_from_real(pos)

				for dorsal in self.dxfdorsals:
					if abs(dorsal.pos - pos[1]) < 0.1:
						dorsal.add_panel(panel)
						break
				else:
					self.dxfdorsals.append(DxfDorsal(pos[1], panel))


	def count_locale_lines(self, doc: Drawing):
		msp = doc.modelspace()
		fittings = msp.query(f'INSERT[layer=="{Config.layer_fittings}"]')
		for fitting in fittings:

			name = fitting.dxf.name
			leo_icons = settings.leo_icons
			if not (name == leo_icons["cap"]["name"] or
							name == leo_icons["tlink"]["name"]):
				continue

			x, y, _ = fitting.dxf.insert
			pos = x, y
			collector = get_attrib(fitting, "collector")

			for room in self.model.processed:
				if room.is_point_inside(pos):
					locale = self.model.get_locale(room, collector)

					if name == leo_icons["cap"]["name"]:
						locale.lines += 1
					else:
						locale.lines -= 1

		for locale in self.model.locales:
			locale.lines //= 2  # each line is counted twice


	def count_components(self, doc:Drawing):
		self.count_panels(doc)
		self.zone_flow()
		self.count_fittings(doc)
		self.size_collectors(doc)
		self.count_probes(doc)
		self.count_lines_from_room(doc)
		self.count_locale_lines(doc)


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


	def drop_panel_from_room(self, room: Room, ptype: int):

		for panel in room.panels:
			if panel.type == ptype:
				if panel.type in [1,2,4]:
					room.panels.remove(panel)
				else:
					panel.halve_panel()
				break

		self.num_panels -= 1


	def drop_excess_panels(self):

		q = [4, 4, 2, 2, 1]
		rooms = self.model.processed
		target = float(self.data["target"])/100.0
		target_in_quarters = ceil(target*self.model.area/0.6)

		# Build a register for room panels
		alloc_quarters = 0
		for room in rooms:
			pr = room.panel_register = [0, 0, 0, 0, 0]
			for panel in room.panels:
				pr[panel.type] += 1

			room.quarters = 0
			for i in range(5):
				room.quarters += pr[i]*q[i]

			alloc_quarters += room.quarters

		excess_quarters = alloc_quarters - target_in_quarters

		if excess_quarters <= 0:
			return

		for room in rooms:
			i = get_nonzero(room.panel_register)
			if i == -1:
				continue
			if i in [1,2,4]:
				room.ratio = 0.6*(room.quarters-q[i]) / room.area_m2()
			else:
				room.ratio = 0.6*(room.quarters-q[i]/2) / room.area_m2()

		while excess_quarters > 0:
			rooms.sort(key=lambda x: x.ratio, reverse=True)
			sel = rooms[0]
			pr = sel.panel_register
			i = get_nonzero(pr)
			if i == -1:
				break
			self.drop_panel_from_room(sel, i)

			# update room register
			if i in [1,2,4]:
				pr[i] -= 1
				sel.quarters -= q[i]
				excess_quarters -= q[i]
			else:
				if i == 0:
					pr[0] -= 1
					pr[2] += 1
					sel.quarters -= 2
					excess_quarters -= 2
				elif i == 3:
					pr[3] -= 1
					pr[4] += 1
					sel.quarters -= 1
					excess_quarters -= 1
			
			# update room ratio
			j = get_nonzero(sel.panel_register)
			if j in [1,2,4]:
				sel.ratio = 0.6*(sel.quarters-q[j]) / sel.area_m2()
			else:
				sel.ratio = 0.6*(sel.quarters-q[j]/2) / sel.area_m2()

