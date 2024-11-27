from collections import Counter
from math import ceil
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

	def pipe_bill(self):

		code = '2112200220'
		desc = 'TUBO MULTISTRATO 20X2 RIV.ROSSO'
		qnt = self.report.area * 0.7
		self.nav_item(qnt, code, desc)
		code = '2112200120'
		desc = 'TUBO MULTISTRATO 20X2 RIV.BLU'
		self.nav_item(qnt, code, desc)

		# code = '2720200120'
		# desc = 'LINEA AGG. PERT-AL-PERT + ANELLI E TERMIN. (2m)'
		# qnt = 0
		# for e in self.msp.query('*[layer=="%s"]' % Config.layer_panel):
		# 	if e.dxftype() == "LWPOLYLINE":
		# 		points = list(e.vertices())	
		# 		mdist = 0
		# 		for i in range(len(points)-1):
		# 			mdist = max(mdist, dist(points[i], points[i+1]))
		# 		mdist = int(np.round(mdist*scale/100))
		# 		qnt += mdist

		# qnt = ceil(qnt/2)
		# self.nav_item(qnt, code, desc)

		# linear joint
		# code = '6910022005'
		# desc = 'RACCORDO LEONARDO 20-20 (4pz)'
		# self.text_nav += nav_item(qnt2, code, desc)

		# rings
		# code = '6910022011'
		# desc = 'ANELLO PER RACC.LEONARDO IN PLASTICA D20 (8pz)'	
		# qnt1 = fittings['Rac_20_20_dritto']['count']
		# qnt2 = fittings['Rac_20_20_curva']['count']
		# qnt = 2*tot_cirs + 3*2*self.joints + 2*qnt1 + 2*qnt2
		# self.text_nav += nav_item(qnt, code, desc)

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


	def collectors_bill(self):

		tot_adpt = 0
		sizes = [int(clt["count"]) for clt in self.components.collectors]
		count = Counter(sizes)
		for size, qnt in count.items():
			tot_adpt += qnt*size
			code = '41200101%02d' % size
			desc = 'COLLETTORE SL 1" %02d+%02d COMPLETO' % (size,size)
			self.nav_item(qnt,code, desc)	
		
		# Adaptors
		code = '4810202001'
		desc = 'ADATTATORE'
		qnt = 2*tot_adpt
		self.nav_item(qnt,code, desc)


	def control_panel_bill(self):

		counters = self.components.panel_counters

		total = 0
		total_hydro = 0
		total_amb = 0
		for panel, quantity in counters.items():
			total += quantity
			if "Idro" in panel:
				total_hydro += quantity
			else:
				total_amb += quantity

		closures = 0
		if (self.model.ptype['handler']=='30'):
			code = '6113021002'
			desc = 'LEONARDO QUADRO DI CHIUSURA PLUS'
			qnt = ceil(0.25*(total))
			closures = total 
			self.nav_item(qnt, code, desc)
		else:
			code = '6110020103'
			desc = 'LEONARDO QUADRO CHIUSURA RACCORDI 420x260mm'
			qnt = total_amb
			self.nav_item(qnt, code, desc)

			code = '6112020201'
			desc = 'LEONARDO QUADRO CHIUSURA RACC.AMB.UMIDI 420x260mm'
			qnt = total_hydro
			self.nav_item(qnt, code, desc)
			closures = total_amb + total_hydro

		code = '6920042001'
		desc = 'COLLA PER QUADRI DI CHIUSURA'
		qnt = ceil(closures/4.35)
		self.nav_item(qnt, code, desc)



	def hatch_bill(self):

		## Hatch (botola)
		code = '6920012001'
		desc = 'BOTOLA'
		tot_clts = len(self.components.collectors)
		self.nav_item(tot_clts, code, desc)
		desc = 'MANOMETRO'
		self.nav_item(tot_clts, code, desc)
		code = '4710020306'
		desc = 'COPPIA VALVOLE SFERA SL SQ/DR.1"1/4 F - 1"F'
		self.nav_item(tot_clts, code, desc)
		code = '4713010301'
		desc = 'ISOLAZIONE VALVOLA SFERA SL (coppia)'
		self.nav_item(tot_clts, code, desc)
	

	def inhibit_bill(self):
		# corrosion inhibitor
		code = '3310020201'
		desc = 'e100 INIBITORE'
		if self.model.ptype['handler'] == '55':
			water = self.report.active_area*0.043*16.67 + self.report.area*0.41

		if self.model.ptype['handler'] == '35':
			water = self.report.active_area*0.043*23.34 + self.report.area*0.41
		
		if self.model.ptype['handler'] == '30':
			water = self.report.active_area*0.043*27.50 + self.report.area*0.41

		self.nav_item(ceil(water/100), code, desc)



	def probe_bill(self):
	
		code = '5150020202'
		desc = 'TESTINE ELETTROTERMICHE 2 FILI'
		qnt = self.components.num_lines
		self.nav_item(qnt, code, desc)
	
		code = '5140030101'
		desc = 'SMARTCOMFORT 365'
		qnt = self.components.smartcomforts
		self.nav_item(qnt, code, desc)

		code = '5140020401'
		desc = 'SMARTPOINT TEMPERATURA'
		qnt = self.components.num_probes_t
		self.nav_item(qnt, code, desc)

		code = '5140020402'
		desc = 'SMARTPOINT TEMPERATURA / UMIDITA\''
		qnt = self.components.num_probes_th
		self.nav_item(qnt, code, desc)

		code = '5140020201'
		desc = 'SMARTBASE PER LA GESTIONE DI TESTINE, POMPA E MISCELATRICE'
		qnt = self.components.smartbases
		self.nav_item(qnt, code, desc)


		code = '5140020403'
		desc = 'SMARTPOINT EXT SONDA ESTERNA'
		qnt = self.components.smartcomforts
		self.nav_item(qnt, code, desc)

		code = '5140020404'
		desc = 'SONDA DI MANDATA'
		qnt = self.components.smartcomforts 
		self.nav_item(qnt, code, desc)



	def make_bill(self):
	
		self.active_panel_bill()
		self.passive_panels_bill()
		self.make_fittings_bill()
		self.pipe_bill()
		self.collectors_bill()
		self.control_panel_bill()
		self.hatch_bill()
		self.inhibit_bill()

		## headers (testina)	
		if not self.model.control == "reg":
			code = '5150020201'
			desc = 'TESTINE ELETTROTERMICHE 4 FILI'
			qnt = self.components.num_lines
			self.nav_item(qnt, code, desc)

		if self.model.control == "reg":
			self.probe_bill()


		## If air conditioning
		#if not self.head == "none":
		#	compamat_R = 0
		#	compamat_TOP = 0
		#	compamat_SUPER = 0
		#	for zone in zones:
		#		if zone.flow < 1850:
		#			compamat_R += 1
		#		else:
		#			if zone.flow < 4000:
		#				compamat_TOP += 1
		#			else:
		#				compamat_SUPER +=1

		#	mtype = self.mtype[:-5]
		#	smartairs = 0
		#	if mtype=="dehum_int":
		#		smartairs = len(zones)

		#	if compamat_R > 0:
		#		code = '5330010101'
		#		desc = 'COMPAMAT R'
		#		qnt = compamat_R
		#		self.text_nav += nav_item(qnt, code, desc)

		#	if compamat_TOP > 0:
		#		code = '5330010201'
		#		desc = 'COMPAMAT TOP'
		#		qnt = compamat_TOP
		#		self.text_nav += nav_item(qnt, code, desc)

		#	if compamat_SUPER > 0:
		#		code = '5330010301'
		#		desc = 'COMPAMAT SUPER'
		#		qnt = compamat_SUPER
		#		self.text_nav += nav_item(qnt, code, desc)

		#	code = '5140020202'
		#	desc = 'SMARTAIR PER LA GESTIONE DELL\'UNITA\' ARIA E SERRANDE'
		#	qnt = smartairs
		#	self.text_nav += nav_item(qnt, code, desc)

		#	if self.control == "reg":
		#		code = '5140020301'
		#		desc = 'SET DI CONNETTORI SMARTBASE / SMARTAIR'
		#		qnt = smartbases + smartairs
		#		self.text_nav += nav_item(qnt, code, desc)

		#	# COMPAMAT accessories
		#	for k, cnd in enumerate(self.cnd):
		#		if (self.best_ac[k]>0):
		#			code = cnd['code']
		#			desc = cnd['model']
		#			qnt = self.best_ac[k]
		#			self.text_nav += nav_item(qnt, code, desc)
		#			accs = cnd['accessories'] 
		#			for acc in accs:
		#				if type(acc) == tuple:
		#					code = accessories[acc[0]]['code']
		#					desc = accessories[acc[0]]['desc']
		#					num = acc[1]
		#				else: 
		#					code = accessories[acc]['code']
		#					desc = accessories[acc]['desc']
		#					num = 1
							
		#				self.text_nav += nav_item(qnt*num, code, desc)
						

	def save(self):
		filename = self.model.outfile[:-3] + "dat"
		with open(filename, "w") as file:
			file.write(self.text)

