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

		self.backup: list["Collector"] = [self] 
		self.overflow = False


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


	def reset(self, extra_feeds=0, extra_flow=0.):

		self.freespace = 0
		self.freeflow = 0.
		self.items = []
	
		if self != self.backup[0]:
			return

		for collector in self.backup:
			collector.freespace = Config.feeds_per_collector + extra_feeds 
			collector.freeflow = Config.flow_per_collector + extra_flow
			collector.items = []


