from ezdxf.entities.lwpolyline import LWPolyline

from element import Element
from geometry import poly_t


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
