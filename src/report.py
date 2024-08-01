from components import Components
from settings import Config
from model import Room
import conf


class Report:

	def __init__(self, components: Components):
		self.components = components
		self.model = components.model
		data = self.model.data
		self.outfile = conf.spool + data['outfile'][:-4]+".txt"
		self.text = ""


	def set_text(self, text):
		self.text = text


	def save_report(self):
		f = open(self.outfile, "w")
		print(self.text, file = f)


	def room_report(self, room: Room):

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


	def make_report(self):

		model = self.model
		scale = model.scale

		self.area = 0 
		self.active_area = 0 

		self.feeds = 0
		self.normal_area = 0
		self.normal_active_area = 0
		self.normal_passive_area = 0
		self.bathroom_area = 0
		self.bathroom_active_area = 0
		self.bathroom_passive_area = 0


		txt = "\nRooms report\n"
		txt += "Room no.|area[m2]| % act. |200x120| 200x60|"
		txt += "   100x120  |    100x60\n"
		txt += "========+========+========+=======+=======+"
		txt += "============+==============\n"
		for room in model.processed:
			self.room_report(room)

			
		self.passive_area = self.area - self.active_area
		self.perimeter = 0
		for room in model.processed:
			self.perimeter += room.perimeter
			

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
		smtxt += "Total lines .............................. $$$\n" 
	

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

		smtxt += "\nPanel Count\n"
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


