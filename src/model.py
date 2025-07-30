from typing import List
from ezdxf.entities.lwpolyline import LWPolyline
from ezdxf.lldxf.const import LWPOLYLINE_CLOSED
from collector import Collector
from leo_object import LeoObject
from settings import Config, dist
from math import sqrt, ceil, log10, atan2, pi
from copy import copy
from ezdxf.filemanagement import readfile

import conf
from room import Locale, Room, RoomGroup



min_room_area = 1
max_steps = 20
max_clt_break = 5
max_iterations = 5e6
extra_flow_probe = 100

MAX_DIST  = 1e20
MAX_DIST2 = 1e20

# Panel types
panel_types = [
    {
        "full_name"  : "Leonardo 5,5",
        "handler"    : "55",
        "rings"      : 10,
        "panels"     : 5,
        "flow_line"  : 280,
        "flow_ring"  : 28,
        "flow_panel" : 56,
		"code_full"  : "6113010431",
		"desc_full"  : "LEONARDO 5,5 MS - 1200x2000x50mm",
		"code_half"  : "6113010432",
		"desc_half"  : "LEONARDO 5,5 MS - 600x2000x50mm",
		"code_full_h": "6114010411",
		"desc_full_h": "LEONARDO 5,5 IDRO MS - 1200x2000x50mm",
		"code_half_h": "6114010412",
		"desc_half_h": "LEONARDO 5,5 IDRO MS - 600x2000x50mm",
    },
    {
        "full_name"  : "Leonardo 3,5",
        "handler"    : "35",
        "rings"      : 9,
        "panels"     : 4.5,
        "flow_line"  : 252,
        "flow_ring"  : 28,
        "flow_panel" : 56,
		"code_full"  : "6113010451",
		"desc_full"  : "LEONARDO 3,5 MS - 1200x2000x50mm",
		"code_half"  : "6113010452",
		"desc_half"  : "LEONARDO 3,5 MS - 600x2000x50mm",
		"code_full_h": "6114010431",
		"desc_full_h": "LEONARDO 3,5 IDRO MS - 1200x2000x50mm",
		"code_half_h": "6114010432",
		"desc_half_h": "LEONARDO 3,5 IDRO MS - 600x2000x50mm",
    },
    {
        "full_name"  : "Leonardo 3,0 plus",
        "handler"    : "30",
        "rings"      : 9,
        "panels"     : 4.5,
        "flow_line"  : 265,
        "flow_ring"  : 29.4,
        "flow_panel" : 58.9,
		"code_full"  : "6113011001",
		"desc_full"  : "LEONARDO 3,0 PLUS MS - 1200x2000x50mm",
		"code_half"  : "6113011002",
		"desc_half"  : "LEONARDO 3,0 PLUS MS - 600x2000x50mm",
		"code_full_h": "6113011001",
		"desc_full_h": "LEONARDO 3,0 PLUS MS - 1200x2000x50mm",
		"code_half_h": "6113011002",
		"desc_half_h": "LEONARDO 3,0 PLUS MS - 600x2000x50mm",
    }
]




class Model(LeoObject):

	@classmethod
	def polyline_area(cls, poly:LWPolyline):
		area = 0.
		p = list(poly.vertices())
		if poly.dxf.flags & LWPOLYLINE_CLOSED:
			p.append(p[0])
		for i in range(0, len(p)-1):
			area += (p[i+1][0]-p[i][0])*(p[i+1][1] + p[i][1])/2

		return abs(area/10000)


	def __init__(self, data):

		super(Model, self).__init__()
		self.data = data
		self.polylines = list()
		self.rooms = list()
		self.roomgroups: list[RoomGroup] = list()
		self.locales: List[Locale] = []
		self.vectors = list()
		self.collectors: list[Collector] = list()
		self.valid_rooms = list()
		self.processed: list[Room] = list()
		self.obstacles = list()
		self.zone = list()
		self.zones = list()
		self.zone_bb = list()
		self.user_zones = list()
		self.output = self
		self.text = ""
		self.best_list = list()
		self.text_nav = ""
		self.cnd = list()
		self.laid = "without"
		self.area = 0.0
		self.active_area = 0.0
		self.outfile = conf.spool + data['outfile']

		for	ctype in panel_types:
			if (ctype['handler'] == data['ptype']):
				self.type = ctype['full_name']

		self.input_file = conf.spool + data['infile']

		self.input_doc = readfile(self.input_file)
		self.msp = self.input_doc.modelspace()
		self.refit = False
		for layer in self.input_doc.layers:
			if layer.dxf.name == Config.layer_panel:
				self.refit = True


		self.scale = 1.0
		self.inputlayer = Config.input_layer
		self.filename = self.input_file
		self.control = data['control']
		self.head =  data['head']
		self.mtype = data['inst']
		self.regulator = data['regulator']
		self.height = data['height']

		if data['laid']=="with":
			self.laid = "with"
			self.cname = data['cname']
			self.caddr = data['caddr']
			self.ccomp = data['ccomp']

		if self.refit:
			ctype = self.type
			for ptype in panel_types:
				if (ctype == ptype['full_name']):
					self.ptype = ptype

		self.ents = self.msp.query('*[layer=="%s"]'
				% self.inputlayer)

		for layer in self.input_doc.layers:
			if (layer.dxf.name == self.inputlayer):
				self.layer_color = layer.dxf.color

		if (len(self.ents) == 0):
			self.print('ABORT: Layer "%s" not available or empty @'
				% self.inputlayer)

		ctype = self.type

		for ptype in panel_types:
			if (ctype == ptype['full_name']):
				self.ptype = ptype

				self.area_per_feed_m2 = ptype['panels'] * 2.4
				self.flow_per_m2 = ptype['flow_panel'] / 2.4
				print('Area/line = %g m2' % self.area_per_feed_m2)
				print('Flow_per_m2 = %g l/m2' % self.flow_per_m2)



	def find_gates(self):

		for room1 in self.processed:
			for room2 in self.processed:
				if (room1 != room2):
					room1.add_gates(room2)


	def merge_rooms(self, collector):

		# calculate distances from collector
		for room in self.processed:
			room.visited = False
			room.uplink = None
			room.walk = MAX_DIST

		root = collector.contained_in
		if (not root):
			return None

		leader = None

		# if collector contained_in room already assigned
		# the leader is the root of that zone
		if (root.zone):
			leader = root.zone

		root.walk = 0
		root.uplink = root
		root.set_as_root(self.processed.copy(), collector)

		if collector.user_zone and collector.user_zone.leader:
			leader = collector.user_zone.leader

		for room in self.processed:

			if ((room.user_zone != collector.user_zone) or
				(room.fixed_collector and
				(room.fixed_collector.user_zone != collector.user_zone))):
				room.walk = MAX_DIST

			link_item = (collector, room.walk, room.uplink)
			room.links.append(link_item)

			if not (room.walk<MAX_DIST or
				room.fixed_collector == collector):
				continue

			# A related room is NOT assigned to a zone
			if not room.zone:

				if not leader:
					leader = collector
					collector.is_leader = True
					if collector.user_zone:
						collector.user_zone.leader = collector
					self.zones.append(collector)

				room.zone = leader
				leader.zone_rooms.append(room)

			# A related room is already assigned to a zone
			else:
				if (leader and room.user_zone != leader.user_zone):
					continue

				if leader and room.zone != leader:
					leader.is_leader = False
					self.zones.remove(leader)
					for r in leader.zone_rooms:
						r.zone = room.zone
					room.zone.zone_rooms += leader.zone_rooms
					leader = room.zone

		return leader


	def create_zones(self):

		# create trees
		self.find_gates()
		for room in self.processed:
			room.links = list()
			room.zone = None

		for collector in self.collectors:

			collector.is_leader = False
			collector.zone_collectors = list()
			collector.zone_rooms = list()
			collector.name ="unassigned"
			collector.zone_num = 0
			collector.number = 0

			leader = self.merge_rooms(collector)

			if leader:
				leader.zone_collectors.append(collector)

		# number zones
		zone_num = 0
		for zone in self.zones:
			zone_num += 1
			number = 1
			for collector in zone.zone_collectors:
				collector.zone_num = zone_num
				collector.number = number
				collector.name = 'C' + str(collector.zone_num)
				collector.name += '.' + str(collector.number)
				number += 1

		self.best_dist = MAX_DIST
		for collector in self.collectors:
			collector.reset()

		self.processed.sort(key=lambda x: x.links[0][1], reverse=True)

		# trim distance vectors
		for room in self.processed:
			room.links.sort(key=lambda x: x[1])
			if (room.links[0][1]> Config.max_clt_distance
					and not room.fixed_collector):
				self.output.print(
					"ABORT: No collectors from Room %d @\n" % room.pindex)
				self.output.print("Check %s layer @" % Config.layer_error +
					" to visualize errors @\n")

				room.poly.dxf.layer = Config.layer_error
				return False


		bound = 0
		for room in reversed(self.processed):
			if (room.fixed_collector or
				room.color==Config.color_disabled_room):
				room.bound = 0
				continue
			room.bound = bound
			bound += room.links[0][1]
			#print(room.pindex, room.bound, room.links[0][1])

		for room in self.processed:
			i = 0
			for i, link in enumerate(room.links):
				if (link[1]>Config.max_clt_distance
					or i>=max_clt_break):
					break

			if (i+1 < len(room.links)):
				del room.links[i:]

		return True


	def autoscale(self) -> float:

		total_area = 0.
		for poly in self.polylines:
			total_area += Model.polyline_area(poly)

		n = len(self.polylines)

		return pow(10, ceil(log10(sqrt(n/total_area))))


	def check_polyline_color(self, poly):

		if (poly.dxf.color == 256):
			# BYLAYER poly color
			poly.dxf.color = self.layer_color

		if (not (poly.dxf.color == Config.color_collector or
				 poly.dxf.color == Config.color_obstacle or
				 poly.dxf.color == Config.color_bathroom or
				 poly.dxf.color == Config.color_valid_room or
				 poly.dxf.color == Config.color_zone or
				 poly.dxf.color == Config.color_neutral or
				 poly.dxf.color == Config.color_disabled_room)):
			return False
		return True

	# Connect rooms to collectors using branch-and-bound
	def connect_rooms(self, room_iter, partial):

		global tot_iterations, max_iterations

		# Check if time to give up
		if (tot_iterations % 100e3 == 0):
			print("#")
		tot_iterations += 1
		if (tot_iterations > max_iterations):
			return

		room = next(room_iter)
		while (room and len(room.links)==0 and
			not room.fixed_collector):
			room = next(room_iter)

		# Terminal case
		if (room == None):

			if (partial < self.best_dist):
				# Found solution
				self.found_one = True

				self.best_dist = partial
				self.best_list = list()
				ir = iter(self.processed)
				while (x:=next(ir)) != None:
					if x.color == Config.color_disabled_room:
						continue
					if x.fixed_collector:
						x.collector = x.fixed_collector
						x.uplink = x.collector.contained_in
						continue
					x.uplink = x._uplink
					x.collector = x._collector

				for collector in self.collectors:
					item = (collector, copy(collector.items))
					self.best_list.append(item)
				return

		# skip disabled room
		if room.color == Config.color_disabled_room:
			self.connect_rooms(copy(room_iter), partial)
			return

		# if collector is fixed or room is ancillary,
		# just assign the collector and move on
		if room.fixed_collector or (
			room.group and not room.is_group_master):
			if room.fixed_collector:
				collector = room.fixed_collector

			if room.group:
				collector = room.group.group_master._collector
			room_dist = 0

			new_partial = partial + room_dist

			if ((new_partial+room.bound<self.best_dist and
				collector.freespace>=room.feeds and
				collector.freeflow>=room.flow)):
				collector.items.append(room)
				collector.freespace -= room.feeds
				collector.freeflow  -= room.flow
				room._uplink = collector.contained_in
				room._collector = collector
				self.connect_rooms(copy(room_iter), new_partial)
				collector.items.remove(room)
				collector.freespace += room.feeds
				collector.freeflow += room.flow
			return


		# Recursive cases
		for link in room.links:
			collector, room_dist, uplink = link

			# If room if fixed to a collector, skip
			# other collectors
			if room.fixed_collector:
				collector = room.fixed_collector
				room_dist = 0

			new_partial = partial + room_dist

			if ((new_partial+room.bound<self.best_dist and
				collector.freespace>=room.feeds and
				collector.freeflow>=room.flow)):
				collector.items.append(room)
				collector.freespace -= room.feeds
				collector.freeflow  -= room.flow
				room._uplink = uplink
				room._collector = collector
				self.connect_rooms(copy(room_iter), new_partial)
				collector.items.remove(room)
				collector.freespace += room.feeds
				collector.freeflow += room.flow


	def catalogue_polylines(self):

		# Create lists of rooms, obstacles, zones and collectors
		# from polylines in the input layer

		pindex = 1
		for poly in self.polylines:

			# check if poly color is allowed
			if (not self.check_polyline_color(poly)):
				wstr = "ABORT: Polyline color %d not allowed @" % poly.dxf.color
				self.output.print(wstr)
				return False

			color = poly.dxf.color
			area = self.scale * self.scale * Model.polyline_area(poly)
			if (area > Config.max_room_area and
				(color == Config.color_valid_room or
				 color == Config.color_bathroom)):
				wstr = "ABORT: Zone %d larger than %d m2 @\n" % (pindex,
					Config.max_room_area)
				wstr += "Consider splitting area \n\n"
				self.output.print(wstr)
				continue

			if (color == Config.color_collector):
				collector = Collector(poly)
				self.collectors.append(collector)
				continue

			if (color == Config.color_valid_room or
			   color == Config.color_bathroom):
				room = Room(poly, self.output)
				self.valid_rooms.append(room)
				continue

			if (color == Config.color_obstacle or
				color == Config.color_neutral):
				obstacle = Room(poly, self.output)
				self.obstacles.append(obstacle)
				continue

			if (color == Config.color_disabled_room):
				room = Room(poly, self.output)
				self.processed.append(room)
				continue

			if (color == Config.color_zone):
				room = Room(poly, self.output)
				self.user_zones.append(room)
				room.leader = None
				continue


	def classify_entities(self):
		for e in self.msp.query('*[layer=="%s"]' % self.inputlayer):
			if (e.dxftype() == 'LINE'):
				self.vectors.append(e)
				continue

			if (e.dxftype() == 'LWPOLYLINE'):


				# Add a final point to closed polylines
				if (not e.dxf.flags & LWPOLYLINE_CLOSED):

					points = list(e.vertices())
					# Check if the polyline is open with large final gap
					tol = Config.tolerance
					n = len(points)-1
					if (dist(points[0], points[n]) > tol):
						wstr = "WARNING: open polyline in layer %s @\n" \
							% self.inputlayer
						self.output.print(wstr)
						continue

				self.polylines.append(e)
				continue

			wstr = "WARNING: layer contains non-polyline: %s @\n" \
				% e.dxftype()
			self.output.print(wstr)

		if (len(self.polylines) == 0):
			wstr = "WARNING: layer %s does not contain polylines @\n" \
				% self.inputlayer
			self.output.print(wstr)


	def determine_scale(self):

		if (self.data['units'] == "auto"):
			self.scale = self.autoscale()
			print("Autoscale: 1 unit = %g cm\n" % self.scale)
		else:
			self.scale = float(self.data['units'])

		Config.tolerance /= self.scale
		Config.min_dist /= self.scale
		Config.min_dist2 /= self.scale
		Config.wall_depth /= self.scale
		Config.max_clt_distance /= self.scale


	def build_model(self):

		global tot_iterations, max_iterations

		if self.refit:
			self.output.print("******************************************\n");
			self.output.print("Detected existing plan, disable allocation\n");
			self.output.print("******************************************\n");


		self.classify_entities()
		self.determine_scale()
		self.catalogue_polylines()

		# check if the room is too small to be processed
		for room in self.valid_rooms:
			area = self.scale * self.scale * room.area
			if  (area < min_room_area):
				wstr = "WARNING: area less than %d m2: " % min_room_area
				wstr += "Consider changing scale! @\n"
				self.output.print(wstr)
				room.errorstr = wstr
				room.error = True
			else:
				self.processed.append(room)

		# renumber rooms
		self.processed.sort(reverse=True, key=lambda room: (room.ay, -room.ax))
		for pindex, room in enumerate(self.processed):
			room.pindex = pindex + 1


		# check if every collector is in a room
		for collector in self.collectors:

			for room in self.processed:
				if (room.contains(collector)):
					collector.contained_in = room
					room.obstacles.append(collector)
					break

			if (not collector.contained_in):
				min_dist_from_room = MAX_DIST
				for room in self.processed:
					dist_from_room = dist(room.pos, collector.pos)
					if dist_from_room < min_dist_from_room:
						min_dist_from_room = dist_from_room
						collector.contained_in = room


		# assings collectors to user zone
		for collector in self.collectors:
			collector.user_zone = None
			for zone in self.user_zones:
				if zone.contains(collector):
					if collector.user_zone != None:
						wstr = "ABORT: Collector inside two user zones @"
						self.output.print(wstr)
						return False
					else:
						collector.user_zone = zone


		# add guard box to collector
		for collector in self.collectors:
			points = collector.guard_box
			polyline = self.msp.add_lwpolyline(points)
			polyline.dxf.layer = self.inputlayer
			polyline.dxf.color = Config.color_obstacle
			if type(collector.contained_in) == Room:
				collector_box = Room(polyline, self.output)
				collector.contained_in.obstacles.append(collector_box)



		# assign rooms to user zones
		for room in self.processed:
			room.user_zone = None
			for zone in self.user_zones:
				if zone.contains(room):
					if room.user_zone != None:
						wstr = "ABORT: Room inside two user zones @"
						self.output.print(wstr)
						return False
					else:
						room.user_zone = zone


		# assign obstacles to rooms
		for obs in self.obstacles:
			for room in self.processed:
				if (obs.collides_with(room)):
					room.obstacles.append(obs)
					obs.contained_in = room


		# check if two rooms collide
		self.valid_rooms.sort(key=lambda room: room.ax)
		room = self.processed
		for i in range(len(room)):
			j=i+1
			while (j<len(room) and room[j].ax < room[i].bx):
				if (room[i].collides_with(room[j])):
					wstr = "ABORT: Collision between Room %d" % room[i].pindex
					wstr += " and Room %d @\n" % room[j].pindex
					wstr += ("Check %s in output drawing" % Config.layer_error +
					 " to visualize errors @\n")
					room[i].poly.dxf.layer = Config.layer_error
					room[j].poly.dxf.layer = Config.layer_error
					room[i].error = True
					room[j].error = True
					self.output.print(wstr)
					return False

				j += 1

		# check if two collectors collide
		for i in range(len(self.collectors)-1):
			for j in range(i+1, len(self.collectors)):
				if (self.collectors[i].collides_with(self.collectors[j])):
					wstr = "ABORT: Collision between collectors @\n"
					wstr += ("Check %s layer " % Config.layer_error +
					 "to visualize errors @")
					self.collectors[i].poly.dxf.layer = Config.layer_error
					self.collectors[j].poly.dxf.layer = Config.layer_error
					self.output.print(wstr)
					return False


		self.classify_vectors()

		for room in self.processed:
			room.frame.scale = self.scale
			# orient room without vector
			if (not room.frame.vector):
				room.frame.orient_frame()


		self.output.print("Detected rooms ........................... %3d\n"
			% len(self.processed))
		self.output.print("Detected collectors ....................... %2d\n"
			% len(self.collectors))
		if (len(self.collectors) == 0):
			self.output.print("ABORT: Please insert at least 1 collector @\n")
			return False


		# Check if room too large  for a collector
		for room in self.processed:
			area = self.scale * self.scale * room.area
			for obstacle in room.obstacles:
				area -= obstacle.area*self.scale*self.scale
			# flow = area*self.flow_per_m2*Config.target_eff
			flow = area*self.flow_per_m2

			group_size = 1
			if room.fixed_collector:
				group_size = len(room.fixed_collector.backup)

			if flow > group_size*Config.flow_per_collector:
				wstr = "ABORT: Room %d larger than a single collector @\n" %\
						room.pindex
				wstr += "capacity and not linked to any collector group. @\n"
				wstr += ("Check %s layer" % Config.layer_error +
					" to visualize errors @\n")
				room.poly.dxf.layer = Config.layer_error
				room.error = True
				self.output.print(wstr)
				print(wstr)

				return False

		# Check if enough collectors
		self.area = feeds_eff = feeds_max = 0
		flow_eff = flow_max = 0
		target_eff = Config.target_eff
		for room in self.processed:

			if room.color == Config.color_disabled_room:
				continue

			obs_area_tot = 0
			for obs in room.obstacles:
				if obs.color == Config.color_neutral:
					obs_area_tot += obs.area * self.scale * self.scale
			area = self.scale * self.scale * room.area - obs_area_tot

			room.feeds_eff = ceil(area/self.area_per_feed_m2*target_eff)
			room.feeds_max = ceil(area/self.area_per_feed_m2)
			feeds_eff += room.feeds_eff
			feeds_max += room.feeds_max
			# connect room based on max allocation
			room.feeds = room.feeds_max
			room.flow_eff = area*target_eff*self.flow_per_m2
			room.flow_max = area*self.flow_per_m2
			flow_eff += room.flow_eff
			flow_max += room.flow_max
			room.flow = room.flow_max
			#self.output.print("Room%3d   lines:%2d  flow:%6.2lf l/h\n" %
			#	(room.pindex, room.feeds, room.flow_eff))
			self.area += area

		available_feeds = Config.feeds_per_collector * len(self.collectors)
		available_flow  = Config.flow_per_collector * len(self.collectors)
		self.output.print("Available lines .......................... %3d\n"
				% available_feeds)
		self.output.print("Estimated lines for %2d%% cover ............ %3d\n"
				% (100*target_eff, feeds_eff))
		self.output.print("Estimated lines for 100%% cover ........... %3d\n"
				% feeds_max)
		self.output.print("Available flow ......................... %5d l/h\n"
				% available_flow)
		self.output.print("Estimated flow for %2d%% cover ............%5d l/h\n"
				% (100*target_eff, flow_eff))
		self.output.print("Estimated flow for 100%% cover .......... %5d l/h\n"
				% flow_max)

		################################################################
		if not self.create_zones():
			return False

		# Disabled room with collector forms its own zone
		for room in self.processed:
			if (room.color==Config.color_disabled_room
				and room.zone
				and not room.collector):
					room.collector = room.zone


		#  Mapping rooms to collectors
		self.mapping_rooms()
		if (not self.found_one):
			self.output.print("CRITICAL: Could not connect rooms @\n")
			return False


		# rotate room frase based on collector position
		for room in self.processed:
			if room.collector:
				room.frame.rotate_frame(room.collector.pos)

		return True


	def mapping_rooms(self):
		global tot_iterations, max_iterations

		# move extensions at the end of the list
		self.processed.sort(key=lambda x: x.is_group_master is False)

		for k in range(max_steps):

			extra_flow = extra_flow_probe * k
			extra_feeds = k//2

			self.best_dist = MAX_DIST
			for collector in self.collectors:
				collector.reset(extra_feeds, extra_flow)

			self.processed.append(None)    ;# Add sentinel
			room_iter = iter(self.processed)
			tot_iterations = 0
			self.found_one = False
			print("Linking Rooms (flow=%d l/h): " %
				(Config.flow_per_collector + extra_flow))
			self.connect_rooms(room_iter, 0)
			self.processed.pop()           ;# Remove sentinel
			if  (self.found_one):
				break


	def classify_vectors(self):

		for vector in self.vectors:

			p1 = (vector.dxf.start[0], vector.dxf.start[1])
			p2 = (vector.dxf.end[0], vector.dxf.end[1])

			elem1 = elem2 = None
			for elem in self.collectors + self.processed:
				if elem.is_point_inside(p1):
					elem1 = elem
					break

			for elem in self.collectors + self.processed:
				if elem.is_point_inside(p2):
					elem2 = elem
					break

			if (type(elem1) == Collector and
				type(elem2) == Collector and
				elem1 != elem2):
				for elem in elem1.backup:
					if not elem in elem2.backup:
						elem2.backup.append(elem)
				elem1.backup = elem2.backup
				continue

			if (type(elem1) == Collector and type(elem2) == Room):
				elem2.fixed_collector = elem1
				continue

			if (type(elem1) == Room and	type(elem2) == Collector):
				elem1.fixed_collector = elem2
				continue

			if (type(elem1) == Room and type(elem2) == Room and
				 elem1 == elem2):
				norm = dist(p1, p2)
				uv = elem1.frame.vector = \
				    (p2[0]-p1[0])/norm, (p2[1]-p1[1])/norm
				elem1.frame.rot_orig = p1
				elem1.frame.rot_angle = -atan2(uv[1], -uv[0])*180/pi
				elem1.vector = True
				continue

			if (type(elem1) == Room and
				type(elem2) == Room and
				elem1 != elem2):
				self.associate_rooms(elem1, elem2)
				continue

			wstr = "WARNING: Vector outside room @\n"
			wstr += ("Check %s layer" % Config.layer_error +
				" to visualize errors @")
			vector.dxf.layer = Config.layer_error
			self.output.print(wstr)


		# Move fixed collector to preferred collector
		# if it is not the main collector of the group
		for room in self.processed:
			if (room.fixed_collector and
				room.fixed_collector.backup[0] != room.fixed_collector):
				room.prefer_collector = room.fixed_collector
				room.fixed_collector = room.fixed_collector.backup[0]


	# Associate two rooms with a vectors
	def associate_rooms(self, room1: Room, room2: Room):

		if room1.group and not room2.group:
			if not room1.group.join(room2):
				wstr ="WARNING: Rooms %d and %d " % \
						(room1.pindex, room2.pindex)
				wstr += "associated with different collectors @\n"
				self.output.print(wstr)
			return

		if room2.group and not room1.group:
			if not room2.group.join(room1):
				wstr ="WARNING: Rooms %d and %d " % \
						(room1.pindex, room2.pindex)
				wstr += "associated with different collectors @\n"
				self.output.print(wstr)
			return

		if room1.group and room2.group:
			if room1.group == room2.group:
				return
			if not room1.group.merge(room2.group):
				wstr ="WARNING: Rooms %d and %d " % \
						(room1.pindex, room2.pindex)
				wstr += "associated with different collectors @\n"
				self.output.print(wstr)
				self.roomgroups.remove(room1.group)
			self.roomgroups.remove(room2.group)
			return

		group = RoomGroup()
		group.join(room1)
		group.join(room2)
		self.roomgroups.append(group)


	def get_locale(self, room: Room, collector: str) -> Locale:

		for locale in self.locales:
			if (locale.room == room and locale.collector == collector):
				return locale
		else:
			locale = Locale(room, collector)
			self.locales.append(locale)
			return locale



