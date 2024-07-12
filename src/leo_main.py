import os, sys
local_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(local_dir)
sys.path.append('..')

from reference_frame import ReferenceFrame
from components import ComponentManager
from drawing import DxfDrawing
from settings import Config

import json
import atexit

from math import sqrt, ceil, log10, atan2, pi

from ezdxf.math import Vec2, intersection_line_line_2d, convex_hull_2d
from copy import copy

from ezdxf.filemanagement import readfile



# Parameter settings (values in cm)
default_scale = 1  # scale=100 if the drawing is in m
default_tolerance    = 1   # ignore too little variations

default_panel_width = 100
default_panel_height = 60
default_search_tol = 5
default_hatch_width = 12
default_hatch_height = 20
default_collector_size = 60
default_wall_depth = 101
default_min_dist = 20
default_min_dist2 = default_min_dist*default_min_dist
default_max_clt_distance = 3000
default_add_offs = 10
default_add_dist = 4

collector_margin_factor = 1.5

flow_per_m2 = 23.33
flow_per_collector = 1700
feeds_per_collector = 13
target_eff = 0.7

min_room_area = 1
max_room_area = 500
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

def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)

def is_gate(line, target):
	
	(xa0,ya0), (xa1,ya1) = line
	(xb0,yb0), (xb1,yb1) = target

	# reference on target
	(ux, uy) = (xb1-xb0, yb1-yb0)
	u = sqrt(ux*ux + uy*uy)
	if (u==0):
		return (False, (None, None))
	(uvx, uvy) = (ux/u, uy/u)
	(uox, uoy) = (-uvy, uvx)
	
	# change of reference for p and q
	(px, py) = (xa0-xb0, ya0-yb0)
	(qx, qy) = (xa1-xb0, ya1-yb0)
	(npx, npy) = (uvx*px+uvy*py, uox*px+uoy*py)
	(nqx, nqy) = (uvx*qx+uvy*qy, uox*qx+uoy*qy)

	w = abs(npx - nqx)

	if ((w <= min_dist) or
		(npx<=0 and nqx<=0) or (npx>=u and nqx>=u)):
		return (False, (None, None))

	if (npx<0):
		p1 = (xb0,yb0)
		l1 = 0
	else:
		if (npx>u):
			p1 = (xb1,yb1)
			l1 = u
		else:
			p1 = (xb0+uvx*npx, yb0+uvy*npx)
			l1 = npx

	if (nqx<0):
		p2 = (xb0,yb0)
		l2 = 0
	else:
		if (nqx>u):
			p2 = (xb1,yb1)
			l2 = u
		else:
			p2 = (xb0+uvx*nqx, yb0+uvy*nqx)
			l2 = nqx

	if (abs(l1-l2)<=min_dist):
		return (False, (None, None))

	d1 = abs((npy*(nqx-l1) - (npx-l1)*nqy)/w)
	d2 = abs((npy*(nqx-l2) - (npx-l2)*nqy)/w)
	
	if (d1<= wall_depth and d2<=wall_depth):
		return (True, (p1, p2))

	return (False, (None, None))




class Room:

	index = 1

	def __init__(self, poly, output):

		self.poly = poly
		self.index = Room.index
		self.pindex = 0
		Room.index = Room.index + 1
		self.output = output
		self.ignore = False
		self.error = False
		self.errorstr = ""
		self.contained_in = None
		self.obstacles = list()
		self.gates = list()
		self.lines = list()
		self.bridges = list()
		self.joined_lines = list()
		self.total_lines = 0
		self.sup = 0
		self.inf = 0
		self.fixed_collector = None
		self.walk = 0
		self.is_collector = False
		self.leader = None

		tol = tolerance
		self.orient = 0
		self.boxes = list()
		self.coord = list()

		self.points = list(poly.vertices())	
		self.vector = None
		self.vector_auto = False
		self.frame = ReferenceFrame(self)

		# Add a final point to closed polylines
		p = self.points
		if (poly.is_closed):
			self.points.append((p[0][0], p[0][1]))

		# Check if the polyine is open with large final gap
		n = len(p)-1
		if (abs(p[0][0]-p[n][0])>tol or abs(p[0][1]-p[n][1])>tol):
			self.ignore = True
			return

		# Straighten up walls
		finished = False
		while not finished:
			for i in range(1, len(p)):
				if (abs(p[i][0]-p[i-1][0]) < tol):
					p[i] = (p[i-1][0], p[i][1])

				if (abs(p[i][1]-p[i-1][1]) < tol):
					p[i] = (p[i][0], p[i-1][1])

			if (p[0] == p[n]):
				finished = True
			else:
				p[0] = p[n]


		self.color = poly.dxf.color
		# self.arrangement = PanelArrangement(self)
		self.panels = list()
		self.bounding_box()
		self.area = self._area()
		self.pos = self._barycentre()
		self.perimeter = self._perimeter()
		self.collector = None
		self.inputs = 0 

	def _area(self):
		a = 0
		p = self.points
		for i in range(0, len(p)-1):
			a += (p[i+1][0]-p[i][0])*(p[i+1][1] + p[i][1])/2
		return abs(a/10000)

	def _centre(self):
		(cx, cy) = (0, 0)
		p = self.points
		n = len(p)-1
		for i in range(0,n):
			p = self.points[i]
			(cx, cy) = (cx+p[0], cy+p[1])

		return (cx/n, cy/n)
		

	def _perimeter(self):
		p = self.points
		d = 0
		for i in range(0, len(p)-1):
			d += sqrt(pow(p[i+1][0]-p[i][0],2)+pow(p[i+1][1]-p[i][1],2))
		return d

	def _barycentre(self):
		
		p = self.points
		(xb, yb) = (0, 0)
		Ax = Ay = 0
		for i in range(len(p)-1):
			(x0, y0) = p[i]
			(x1, y1) = p[i+1]
			xb += (y1-y0)*(x0*x0+x0*x1+x1*x1)/6
			yb += (x1-x0)*(y0*y0+y0*y1+y1*y1)/6
			Ax += (y1-y0)*(x0+x1)/2
			Ay += (x1-x0)*(y0+y1)/2
		
		if (Ax!=0 and Ay!=0):
			return (xb/Ax, yb/Ay)
		else:
			return (0, 0)

	def bounding_box(self):

		# Projections of coordinates on x and y
		self.xcoord = sorted(set([p[0] for p in self.points]))	
		self.ycoord = sorted(set([p[1] for p in self.points]))	

		self.ax = min(self.xcoord)
		self.bx = max(self.xcoord)
		self.ay = min(self.ycoord)
		self.by = max(self.ycoord)
		

	def orient_room(self):
		global max_room_area

		uvx = 0
		uvy = 0
		max_rot_orig = 0
		vtx = [(p[0],p[1],0) for p in self.points]
		conv_hull = convex_hull_2d(vtx)
		ch = [(s.x, s.y) for s in conv_hull]
		ch = [*ch, ch[0]]

		max_area = MAX_DIST2
		max_uv = (1,0)
		for i in range(len(ch)-1):
			p0, p1 = ch[i], ch[i+1]
			norm_uv = dist(p0, p1)
			if (norm_uv == 0):
				continue
			uvx, uvy = uv = (p1[0]-p0[0])/norm_uv, (p1[1]-p0[1])/norm_uv
			bxm = bxM = 0; by = 0
			for p in ch[:-1]:
				px =  uvx*(p[0]-p0[0]) + uvy*(p[1]-p0[1])
				py = abs(-uvy*(p[0]-p0[0]) + uvx*(p[1]-p0[1]))
				if (py > by):
					by = py

				if (px < bxm):
					bxm = px
				if (px > bxM):
					bxM = px

			Ar = (bxM - bxm)*by
			if ( Ar < max_area ):
				max_area = Ar
				max_uv = uv
				max_rot_orig = p0

		angle = min(abs(uvx),abs(uvy))/max(abs(uvx),abs(uvy))
		if (angle > 0.01):
			self.vector = True
			self.vector_auto = True
			self.uvector = max_uv
			self.rot_orig = max_rot_orig
			self.rot_angle = -atan2(max_uv[1], -max_uv[0])*180/pi
				

	def is_point_inside(self, point):

		p = self.points
		x, y = point
		ints = 0

		for i in range(0, len(p)-1):
	
			if (p[i][0]==x and p[i+1][0]==x):
				if (max(p[i][1], p[i+1][1]) >= y
				  and min(p[i][1], p[i+1][1]) <=y):
					return True

			if (p[i][0] == p[i+1][0]):
				continue	

			if (p[i][0] < p[i+1][0]):
				x0, y0 = p[i][0], p[i][1]
				x1, y1 = p[i+1][0], p[i+1][1]
			else:
				x0, y0 = p[i+1][0], p[i+1][1]
				x1, y1 = p[i][0], p[i][1]

			
			if (x0<=x and x<x1):
				if (y0==y1 and y0==y):
					return True

				delta = x1 - x0
				py = (y0*(x1-x) - y1*(x0-x))/delta
				if (py>=y):
					ints += 1

		return (ints % 2 == 1)



	def contains(self, room):
		for point in room.points:
			if (self.is_point_inside(point)):
				return True

		return False


	def collides_with(self, room):

		# check if BBs overlap
		if (self.ax > room.bx or
			self.bx < room.ax or
			self.ay > room.by or
			self.by < room.ay):
			return False

		# check if room contains self or is contained
		if (room.contains(self) or self.contains(room)):
			return True

		# check if polylines cross each other
		p = self.points
		q = room.points
		for i in range(0, len(p)-1):
			line1 = (Vec2(p[i]), Vec2(p[i+1]))
			for j in range(0, len(q)-1):
				line2 = (Vec2(q[j]), Vec2(q[j+1]))
				if (intersection_line_line_2d(line1, line2, virtual=False)):
					return True

		return False
		

	def add_gates(self, room):
		p1 = self.points
		p2 = room.points
		for i in range(0, len(p1)-1):
			line1 = (p1[i], p1[i+1]) 
			for j in range(0, len(p2)-1):
				line2 = (p2[j], p2[j+1]) 
				cond, wall = is_gate(line2, line1)
				if (cond):
					self.gates.append((room, wall))

	def set_as_root(self, queue, collector):
		self.visited = True

		for room, _ in self.gates:
			if (not room.visited):
				if (collector.contained_in == self):
					pos = collector.pos
				else:
					pos = self.pos
				distance = dist(pos, room.pos)
				walk = self.walk + distance
				if (walk < room.walk):
					room.walk = walk
					room.uplink = self

		# select next room
		if (len(queue)>0):
			queue.sort(key=lambda x: x.walk)
			next_room = queue.pop(0)
			next_room.set_as_root(queue, collector)

	def contains_vector(self, v):
		p1 = (v.dxf.start[0], v.dxf.start[1])
		p2 = (v.dxf.end[0], v.dxf.end[1])
		if (p1 == p2):
			return False
		return self.is_point_inside(p1) and self.is_point_inside(p2)





class Model():
	def __init__(self, data):

		global block_blue_120x100 
		global block_blue_60x100 
		global block_green_120x100
		global block_green_60x100
		global block_collector
		global area_per_feed_m2

		super(Model, self).__init__()
		self.data = data
		self.rooms = list()
		self.vectors = list()
		self.collectors = list()
		self.valid_rooms = list()
		self.processed = list()
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

		for	ctype in panel_types:
			if (ctype['handler'] == data['ptype']):
				self.type = ctype['full_name']
		self.input_file = data['cfg_dir'] + "/" + data['infile']
	
		self.input_doc = readfile(self.input_file)	
		self.msp = self.input_doc.modelspace()
		self.refit = False
		for layer in self.input_doc.layers:
			if layer.dxf.name == Config.layer_panel:
				self.refit = True


		self.scale = default_scale 
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
			return

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

				area_per_feed_m2 = ptype['panels'] * 2.4
				flow_per_m2 = ptype['flow_panel'] / 2.4
				print('Area/line = %g m2' % area_per_feed_m2)
				print('Flow_per_m2 = %g l/m2' % flow_per_m2)


	def print(self, text):
		self.text += text
		#print(text, end='')

	def insert(self, text):
		print(text, end='')


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

		root.walk = 0
		root.uplink = root
		root.set_as_root(self.processed.copy(), collector)

		# leader: reference zone for collector
		leader = None 
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
			collector.freespace = feeds_per_collector 
			collector.freeflow = flow_per_collector
			collector.items = list()

		self.processed.sort(key=lambda x: x.links[0][1], reverse=True)

		# trim distance vectors
		for room in self.processed:
			room.links.sort(key=lambda x: x[1])
			if (room.links[0][1]> max_clt_distance 
					and not room.fixed_collector):
				self.output.print(
					"ABORT: No collectors from Room %d @\n" % room.pindex)
				self.output.print("Check %s layer @" % Config.layer_error + 
					" to visualize errors @\n")

				room.poly.dxf.layer = Config.layer_error
				self.output_error()
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
				if (link[1]>max_clt_distance 
					or i>=max_clt_break):
					break

			if (i+1 < len(room.links)):
				del room.links[i:]

		return True


	def rescale_model(self):

		global tolerance 
		global font_size
		global default_scale
		global default_panel_width
		global default_panel_height
		global default_search_tol
		global default_hatch_width
		global default_hatch_height
		global default_collector_size
		global default_min_dist
		global default_min_dist2
		global default_wall_depth
		global default_max_clt_distance
		global default_add_offs
		global default_add_dist

		global panel_width 
		global panel_height 
		global search_tol 
		global hatch_width
		global hatch_height
		global collector_size
		global min_dist
		global min_dist2
		global wall_depth
		global max_clt_distance
		global add_offs
		global add_dist

		scale = self.scale

		tolerance    = default_tolerance/scale
		font_size  = Config.font_size/scale

		panel_width = default_panel_width/scale
		panel_height = default_panel_height/scale
		search_tol = default_search_tol/scale
		hatch_width = default_hatch_width/scale
		hatch_height = default_hatch_height/scale
		collector_size = default_collector_size/scale
		min_dist = default_min_dist/scale
		min_dist2 = default_min_dist2/scale
		wall_depth = default_wall_depth/scale
		max_clt_distance = default_max_clt_distance/scale
		add_offs = default_add_offs/scale
		add_dist = default_add_dist/scale


	def autoscale(self):

		for e in self.msp.query('*[layer=="%s"]' % self.inputlayer):
			if (e.dxftype() == 'LINE'):
				continue
			if (e.dxftype() != 'LWPOLYLINE'):
				wstr = "WARNING: layer contains elements not allowed: %s @\n" % e.dxftype()
				self.output.print(wstr)

		searchstr = 'LWPOLYLINE[layer=="'+self.inputlayer+'"]'
		query = self.msp.query(searchstr)
		if (len(query) == 0):
			wstr = "WARNING: layer %s does not contain polylines @\n" % self.inputlayer
			self.output.print(wstr)

		n = 0
		tot = 0
		# Create list of rooms
		for poly in query:
			rm = Room(poly, self.output)
			if rm.ignore:
				wstr = "ABORT: Open polyline in layer %s @\n" % self.inputlayer
				self.output.print(wstr)
				return False
			tot += rm.area
			n += 1

		self.scale = pow(10, ceil(log10(sqrt(n/tot))))
		print("Autoscale: 1 unit = %g cm\n" % self.scale)
		return True

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

		# if collector is fixed, just to that case
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

	def build_model(self):
 
		global tot_iterations, max_iterations

		if self.refit:
			self.output.print("******************************************\n");
			self.output.print("Detected existing plan, disable allocation\n");
			self.output.print("******************************************\n");


		if (self.data['units'] == "auto"):
			self.rescale_model()
			if not self.autoscale():
				return False
		else:
			self.scale = float(self.data['units'])

		self.rescale_model()

		Room.index = 1
		# if not self.refit:
		# 	self.create_layers()
		
		for e in self.msp.query('*[layer=="%s"]' % self.inputlayer):
			if (e.dxftype() == 'LINE'):
				self.vectors.append(e)
				continue

			if (e.dxftype() != 'LWPOLYLINE'):
				wstr = "WARNING: layer contains non-polyline: %s @\n" \
					% e.dxftype()
				self.output.print(wstr)

		searchstr = 'LWPOLYLINE[layer=="'+self.inputlayer+'"]'
		self.query = self.msp.query(searchstr)
		if (len(self.query) == 0):
			wstr = "WARNING: layer %s does not contain polylines @\n" \
				% self.inputlayer
			self.output.print(wstr)


		pindex = 1
		# Create list of rooms, obstacles and collectors
		for poly in self.query:

			# check if poly color is allowed
			if (not self.check_polyline_color(poly)):
				wstr = "ABORT: Polyline color %d not allowed @" % poly.dxf.color
				self.output.print(wstr)
				return False

			room = Room(poly, self.output)
			self.rooms.append(room)

			if (len(room.errorstr)>0):
				# Invalid polyline
				room.error = True
				self.output.print(room.errorstr)
			else:

				# Valid polyline, classify room
				room.error = False
				area = self.scale * self.scale * room.area
				if (area > max_room_area and
				    (room.color == Config.color_valid_room or
				     room.color == Config.color_bathroom)):
					wstr = "ABORT: Zone %d larger than %d m2 @\n" % (room.index, 
						max_room_area)
					wstr += "Consider splitting area \n\n"
					self.output.print(wstr)
					room.errorstr = wstr
					room.error = True
					continue

				if (room.color == Config.color_collector):
					self.collectors.append(room)
					room.is_collector = True
					continue

				if (room.color == Config.color_valid_room or
				   room.color == Config.color_bathroom):
					self.valid_rooms.append(room)

				if (room.color == Config.color_obstacle or
				    room.color == Config.color_neutral):
					self.obstacles.append(room)

				if (room.color == Config.color_disabled_room):
					room.pindex = pindex
					pindex += 1
					self.processed.append(room)

				if (room.color == Config.color_zone):
					self.user_zones.append(room)
					room.leader = None


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
				room.pindex = pindex
				pindex += 1
				self.processed.append(room)

		# renumber rooms	
		self.processed.sort(reverse=True, key=lambda room: (room.ay, -room.ax))	
		pindex = 1
		for room in self.processed:
			room.pindex = pindex
			pindex += 1


		# check if every collector is in a room
		for collector in self.collectors:

			collector.contained_in = False
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

		# add margins to collector boundaries
		cmf = collector_margin_factor
		for collector in self.collectors:
			cx, cy = collector.pos
			points = list()
			poly = collector.poly
			for p in poly:
				points.append((cx+cmf*(p[0]-cx), cy+cmf*(p[1]-cy)))
			points.append((cx+cmf*(poly[0][0]-cx), cy+cmf*(poly[0][1]-cy)))
			
			polyline = self.msp.add_lwpolyline(points)
			polyline.dxf.layer = self.inputlayer
			polyline.dxf.color = Config.color_obstacle	
			collector_box = Room(polyline, self.output)
			collector.box = collector_box
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
					self.output.print(wstr)
					# self.output_error()
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
					# self.output_error()
					return False
	
		# check if vector is in room or 
		# across collector and room
		for v in self.vectors:

			p1 = (v.dxf.start[0], v.dxf.start[1])
			p2 = (v.dxf.end[0], v.dxf.end[1])

			p1_clt = p2_clt = None
			for clt in self.collectors:
				if clt.is_point_inside(p1):
					p1_clt = clt
					break;

				if clt.is_point_inside(p2):
					p2_clt = clt
					break

			for room in self.processed:

				if p1_clt and room.is_point_inside(p2):
					room.fixed_collector = p1_clt
					self.msp.delete_entity(v)
					break

				if p2_clt and room.is_point_inside(p1):
					room.fixed_collector = p2_clt
					self.msp.delete_entity(v)
					break

				if (room.contains_vector(v) and
					not (p1_clt or p2_clt)):
					# Allocate vector
					room.vector = v
					norm = dist(p1, p2)
					uv = room.uvector = (p2[0]-p1[0])/norm, (p2[1]-p1[1])/norm
					room.rot_orig = p1
					room.rot_angle = -atan2(uv[1], -uv[0])*180/pi
					break
			else:
				# Check if vector is vector fixes to collector

				wstr = "ABORT: Vector outside room @\n"
				wstr += ("Check %s layer" % Config.layer_error + 
					" to visualize errors @")
				v.dxf.layer = Config.layer_error
				self.output.print(wstr)
				#self.output_error()
				return False
	
		# orient room without vector
		# for room in self.processed:
		# 	if (not room.vector):
		# 		room.orient_room()	
	
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
			flow = area*flow_per_m2
			if flow > flow_per_collector:
				wstr = "ABORT: Room %d larger than collector capacity @\n" % room.pindex
				wstr += ("Check %s layer" % Config.layer_error + 
					" to visualize errors @\n")
				room.poly.dxf.layer = Config.layer_error
				self.output.print(wstr)
				#self.output_error()
				return False

		# Check if enough collectors
		tot_area = feeds_eff = feeds_max = 0
		flow_eff = flow_max = 0
		for room in self.processed:

			if room.color == Config.color_disabled_room:
				continue

			obs_area_tot = 0
			for obs in room.obstacles:
				obs_area_tot += obs.area * self.scale * self.scale
			area = self.scale * self.scale * room.area - obs_area_tot

			room.feeds_eff = ceil(area/area_per_feed_m2*target_eff)
			room.feeds_max = ceil(area/area_per_feed_m2)
			feeds_eff += room.feeds_eff
			feeds_max += room.feeds_max
			# connect room based on max allocation
			room.feeds = room.feeds_max
			room.flow_eff = area*target_eff*flow_per_m2
			room.flow_max = area*flow_per_m2
			flow_eff += room.flow_eff
			flow_max += room.flow_max
			room.flow = room.flow_max
			#self.output.print("Room%3d   lines:%2d  flow:%6.2lf l/h\n" % 
			#	(room.pindex, room.feeds, room.flow_eff))
			tot_area += area

		available_feeds = feeds_per_collector * len(self.collectors)
		available_flow  = flow_per_collector * len(self.collectors)
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

		# for collector in self.collectors:
		#self.draw_trees(self.collectors[5])

		#self.draw_gates()	
		#return

		################################################################
		#  Mapping rooms to collectors


		for k in range(max_steps):

			extra_flow = extra_flow_probe * k
			extra_feeds = k//2

			self.best_dist = MAX_DIST
			for collector in self.collectors:
				collector.freespace = feeds_per_collector + extra_feeds 
				collector.freeflow = flow_per_collector + extra_flow
				collector.items = list()

			self.processed.append(None)    ;# Add sentinel
			room_iter = iter(self.processed)
			tot_iterations = 0
			self.found_one = False
			print("Linking Rooms (flow=%d l/h): " %
				(flow_per_collector + extra_flow))
			self.connect_rooms(room_iter, 0)
			self.processed.pop()           ;# Remove sentinel
			if  (self.found_one):
				break

		if (not self.found_one):
			self.output.print("CRITICAL: Could not connect rooms @\n")
			return False

		return True


	# def populate(self):

	# 	self.num_panels = 0
	# 	for room in self.processed:
	# 		planner = RoomPlanner(room, scale)
	# 		room.panels = planner.get_panels()
	# 		self.num_panels += len(room.panels)

############ START PROCESS ##########################


# read configuration file into local dict
json_file = open(sys.argv[1], "r")
data = json.loads(json_file.read())
lock_name = data['lock_name']


def remove_lock():
	out = data['outfile'][:-4]+".txt"
	f = open(out, "w")
	print("Early exit", file = f)
	os.remove(lock_name)


# Acquire lock 
if os.path.exists(lock_name):
	print("ABORT: Resource busy")
open(lock_name, "w")	
atexit.register(remove_lock)


data['cfg_dir'] = os.path.dirname(sys.argv[1])

model = Model(data)
manager = ComponentManager()

outfile = data['cfg_dir'] + "/" + data['outfile'] 
dxfdrawing = DxfDrawing(outfile, model.refit, model.scale)

model.build_model()
manager.get_components(model)



dxfdrawing.save()



