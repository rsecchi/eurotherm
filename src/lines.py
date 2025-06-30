from pprint import pprint
from typing import Optional, Tuple
from planner import Panel
from collector import Collector
from reference_frame import adv, mul, versor
from settings import Config, dist, MAX_DIST
from geometry import Picture, horizontal_distance, vertical_distance
from geometry import trim, poly_t
from settings import leo_types

class Dorsal():
	def __init__(self):
		self.panels: list[Panel] = []
		self.front = (0., 0.)
		self.side = (0., 0.)
		self.back = (0., 0.)
		self.back_side = (0., 0.)
		self.area_m2 = 0.
		self.dorsal_row = 0
		self.front_dorsal = True
		self.upright = False
		self.terminal = False 
		self.detached = False
		self.reversed = False
		self.boxed = False
		self.water_from_left = False
		self.indented = False
		self.indent_front = (0., 0.)
		self.indent_side = (0., 0.)

		self.red_attach = (0., 0.)
		self.blue_attach = (0., 0.)
		self.bridged = False
		self.red_bridge: poly_t = []
		self.blue_bridge: poly_t = []
		self.top = 0.
		self.bottom = 0.
		self.level = 0.
		self.wide_size = False

		self.x_axis = (0., 0.)
		self.y_axis = (0., 0.)
		self.rot = 0


	def flow(self) -> float:
		flow = 0.
		for panel in self.panels:
			print(panel)	
		return flow


	def dorsal_to_local(self, point: Tuple, orig: Tuple):

		x0, y0 = point
		ux, uy = self.x_axis
		vx, vy = self.y_axis

		rx = ux * x0 + vx * y0
		ry = uy * x0 + vy * y0

		return (rx + orig[0], ry + orig[1])


	def local_attachments(self):

		if self.reversed:
			offs_red = (Config.attach_red_left, Config.offset_red)
			offs_blue = (Config.attach_blue_left, Config.offset_blue)
		else:
			offs_red = (Config.attach_red_right, Config.offset_red)
			offs_blue = (Config.attach_blue_right, Config.offset_blue)

		self.red_attach = self.dorsal_to_local(offs_red, self.front)
		self.blue_attach = self.dorsal_to_local(offs_blue, self.front)


	def insert(self, panel: Panel):

		self.dorsal_row = panel.dorsal_row
		self.area_m2 += panel.area_m2

		self.front = panel.front_corner
		self.side = panel.front_side

		self.wide_size = True if panel.type in [0, 1, 3] else False

		if not self.panels:
			self.rot = panel.rot
			self.water_from_left = (self.rot==0 or self.rot==3)
			self.upright = (panel.rot == 1 or panel.rot == 3)
			self.back = panel.rear_corner
			self.back_side = panel.rear_side

			dx = dist(self.front, self.back)
			dy = dist(self.back_side, self.back)
			dx_x = self.front[0] - self.back[0]
			dx_y = self.front[1] - self.back[1]
			dy_x = self.back_side[0] - self.back[0]
			dy_y = self.back_side[1] - self.back[1]
			self.x_axis = (dx_x/dx, dx_y/dx)
			self.y_axis = (dy_x/dy, dy_y/dy)
			ux, uy = self.x_axis
			vx, vy = self.y_axis
			if ux*vy < vx*uy:
				self.reversed = True

		if self.upright:
			self.top = min(self.front[0], self.side[0])
			self.bottom = max(self.front[0], self.side[0])
			self.level = self.front[1]
		else:
			self.top = max(self.front[1], self.side[1])
			self.bottom = min(self.front[1], self.side[1])
			self.level = self.front[0]

		self.local_attachments()
		self.panels = [panel] + self.panels



class Line:

	def __init__(self, dorsals: list[Dorsal]):
		self.dorsals = dorsals
		self.flipped = False
		self.area_m2 = 0.
		self.red_frontline: poly_t = []
		self.blue_frontline: poly_t = []
		self.collector: Optional[Collector] = None
		self.red_attach = (0., 0.)
		self.blue_attach = (0., 0.)

		self.uplink_red: poly_t = []
		self.uplink_blue: poly_t = []

		for dorsal in dorsals:
			self.area_m2 += dorsal.area_m2

		if len(dorsals)>0:
			self.dorsals[-1].terminal = True

		if len(dorsals)==1:
			self.dorsals[0].detached = True


	def __str__(self) -> str:
		_string = ""
		for dorsal in self.dorsals:
			_string += "[" + str(dorsal.area_m2) + "]"

		return _string


	def front_line(self, offset) -> list[Tuple]:

		_line = []
		for dorsal in self.dorsals:
			ofs = (offset, .0)
			if dorsal.indented:
				front = dorsal.dorsal_to_local(ofs, dorsal.indent_front)
				side = dorsal.dorsal_to_local(ofs, dorsal.indent_side)
			else:
				front = dorsal.dorsal_to_local(ofs, dorsal.front)
				side = dorsal.dorsal_to_local(ofs, dorsal.side)

			if dorsal.rot == 2 or dorsal.rot == 3:				
				front, side = side, front

			_line.append(front)
			_line.append(side)

			
		return _line	


class LinesManager():

	def __init__(self):
		self.dorsals: list[Dorsal] = []
		self.panels: list[Panel] = []
		self.num_lines = 0
		self.pipe_length = 0.
		self.lines: list[Line] = []
		self.line_coverage_m2: float = Config.line_coverage_m2


	def area_m2(self) -> float:
		area = 0.
		for line in self.lines:
			area += line.area_m2
		return area


	def append(self, line: Line):
		self.lines.append(line)


	def get_dorsals(self, panels: list[Panel], ptype: str):

		self.panels = panels
		if panels == []:
			return

		self.line_coverage_m2 = 2.4 * leo_types[ptype]["panels"] + 0.01

		dorsal_row = -1
		for panel in panels:

			if (panel.dorsal_row != dorsal_row or
			   dorsal.area_m2 + panel.area_m2 > self.line_coverage_m2):
				dorsal = Dorsal()
			
				if (dorsal_row == panel.dorsal_row):
					dorsal.front_dorsal = False

				dorsal_row = panel.dorsal_row
				self.dorsals.append(dorsal)

			dorsal.insert(panel)


	def mark_boxed_dorsals(self, poly: poly_t):
		
		if not self.dorsals:
			return

		prev = self.dorsals[0]
		if not prev.upright:
			for i, dorsal in enumerate(self.dorsals):


				if (dorsal.front[0] > prev.front[0] and
					prev.bottom - dorsal.front[1] < 
						Config.lateral_margin_cm):
						dorsal.boxed = True

				if i<len(self.dorsals)-1:
					next = self.dorsals[i+1]
					if (dorsal.front[0] > next.front[0] and
						dorsal.front[1] - next.top < 
							Config.lateral_margin_cm):
						dorsal.boxed = True

				gap = vertical_distance(poly, dorsal.front)
				if (gap < Config.lateral_margin_cm):
					dorsal.boxed = True

				prev = dorsal

		else:
			for i, dorsal in enumerate(self.dorsals):

				if (dorsal.front[1] < prev.front[1] and
					dorsal.front[0] - prev.bottom < 
						Config.lateral_margin_cm):
						dorsal.boxed = True

				if i<len(self.dorsals)-1:
					next = self.dorsals[i+1]
					if (dorsal.front[1] < next.front[1] and
						next.top - dorsal.front[0]  < 
							Config.lateral_margin_cm):
						dorsal.boxed = True

				gap = horizontal_distance(poly, dorsal.front)
				if (gap < Config.lateral_margin_cm):
					dorsal.boxed = True

				prev = dorsal


	def make_frontline(self, line: Line):

		if not line.dorsals:
			return

		r_line = line.red_frontline
		b_line = line.blue_frontline

		for dorsal in reversed(line.dorsals):
			v = versor(dorsal.back, dorsal.front)
			u = versor(dorsal.front, dorsal.side)

			us = mul(Config.tfit_offset,u)
			vs = mul(Config.offset_front_cm,v)
			red_end = adv(dorsal.red_attach, vs)
			blue_end = adv(dorsal.blue_attach, vs)

			if dorsal.boxed and not dorsal.terminal:
				red_bridge_end = adv(red_end, us)
				blue_bridge_end = adv(blue_end, us)
				dorsal.bridged = True
				dorsal.red_bridge = [red_end, red_bridge_end]
				dorsal.blue_bridge = [blue_end, blue_bridge_end]
				red_end = red_bridge_end
				blue_end = blue_bridge_end

			r_line.append(red_end)
			b_line.append(blue_end)

		line.red_attach = r_line[-1]
		line.blue_attach = b_line[-1]

		stub = mul(Config.bridge_stub_length_cm, v)
		red_stub = adv(line.red_attach, stub)
		blue_stub = adv(line.blue_attach, stub)
		line.uplink_red = [r_line[-1], red_stub]
		line.uplink_blue = [b_line[-1], blue_stub]


		# dorsal = line.dorsals[-1]

		# if dorsal.reversed:
		# 	line.red_frontline = line.front_line(Config.supply_out)
		# 	line.blue_frontline = line.front_line(Config.supply_in)
		# else:
		# 	line.red_frontline = line.front_line(Config.supply_in)
		# 	line.blue_frontline = line.front_line(Config.supply_out)

		# # trim back of frontlines
		# red  = [(0., Config.offset_red), (-100., Config.offset_red)]
		# blue = [(0., Config.offset_blue), (-100., Config.offset_blue)]

		# r_trim = [dorsal.dorsal_to_local(red[0], dorsal.front),
		# 			   dorsal.dorsal_to_local(red[1], dorsal.front)]

		# b_trim = [dorsal.dorsal_to_local(blue[0], dorsal.front),
		# 			   dorsal.dorsal_to_local(blue[1], dorsal.front)]

		# r_line = trim(line.red_frontline, r_trim, from_tail=False)
		# b_line = trim(line.blue_frontline, b_trim, from_tail=False)

		# # Project indented fronts
		# if dorsal.indented:
		# 	r_line.append(dorsal.red_attach)
		# 	b_line.append(dorsal.blue_attach)

		# line.red_frontline = r_line
		# line.blue_frontline = b_line



	def print_partition(self, partition):

		print(end="P")
		for lines in partition:
			print(end="[")
			for dorsal in lines:
				print(end=" (%d->%.2f) " % 
					(dorsal.dorsal_row, dorsal.area_m2))
			print(end="]  ")
		print()


	def make_lines(self):

		for dorsals in self.best_partition:
			line = Line(dorsals)
			self.append(line)

		self.mark_linear_dorsals()

		for line in self.lines:
			self.make_frontline(line)


	def partitions(self, l: list[Dorsal], level: int):

		if level > self.num_lines:
			return

		n = len(l) - 1
		for i in range(2**n-1, -1, -1):

			first = [l[0]]
			others = []

			area_m2 = l[0].area_m2
			for j in range(n):
				if (i&(2**j)>0):
					first.append(l[j+1])
					area_m2 += l[j+1].area_m2
				else:
					others.append(l[j+1])

			if area_m2 > self.line_coverage_m2:
				continue

			if others == []:
				yield [l]
				continue

			for group in self.partitions(others, level+1):
				yield [first, *group]
		

	def eval(self, lines) -> float:
		
		total_length = 0.
		for line in lines:
			length = 0.
			point = line[0].front
			for dorsal in line:
				point_next = dorsal.front
				length += dist(point_next, point)
				point = point_next

			total_length += length

		return total_length

	
	def mark_linear_dorsals(self):

		dors = self.dorsals
		for i, dorsal in enumerate(dors):
			if not (dorsal.terminal and dorsal.dorsal_row>0):
				continue

			level = dors[i].level
			prev_level = dors[i-1].level
			curr_top = dors[i].top
			prev_btm = dors[i-1].bottom

			if not dorsal.upright:
				if abs(prev_btm-curr_top)<1 and (level>prev_level):
					dorsal.indented = True
					dorsal.indent_front = (prev_level, dorsal.front[1])
					dorsal.indent_side = (prev_level, dorsal.side[1])

			if dorsal.upright:
				if abs(prev_btm-curr_top)<1 and (level<prev_level):
					dorsal.indented = True
					dorsal.indent_front = (prev_level, dorsal.front[1])
					dorsal.indent_side = (prev_level, dorsal.side[1])
					

	def get_lines(self, ptype: str):

		if self.dorsals==[]:
			return

		self.line_coverage_m2 = 2.4 * leo_types[ptype]["panels"] + 0.01

		self.num_lines = len(self.dorsals) + 1 
		self.pipe_length = MAX_DIST

		self.best_partition = []
		for partition in self.partitions(self.dorsals, 1):
			partition_length = len(partition)

			if partition_length > self.num_lines:
				continue

			pipe_length = self.eval(partition)

			if partition_length < self.num_lines:
				self.num_lines = partition_length
				self.pipe_length = pipe_length
				self.best_partition = partition	
				continue

			if pipe_length < self.pipe_length:
				self.num_lines = partition_length
				self.pipe_length = pipe_length
				self.best_partition = partition

		self.make_lines()


	def lines_picture(self, poly: poly_t) -> Picture:

		picture = Picture()
		picture.add(poly, color="blue")

		for line in self.lines:
			for dorsal in line.dorsals:
				picture.add([dorsal.front, dorsal.side])
				picture.add([dorsal.side, dorsal.back_side])
				picture.add([dorsal.back_side, dorsal.back])
				picture.add([dorsal.back, dorsal.front])

				center = [(dorsal.front[0] + dorsal.back_side[0]) / 2,
						  (dorsal.front[1] + dorsal.back_side[1]) / 2]
				picture.text(center, str(dorsal.dorsal_row), color="red")

		return	picture

