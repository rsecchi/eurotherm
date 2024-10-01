from report import Report
from settings import Config


class Bill:

	def __init__(self, report: Report):
		self.report = report
		self.components = self.report.components
		self.model = self.components.model
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

	def passive_panels_bill(self):
		# Passive panels
		code = '6111020101'
		desc = 'LEONARDO PASSIVO 1200x2000x50mm'
		qnt = 1.05*self.report.normal_passive_area
		self.nav_item(qnt, code, desc)
		code = '6114020201'
		desc = 'LEONARDO PASSIVO IDRO 1200x2000x50mm'
		qnt = 1.05*self.report.bathroom_passive_area
		self.nav_item(qnt, code, desc)


	def active_panel_bill(self):
		counters = self.components.panel_counters

		catalog = Config.panel_catalog()

		for panel, quantity in counters.items():
			qnt = catalog[panel]["area"]*quantity
			code = catalog[panel]["code"]
			name = catalog[panel]["name"]
			self.nav_item(qnt, code, name)


	def make_fittings_bill(self):

		catalog = Config.icon_catalog()

		for name, quantity in self.components.fittings.items():
			code = catalog[name]["code"]
			self.nav_item(quantity, code, name)

		
	def make_bill(self):
	
		self.active_panel_bill()
		self.passive_panels_bill()
		self.make_fittings_bill()

	def save(self):
		filename = self.model.outfile[:-3] + "dat"
		with open(filename, "w") as file:
			file.write(self.text)
		print(self.text)

