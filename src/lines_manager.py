from lines import Dorsal, Line
from panels import Panel
from model import Model
from reference_frame import MAX_DIST, invert, versor
from room import Room
from settings import leo_types, Config
from geometry import Picture, dist, horizontal_distance, xprod 
from geometry import poly_t, point_t, vertical_distance


class LinesManager():

	def __init__(self):
		self.num_lines = 0
		self.pipe_length = 0.
		self.line_coverage_m2: float = Config.line_coverage_m2


	def build_lines(self, room: Room, ptype: str):

		if not room.panels:
			return

		self.get_dorsals(room, room.panels, ptype)
		self.mark_boxed_dorsals(room, room.local_points())
		self.partition_lines(room, ptype)
		for dorsals in self.best_partition:
			line = Line(dorsals)
			room.lines.append(line)

		self.mark_linear_dorsals(room)

		for line in room.lines:
			line.make_frontline()


	def setup_lines(self, room: Room):

		for line in room.lines:
			if not line.collector:
				continue

			for dorsal in line.dorsals:
				dorsal.facing_inward = dorsal.reversed or dorsal.boxed

			pos = room.frame.local_from_real(line.collector.pos)
			self.line_attachment(line, pos)


	def area_m2(self, room: Room) -> float:
		area = 0.
		for line in room.lines:
			area += line.area_m2
		return area


	def get_dorsals(self, room: Room, panels: list[Panel], ptype: str):

		self.panels = panels
		if panels == []:
			return

		self.line_coverage_m2 = 2.4 * leo_types[ptype]["panels"] + 0.01

		dorsal_row = -1
		for panel in panels:

			if (panel.dorsal_row != dorsal_row or
			   dorsal.area_m2 + panel.area_m2 > self.line_coverage_m2):
				dorsal = Dorsal(room)
			
				if (dorsal_row == panel.dorsal_row):
					dorsal.front_dorsal = False

				dorsal_row = panel.dorsal_row
				room.dorsals.append(dorsal)

			dorsal.insert(panel)


	def mark_boxed_dorsals(self, room: Room, poly: poly_t):
		
		if not room.dorsals:
			return

		prev = room.dorsals[0]
		if not prev.upright:
			for i, dorsal in enumerate(room.dorsals):


				if (dorsal.front[0] > prev.front[0] and
					prev.bottom - dorsal.front[1] < 
						Config.lateral_margin_cm):
						dorsal.boxed = True

				if i<len(room.dorsals)-1:
					next = room.dorsals[i+1]
					if (dorsal.front[0] > next.front[0] and
						dorsal.front[1] - next.top < 
							Config.lateral_margin_cm):
						dorsal.boxed = True

				gap = vertical_distance(poly, dorsal.front)
				if (gap < Config.lateral_margin_cm):
					dorsal.boxed = True

				prev = dorsal

		else:
			for i, dorsal in enumerate(room.dorsals):

				if (dorsal.front[1] < prev.front[1] and
					dorsal.front[0] - prev.bottom < 
						Config.lateral_margin_cm):
						dorsal.boxed = True

				if i<len(room.dorsals)-1:
					next = room.dorsals[i+1]
					if (dorsal.front[1] < next.front[1] and
						next.top - dorsal.front[0]  < 
							Config.lateral_margin_cm):
						dorsal.boxed = True

				gap = horizontal_distance(poly, dorsal.front)
				if (gap < Config.lateral_margin_cm):
					dorsal.boxed = True

				prev = dorsal

	
	def line_attachment(self, line: Line, pos: point_t):

		if len(line.dorsals) < 1:
			return

		dorsal = line.dorsals[0]

		if dorsal.bridged:
			line.dir_attach = dorsal.exit_dir
			return

		line.red_attach = dorsal.red_end
		line.blue_attach = dorsal.blue_end


		v = versor(dorsal.back, dorsal.front)
		s = versor(dorsal.front, pos)
		u0 = versor(dorsal.front, dorsal.side)

		dorsal.facing_forward = xprod(v, s) > Config.cos_beam_angle
		dorsal.facing_inward = xprod(u0, s) > 0	

		if not dorsal.detached:
			p = line.dir_attach = dorsal.exit_dir
			dorsal.facing_inward = xprod(p, u0) > 0
			return

		if dorsal.facing_forward: 
			line.dir_attach = v 
			return

		if dorsal.boxed and not dorsal.facing_inward:
			dorsal.facing_forward = True
			line.dir_attach = v 
			return

		line.dir_attach = u0 if dorsal.facing_inward else invert(u0)


	def print_partition(self, partition):

		print(end="P")
		for lines in partition:
			print(end="[")
			for dorsal in lines:
				print(end=" (%d->%.2f) " % 
					(dorsal.dorsal_row, dorsal.area_m2))
			print(end="]  ")
		print()



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

	
	def mark_linear_dorsals(self, room: Room):

		dors = room.dorsals
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
					

	def partition_lines(self, room: Room, ptype: str):

		dorsals = room.dorsals
		for extension in room.extensions:
			dorsals += extension.dorsals 

		if dorsals==[]:
			return

		self.line_coverage_m2 = 2.4 * leo_types[ptype]["panels"] + 0.01

		self.num_lines = len(room.dorsals) + 1 
		self.pipe_length = MAX_DIST

		self.best_partition = []
		for partition in self.partitions(dorsals, 1):
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



	def lines_picture(self, room: Room, poly: poly_t) -> Picture:

		picture = Picture()
		picture.add(poly, color="blue")

		for line in room.lines:
			for dorsal in line.dorsals:
				picture.add([dorsal.front, dorsal.side])
				picture.add([dorsal.side, dorsal.back_side])
				picture.add([dorsal.back_side, dorsal.back])
				picture.add([dorsal.back, dorsal.front])

				center = [(dorsal.front[0] + dorsal.back_side[0]) / 2,
						  (dorsal.front[1] + dorsal.back_side[1]) / 2]
				picture.text(center, str(dorsal.dorsal_row), color="red")

		return	picture


	def redistribute_lines(self, model: Model):
		flow_m2 = model.flow_per_m2

		for collector in model.collectors:

			if collector != collector.backup[0]:
				continue

			backup = collector.backup
			num_clt = len(backup)
			cap = Config.flow_per_collector * num_clt
			
			# select room in collector group
			room_group = []
			for room in model.processed:
				if room.collector == collector:
					room_group.append(room)
					if room.prefer_collector == None:
						room.prefer_collector = collector

			# calculate required flow
			required_flow = 0.
			for room in room_group:
				room.flow = room.area_m2() * flow_m2
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
			
				for line in room.lines:
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
