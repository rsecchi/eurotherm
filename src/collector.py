from functools import cached_property
from ezdxf.entities.lwpolyline import LWPolyline

from element import Element
from geometry import poly_t
from settings import Config


class Collector(Element):

	def __init__(self, poly:LWPolyline):
		Element.__init__(self, poly)
		# collector related variables
		self.number = 0
		self.zone_num = 0
		self.inputs = 0 
		self.name = ""

		self.flow = 0.
		self.box: poly_t = list()

		self.freespace = 0
		self.freeflow = 0.
		self.items = []


	@cached_property
	def guard_box(self) -> poly_t:
		# add margins to collector boundaries
		cmf = Config.collector_margin_factor

		cx, cy = self.pos
		points = list()
		poly = self.poly
		for p in poly:
			points.append((cx+cmf*(p[0]-cx), cy+cmf*(p[1]-cy)))
		points.append((cx+cmf*(poly[0][0]-cx), cy+cmf*(poly[0][1]-cy)))
		
		return points
