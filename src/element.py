

from ezdxf.entities.lwpolyline import LWPolyline


class Element:
	def __init__(self, poly:LWPolyline):
		self.poly = poly
		self.points = list(poly.vertices())

