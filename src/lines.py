from planner import Panel
from settings import Config

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
	def __init__(self):
		self.dorsals: list[Dorsal] = list()
		self.area_m2 = 0.



class Lines:
	def __init__(self):
		self.dorsals: list[Dorsal] = []
		self.panels: list[Panel] = []


	def get_dorsals(self, panels: list[Panel]):

		self.panels = panels

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
