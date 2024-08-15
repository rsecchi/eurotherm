from planner import Panel
from settings import Config, dist, MAX_DIST

class Dorsal:
	def __init__(self):
		self.panels: list[Panel] = []
		self.front = (0., 0.)
		self.back = (0., 0.)
		self.area_m2 = 0.
		self.dorsal_row = 0
		self.front_dorsal = True


	def insert(self, panel: Panel):

		self.dorsal_row = panel.dorsal_row
		self.area_m2 += panel.area_m2

		if not self.panels:
			self.back = panel.rear_corner
		self.front = panel.front_corner

		self.panels = [panel] + self.panels


class Line:

	def __init__(self, dorsals: list[Dorsal]):
		self.dorsals = dorsals
		self.area_m2 = 0.
		for dorsal in dorsals:
			self.area_m2 += dorsal.area_m2
	
	def front_line_len(self):
		for dorsal in self.dorsals:
			print(dorsal.front)


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

		for lines in partition:
			print(end="[")
			for dorsal in lines:
				print(end=" (%.2f) " % dorsal.area_m2)
			print(end="]  ")
		print()


	def make_lines(self):
		for dorsals in self.best_partition:
			line = Line(dorsals)
			self.append(line)


	def partitions(self, l: list[Dorsal], level: int):

		yield [l]

		if level == self.num_lines:
			return

		n = len(l) - 1
		for i in range(2**n-2, -1, -1):

			first = [l[0]]
			others = []

			area_m2 = 0
			for j in range(n):
				if (i&(2**j)>0):
					first.append(l[j+1])
					area_m2 += l[j+1].area_m2
				else:
					others.append(l[j+1])

			if area_m2 > Config.line_coverage_m2:
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
			# self.print_partition(partition)
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


