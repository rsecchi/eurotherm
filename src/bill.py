from components import Components
from settings import Config


class Bill:

	def __init__(self, components: Components):
		self.components = components
		self.model = components.model
		self.text = ""

	def nav_item(self, quantity: int | float, code: str, description: str):

		if quantity <= 0:
			return

		if (type(quantity)==int):
			self.text += '%d\r\n' % quantity
		else:
			self.text += ('%.1f\r\n' % quantity).replace(".", ",")
		
		self.text += code
		self.text += '      EURO\t'
		self.text += description + '\r\n'


	def make_bill(self):
	
		counters = self.components.panel_counters

		catalog = Config.panel_blocks_catalog()

		for panel, quantity in counters.items():
			code = catalog[panel]["code"]
			name = catalog[panel]["name"]
			self.nav_item(quantity, code, name)
		
		# Passive panels
		# code = '6111020101'
		# desc = 'LEONARDO PASSIVO 1200x2000x50mm'
		# qnt = 1.05*self.normal_passive_area
		# self.text_nav += nav_item(qnt, code, desc)
		# code = '6114020201'
		# desc = 'LEONARDO PASSIVO IDRO 1200x2000x50mm'
		# qnt = 1.05*self.bathroom_passive_area
		# self.text_nav += nav_item(qnt, code, desc)

	def save(self):
		filename = self.model.outfile[:-3] + "dat"
		with open(filename, "w") as file:
			file.write(self.text)

