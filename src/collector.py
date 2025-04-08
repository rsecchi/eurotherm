from ezdxf.entities.lwpolyline import LWPolyline

from element import Element


class Collector(Element):
	def __init__(self, poly:LWPolyline):
		self.poly = poly
		self.points = list(poly.vertices())

