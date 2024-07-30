import openpyxl
import os, sys
from copy import deepcopy
from settings import Config
from model import Model
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Alignment, PatternFill

def set_border(ws, row, cols):

#	thin_border = Border(left=Side(style='thin'), 
#                   right=Side(style='thin'), 
#                   top=Side(style='thin'), 
#                   bottom=Side(style='thin'))

	cell_border = Border(top=Side(style='thin'))
	for col in cols:
		ws[col+row].border = cell_border

class XlsDocument:

	thin_left = Border(left=Side(style='thin'))
	thin_right = Border(right=Side(style='thin'))
	thin_left_top = Border(left=Side(style='thin'),
					top=Side(style='thin'))
	thin_right_top = Border(right=Side(style='thin'),
					top=Side(style='thin'))

	def __init__(self, data):
		self.data = data


	def save_in_xls(self, model: Model):

		xlsx_template = Config.xlsx_template_ita
		if self.data["lang"] == "eng":
			xlsx_template = Config.xlsx_template_eng

		wb = openpyxl.load_workbook(xlsx_template)
		ws1 = wb[Config.sheet_template_1]
		ws2 = wb[Config.sheet_template_2]
		ws3 = wb[Config.sheet_template_3]

		self.xls_headers(ws1, model)
		self.xls_headers(ws2, model)
		self.xls_headers(ws3, model)

		self.room_breakdown(ws1, model)
		self.room_breakdown(ws2, model)
		self.room_breakdown(ws3, model)

		out = self.data['cfg_dir']+'/'+self.data["outfile"][:-4]+".xlsx"		
		wb.save(out)

	def xls_headers(self, ws, model: Model):


		no_collectors = len(model.collectors)


		# copy total area
		ws['B14'] = str(model.area)
		ws['B18'] = str(model.area)

		# copy total coverage
		ws['A14'] = str(model.active_area)
		ws['A18'] = str(model.active_area)

		# copy total panels
		ws['D14'] = ws['D18'] = "0"
		ws['E14'] = ws['E18'] = "0"

		# copy number of feeds
		# ws1['F14'] = ws1['F18'] = self.feeds

		# copy number of collectors 
		ws['G14'] = ws['G18'] = str(no_collectors) 



	def room_breakdown(self, ws, model: Model):

		sheet_breakdown = Config.sheet_breakdown_ita
		if self.data["lang"] == "eng":
			sheet_breakdown = Config.sheet_breakdown_eng

		print(sheet_breakdown)
		for sheet, warm_coef, cool_coef in sheet_breakdown:

			ws['A22'] = str(sheet)
			ws.row_dimensions[3].height = 32

			# header
			for i in range(65,85):
				if (67<=i<=78):
					ws.column_dimensions[chr(i)].width = 10
				ws[chr(i)+'23'].alignment = \
					Alignment(wrapText=True, 
						vertical ='center',
						horizontal ='center')

			if self.data["lang"] == "ita":
				ws['A23'] = "Zona"
				ws['B23'] = "Collettore"
				ws['C23'] = "Stanza"

				ws['D23'] = "Attiva\n[m2]"
				ws['E23'] = "Area\n[m2]"
				ws['F23'] = "% cop."
				ws['G23'] = "linee"

				ws['H23'] = "Pannelli\n200x120"
				ws['I23'] = "Pannelli\n200x60"
				ws['J23'] = "Pannelli\n100x120"
				ws['K23'] = "Pannelli\n100x60"
					
				#ws.column_dimensions['M'].width = 2

				ws['L22'] = 'Riscaldamento'
				ws['L23'] = "Q, resa\n[W]"
				ws['M23'] = "Q, tot\n[W]"
				ws['N23'] = "Portata\n[kg/h]"

				#ws.column_dimensions['Q'].width = 2

				ws['O22'] = 'Raffrescamento'
				ws['O23'] = "Q, resa\n[W]"
				ws['P23'] = "Q, tot\n[W]"
				ws['Q23'] = "Portata\n[kg/h]"

				ws['A23'] = "Zona"
				ws['B23'] = "Collettore"
				ws['C23'] = "Stanza"

				ws['D23'] = "Attiva\n[m2]"
				ws['E23'] = "Area\n[m2]"
				ws['F23'] = "% cop."
				ws['G23'] = "linee"

				ws['H23'] = "Pannelli\n200x120"
				ws['I23'] = "Pannelli\n200x60"
				ws['J23'] = "Pannelli\n100x120"
				ws['K23'] = "Pannelli\n100x60"
					
				#ws.column_dimensions['M'].width = 2

				ws['L22'] = 'Riscaldamento'
				ws['L23'] = "Q, resa\n[W]"
				ws['M23'] = "Q, tot\n[W]"
				ws['N23'] = "Portata\n[kg/h]"

				#ws.column_dimensions['Q'].width = 2

				ws['O22'] = 'Raffrescamento'
				ws['O23'] = "Q, resa\n[W]"
				ws['P23'] = "Q, tot\n[W]"
				ws['Q23'] = "Portata\n[kg/h]"

			if self.data["lang"] == "eng":
				ws['A23'] = "Zone"
				ws['B23'] = "Collector"
				ws['C23'] = "Room"

				ws['D23'] = "Active\n[m2]"
				ws['E23'] = "Area\n[m2]"
				ws['F23'] = "% cov."
				ws['G23'] = "lines"

				ws['H23'] = "Panels\n200x120"
				ws['I23'] = "Panels\n200x60"
				ws['J23'] = "Panels\n100x120"
				ws['K23'] = "Panels\n100x60"
					
				#ws.column_dimensions['M'].width = 2

				ws['L22'] = 'Heating'
				ws['L23'] = "Q, yield\n[W]"
				ws['M23'] = "Q, tot\n[W]"
				ws['N23'] = "Flow\n[kg/h]"

				#ws.column_dimensions['Q'].width = 2

				ws['O22'] = 'Cooling'
				ws['O23'] = "Q, yield\n[W]"
				ws['P23'] = "Q, tot\n[W]"
				ws['Q23'] = "Flow\n[kg/h]"

				ws['A23'] = "Zone"
				ws['B23'] = "Collector"
				ws['C23'] = "Room"

				ws['D23'] = "Active\n[m2]"
				ws['E23'] = "Area\n[m2]"
				ws['F23'] = "% cov."
				ws['G23'] = "lines"

				ws['H23'] = "Panels\n200x120"
				ws['I23'] = "Panels\n200x60"
				ws['J23'] = "Panels\n100x120"
				ws['K23'] = "Panels\n100x60"
					
				#ws.column_dimensions['M'].width = 2

				ws['L22'] = 'Heating'
				ws['L23'] = "Q, yield\n[W]"
				ws['M23'] = "Q, tot\n[W]"
				ws['N23'] = "Flow\n[kg/h]"

				#ws.column_dimensions['Q'].width = 2

				ws['O22'] = 'Cooling'
				ws['O23'] = "Q, yield\n[W]"
				ws['P23'] = "Q, tot\n[W]"
				ws['Q23'] = "Flow\n[kg/h]"


			set_border(ws, '23', "ABCDEFGHIJKLMNOPQ")
			ws['A23'].border = XlsDocument.thin_left_top
			ws['B23'].border = XlsDocument.thin_left_top
			ws['G23'].border = XlsDocument.thin_left_top
			ws['L23'].border = XlsDocument.thin_left_top
			ws['O23'].border = XlsDocument.thin_left_top
			ws['Q23'].border = XlsDocument.thin_right_top

			model.processed.sort(key=lambda x: 
				(x.collector.zone_num, x.collector.number, x.pindex))

			zone = 0
			index = 24
			number = -1
			for room in model.processed:

				ws['A'+str(index)].border = XlsDocument.thin_left
				ws['B'+str(index)].border = XlsDocument.thin_left
				ws['G'+str(index)].border = XlsDocument.thin_left
				ws['L'+str(index)].border = XlsDocument.thin_left
				ws['O'+str(index)].border = XlsDocument.thin_left
				ws['Q'+str(index)].border = XlsDocument.thin_right

				# body
				for i in range(65,82):
					pos = chr(i)+str(index)
					ws[pos].alignment = \
						Alignment(wrapText=True, 
							vertical ='center',
							horizontal ='center')
					color = "D0D0D0"
					if (index%2==0 and i>65):
						color = "F0F0F0"
					ws[pos].fill = PatternFill(start_color=color, 
							fill_type = "solid")

				while (room.collector.zone_num>zone):
					zone += 1
					pos = 'A' + str(index)
					ws[pos] = "Zona %d" % zone
					set_border(ws,str(index), 'B')
				
				if (room.collector.number != number):
					number = room.collector.number
					set_border(ws, str(index), "ABCDEFGHIJKLMNOPQ")
					ws['A'+str(index)].border = XlsDocument.thin_left_top
					ws['B'+str(index)].border = XlsDocument.thin_left_top
					ws['G'+str(index)].border = XlsDocument.thin_left_top
					ws['L'+str(index)].border = XlsDocument.thin_left_top
					ws['O'+str(index)].border = XlsDocument.thin_left_top
					ws['Q'+str(index)].border = XlsDocument.thin_right_top


				pos = 'B' + str(index)
				ws[pos] = room.collector.name
				ws[pos].alignment = Alignment(horizontal='center')
				
				pos = 'C' + str(index)
				ws[pos] = room.pindex
				ws[pos].alignment = Alignment(horizontal='center')

				pos = 'E' + str(index)
				ws[pos] = room.area_m2()
				ws[pos].number_format = "0.0"

				if (room.active_m2==0):
					index += 1
					continue

				pos = 'D' + str(index)
				ws[pos] = room.active_m2
				ws[pos].number_format = "0.0"

				pos = 'F' + str(index)
				ws[pos] = room.ratio
				ws[pos].number_format = "0.0"

				pos = 'G' + str(index)
				ws[pos] = room.total_lines

				if (room.room_rep['panels_120x200']>0):
					pos = 'H' + str(index)
					ws[pos] = room.room_rep['panels_120x200']

				if (room.room_rep['panels_60x200']>0):
					pos = 'I' + str(index)
					ws[pos] = room.room_rep['panels_60x200']

				if (room.room_rep['panels_120x100']>0):
					pos = 'J' + str(index)
					ws[pos] = room.room_rep['panels_120x100']

				if (room.room_rep['panels_60x100']>0):
					pos = 'K' + str(index)
					ws[pos] = room.room_rep['panels_60x100']


				# heating 
				pos = 'L' + str(index)
				ws[pos] = radiated = room.active_m2 * warm_coef
				ws[pos].number_format = "0"

				pos = 'M' + str(index)
				ws[pos] = output = radiated * 1.1
				ws[pos].number_format = "0"

				pos = 'N' + str(index)
				ws[pos] = 3.6*output/(4.186*wsh['K14'].value)
				ws[pos].number_format = "0"

				# cooling
				pos = 'O' + str(index)
				ws[pos] = absorbed = room.active_m2 * cool_coef
				ws[pos].number_format = "0"

				pos = 'P' + str(index)
				ws[pos] = output = absorbed * 1.1
				ws[pos].number_format = "0"

				pos = 'Q' + str(index)
				ws[pos] = 3.6*output/(4.186*wsh['K18'].value)
				ws[pos].number_format = "0"


				#ws[pos_area].number_format = "0.00"
				index += 1

			set_border(ws, str(index), "ABCDEFGHIJKLMNOPQ")

