from typing import Tuple
from planner import Panel
from settings import Config, dist, MAX_DIST

class Dorsal:
	def __init__(self):
		self.panels: list[Panel] = []
		self.front = (0., 0.)
		self.back = (0., 0.)
		self.back_side = (0., 0.)
		self.area_m2 = 0.
		self.dorsal_row = 0
		self.front_dorsal = True
		self.flipped = False
		self.terminal = False 
		self.detached = False
		self.reversed = False

		self.x_axis = (0., 0.)
		self.y_axis = (0., 0.)
		self.rot = 0


	@staticmethod
	def local_rotation(rot):
		if rot==1 or rot==2:
			return (rot + 2) % 4
		return rot 


	def dorsal_to_local(self, point: Tuple, orig: Tuple):

		x0, y0 = point
		ux, uy = self.x_axis
		vx, vy = self.y_axis

		rx = ux * x0 + vx * y0
		ry = uy * x0 + vy * y0

		return (rx + orig[0], ry + orig[1])



	def insert(self, panel: Panel):

		self.dorsal_row = panel.dorsal_row
		self.area_m2 += panel.area_m2

		self.front = panel.front_corner
		self.side = panel.front_side

		if not self.panels:
			self.rot = Dorsal.local_rotation(panel.rot)
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


		self.panels = [panel] + self.panels
		if panel.rot == 1 or panel.rot == 3:
			self.flipped = True


class Line:

	def __init__(self, dorsals: list[Dorsal]):
		self.dorsals = dorsals
		self.flipped = False
		self.area_m2 = 0.
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
			ofs_red  = (offset, .0)
			front = dorsal.dorsal_to_local(ofs_red, dorsal.front)
			side = dorsal.dorsal_to_local(ofs_red, dorsal.side)
			_line.append(front)
			_line.append(side)

		return _line	

class Lines(list):

	def __init__(self):
		self.dorsals: list[Dorsal] = []
		self.panels: list[Panel] = []
		self.num_lines = 0
		self.pipe_length = 0.


	def get_dorsals(self, panels: list[Panel]):

		self.panels = panels
		if panels == []:
			return

		dorsal_row = 0
		dorsal = Dorsal()
		self.dorsals.append(dorsal)

		for panel in panels:

			if (panel.dorsal_row != dorsal_row or
			   dorsal.area_m2 + panel.area_m2 > Config.line_coverage_m2):
				dorsal = Dorsal()
			
				if (dorsal_row == panel.dorsal_row):
					dorsal.front_dorsal = False

				dorsal_row = panel.dorsal_row
				self.dorsals.append(dorsal)

			dorsal.insert(panel)


	def print_partition(self, partition):

		print(end="P")
		for lines in partition:
			print(end="[")
			for dorsal in lines:
				print(end=" (%d->%.2f) " % (dorsal.dorsal_row, dorsal.area_m2))
			print(end="]  ")
		print()


	def make_lines(self):

		for dorsals in self.best_partition:
			line = Line(dorsals)
			self.append(line)



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

			if area_m2 > Config.line_coverage_m2:
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

	

	def get_lines(self):

		if self.dorsals==[]:
			return

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

		self.print_partition(self.best_partition)
		print()
		self.make_lines()


