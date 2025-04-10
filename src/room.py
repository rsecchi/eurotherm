from typing import Optional
from ezdxf.entities.lwpolyline import LWPolyline
from collector import Collector
from element import Element
from geometry import dist
from settings import Config
from lines import Panel, LinesManager
from engine.panels import panel_map
from math import sqrt

MAX_DIST  = 1e20


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

	if ((w <= Config.min_dist) or
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

	if (abs(l1-l2)<=Config.min_dist):
		return (False, (None, None))

	d1 = abs((npy*(nqx-l1) - (npx-l1)*nqy)/w)
	d2 = abs((npy*(nqx-l2) - (npx-l2)*nqy)/w)
	
	if (d1<= Config.wall_depth and d2<=Config.wall_depth):
		return (True, (p1, p2))

	return (False, (None, None))



class Room(Element):

	def __init__(self, poly:LWPolyline, output):

		Element.__init__(self, poly)
		self.pindex = 0
		self.output = output
		self.ignore = False
		self.error = False
		self.errorstr = ""
		self.obstacles = list()
		self.gates = list()
		self.links = list()
		self.bridges = list()
		self.joined_lines = list()
		self.total_lines = 0
		self.sup = 0
		self.inf = 0
		self.fixed_collector: Optional[Collector] = None
		self.prefer_collector: Optional[Collector] = None
		self.vector = False

		self.leader = None
		self.uplink = None
		self.walk = MAX_DIST
		self.links = list()

		self.orient = 0
		self.boxes = list()
		self.coord = list()
		self.collector: Optional[Collector] = None


		self.straighten_walls()

		# feeds/flow estimates
		self.feeds_eff = 0.0
		self.feeds_max = 0.0
		self.flow_eff = 0.0
		self.flow_max = 0.0
		self.feeds = 0
		self.flow = 0.0


		# self.arrangement = PanelArrangement(self)
		self.panels: list[Panel] = list()
		self.panel_register: list[int] = []
		self.quarters = 0
		self.lines_manager = LinesManager()
		self.active_m2 = 0.0
		self.ratio = 0.0


		self.panel_record = dict()
		for panel in panel_map:
			self.panel_record[panel+"_classic"] = 0
			self.panel_record[panel+"_hydro"] = 0
	

	def straighten_walls(self):

		# Straighten up walls
		finished = False
		p = self.points
		tol = Config.tolerance
		n = len(p)-1
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



