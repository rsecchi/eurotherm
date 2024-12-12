from pprint import pprint
from components import Components
from settings import Config
from model import Room
import conf
from page import Section


def print_line(a: int) -> str:
	if (a>0):
		txt = " %3d   |" % a
	else:
		txt = "       |" 
	return txt



class Report:

	def __init__(self, components: Components):

		self.area = 0 
		self.active_area = 0 

		self.feeds = 0
		self.normal_area = 0
		self.normal_active_area = 0
		self.normal_passive_area = 0
		self.bathroom_area = 0
		self.bathroom_active_area = 0
		self.bathroom_passive_area = 0

		self.components = components
		self.model = components.model
		data = self.model.data
		self.outfile = conf.spool + data['outfile'][:-4] + ".txt"
		self.text = ""
		self.perimeter = 0


	def set_text(self, text):
		self.text = text


	def output_section(self):

		if self.model.data['head'] == "none":
			return

		air_handlers = self.components.air_handlers

		lang = self.model.data['lang']
		section = Section(lang)
		section.header( 
				 {"ita": "Eurotherm consiglia:",
				  "eng": "Eurotherm recommends:"})


		for item in air_handlers:

			section.paragraph(
				{"ita": "Zona: %s" % item['zone'],
				 "eng": "Zone: %s" % item['zone']})

			for i, qnt in enumerate(item['best_ac']):

				if qnt == 0:
					continue

				label = item['air_handler'][i]['type_label']
				flow = int(air_handlers[i]['coverage'])	

				if item['air_handler'][i]['mount'] == 'V':
					mount = {"ita": "ad installazione verticale",
							 "eng": "vertical mounting"}
				else:
					mount = {"ita": "ad installazione orizzontale",
							 "eng": "horizontal mounting"}

				section.paragraph(
					{"ita": f" {label} {mount['ita']} " + 
								f"per una portata di {flow} m3/h",
					 "eng": f" {label} {mount['eng']} " +
								f"for a flow of {flow} m3/h"})


				mod = item['air_handler'][i]['model']
				section.paragraph( "%d x %s" % (qnt, mod))

				coverage = int(item['best_flow'])
				excess = int(item['best_flow'] - item['coverage'])

				section.paragraph(
				  {"ita": f"copertura {coverage} m3/h, eccesso {excess} m3/h",
				   "eng": f"coverage {coverage} m3/h, excess {excess} m3/h"})

		section.close()
		
		filesec = self.outfile[:-4] + ".rep"
		f = open(filesec, "w")
		print(section.text, file = f)


	def save_report(self):
		self.output_section()
		f = open(self.outfile, "w")
		print(self.text, file = f)


	def room_summary(self, room: Room):

		model = self.model
		scale = model.scale

		self.area += room.area_m2()
		self.active_area += room.active_m2

		if (room.color == Config.color_bathroom):
			self.bathroom_area += room.area_m2()
			self.bathroom_active_area += room.active_m2
			self.bathroom_passive_area += room.area_m2() - room.active_m2

			# grey areas are not included in passive
			grey_tot = 0
			for obs in room.obstacles:
				if obs.color == Config.color_neutral:
					grey_tot += obs.area * scale * scale
			self.bathroom_passive_area -= grey_tot

		else:
			self.normal_area += room.area_m2()
			self.normal_active_area += room.active_m2
			self.normal_passive_area += room.area_m2() - room.active_m2

			# grey areas are not included in passive
			grey_tot = 0
			for obs in room.obstacles:
				if obs.color == Config.color_neutral:
					grey_tot += obs.area * scale * scale
			self.normal_passive_area -= grey_tot

			
		# room.actual_feeds = ceil(rep['active_area']/area_per_feed_m2)
		# self.feeds += room.actual_feeds


	def model_summary(self):

		model = self.model
		scale = model.scale

		# Summary of all areas
		smtxt =  "\nTotal processed rooms .................... %3d\n" \
			% len(model.processed)
		smtxt += "Total collectors .......................... %2d\n" \
			% len(model.collectors)
		smtxt += "Total area ............................ %6.01f m2\n" \
			% self.area
		smtxt += "Total active area ..................... %6.01f m2 " \
			% self.active_area
		smtxt += " (%2d%%)" % (100*self.active_area/self.area)
		if self.active_area/self.area < Config.target_eff:
			smtxt += "@\n"
		else:
			smtxt += "\n"
		smtxt += "Total passive area .................... %6.01f m2\n" \
			% self.passive_area
		smtxt += "Normal area ........................... %6.01f m2\n" \
			% self.normal_area
		smtxt += "Normal active area .................... %6.01f m2\n" \
			% self.normal_active_area
		smtxt += "Normal passive area ................... %6.01f m2\n" \
			% self.normal_passive_area
		smtxt += "Hydro area ............................ %6.01f m2\n" \
			% self.bathroom_area
		smtxt += "Hydro active area ..................... %6.01f m2\n" \
			% self.bathroom_active_area
		smtxt += "Hydro passive area .................... %6.01f m2\n" \
			% self.bathroom_passive_area
		smtxt += "Total perimeter ....................... %6.01f m\n" \
			% (self.perimeter*scale/100)
		smtxt += "Total lines .............................. %3d\n" \
			% self.components.num_lines

		self.text += smtxt 


	def panel_requirements(self):

		# Calculating required panels 
		panel_record = self.components.panel_record
		full_classic    = panel_record["full_classic"]
		full_hydro      = panel_record["full_hydro"]
		lux_classic     = panel_record["lux_classic"]
		lux_hydro       = panel_record["lux_hydro"]
		split_classic   = panel_record["split_classic"]
		split_hydro     = panel_record["split_hydro"]
		half_classic    = panel_record["half_classic"]
		half_hydro      = panel_record["half_hydro"]
		quarter_classic = panel_record["quarter_classic"]
		quarter_hydro   = panel_record["quarter_hydro"]

		smtxt  = "\nPanel Count\n"
		smtxt += "Type    |200x120|  lux  | 200x60| 100x120| 100x60 \n"
		smtxt += "========+=======+=======+=======+========+========\n"	
		smtxt += "Classic |  %2d   | %2d    |  %2d   |   %2d   |  %2d \n"\
				% (full_classic, 
				   lux_classic, 
				   split_classic, 
				   half_classic,  
				   quarter_classic)
		smtxt += "Hydro   |  %2d   | %2d    |  %2d   |   %2d   |  %2d \n"\
				% (full_hydro, 
				   lux_hydro, 
				   split_hydro, 
				   half_hydro,  
				   quarter_hydro)

		self.text += smtxt


	def rooms_report(self):

		model = self.model

		txt = ""
		txt += "\nRooms report\n"
		txt += "Room no.|area[m2]| % act. |200x120|  lux  | 200x60|"
		txt += "100x120| 100x60\n"
		txt += "========+========+========+=======+=======+"
		txt += "=======+=======+========\n"

		for rm in model.processed:
			rec = rm.panel_record
			txt += "Room %3d|" % rm.pindex
			txt += "%7.02f | %5.01f%% |" % (rm.active_m2, 100*rm.ratio)
			txt += print_line(rec["full_hydro"]+rec["full_classic"])
			txt += print_line(rec["lux_hydro"]+rec["lux_classic"])
			txt += print_line(rec["split_hydro"]+rec["split_classic"])
			txt += print_line(rec["half_hydro"]+rec["half_classic"])
			txt += print_line(rec["quarter_hydro"]+rec["quarter_classic"])

			if rm.ratio < Config.target_eff:
				txt += " @" 
			txt += "\n"

		self.text += txt


	def make_report(self):

		model = self.model

		for room in model.processed:
			self.room_summary(room)
			
		self.passive_area = self.area - self.active_area
		for room in model.processed:
			self.perimeter += room.perimeter
			
		self.model_summary()
		self.panel_requirements()
		self.rooms_report()
	


