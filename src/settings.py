import os, json
from math import sqrt
import conf

MAX_DIST  = 1e20
MAX_COST  = 1000000

panel_sizes = {
	"full": 2.4,
	"lux": 2.4,
	"split": 1.2,
	"half": 1.2,
	"quarter": 0.6,
	"full_classic": 2.4,
	"full_hydro": 2.4,
	"lux_classic": 2.4,
	"lux_hydro": 2.4,
	"split_classic": 1.2,
	"split_hydro": 1.2,
	"half_classic": 1.2,
	"half_hydro": 1.2,
	"quarter_classic": 0.6,
	"quarter_hydro": 0.6,
}


leo_icons = {
	"collector": {
		"name": "collettore",
		"code": "???"
	},
	"collector_W": {
		"name": "collettore_W",
		"code": "???"
	},
	"probe_T": {
		"name": "sonda T",
		"code": "???"
	},
	"probe_TH": {
		"name": "sonda T_U",
		"code": "???"
	},
	"cap": {
		"name": "Tappo CS",
		"code": "6910022307",
		"desc": "CONF. TAPPO CHIUSURA FINE LINEA CLICK&SAFE",
	},
	"bend": {
		"name": "Gomito 20-CS",
		"code": "6910022306",
		"desc": "CONF. RACCORDO GOMITO 20-CLICK&SAFE",
		"rings": 1,
	},
	"nipple": {
		"name": "Nipples 20-CS",
		"code": "6910022304",
		"desc": "CONF. RACCORDO 20-CLICK&SAFE",
		"rings": 1,
	},
	"link": {
		"name": "Manicotto CS-CS",
		"code": "6910022302",
		"desc": "CONF. RACCORDO DRITTO CLICK&SAFE",
	},
	"tlink": {
		"name": "T 20-CS-20",
		"code": "6910022305",
		"desc": "CONF. RACCORDO T 20-CLICK&SAFE-20",
		"rings": 2,
	},
	"fit": {
		"name": "Nipples 20-20",
		"code": "6910022308",
		"desc": "CONF. RACCORDO 20-20",
		"rings": 2,
	},
	"bendfit": {
		"name": "Gomito 20-20",
		"code": "6910022309",
		"desc": "CONF. RACCORDO GOMITO 20-20",
		"rings": 2,
	},
	"tfit": {
		"name": "T 20-20-20",
		"code": "6910022310",
		"desc": "CONF. RACCORDO T 20-20-20",
		"rings": 3,
	}
}


leo_types = {
	"55": {
        "full_name"  : "Leonardo 5,5",
        "handler"    : "55",
        "rings"      : 10,
        "panels"     : 5,
        "flow_line"  : 280,
        "flow_ring"  : 28,
        "flow_panel" : 56,
		
		"panel_names_classic": {
			"full"    : "LEONARDO CS 5,5 - 1200x2000x60mm",
			"lux"     : "LEONARDO CS LUX - 1200x2000x60mm",
			"split"   : "LEONARDO CS 5,5 - 600x2000x60mm",
			"half"    : "LEONARDO CS 5,5 - 1200x1000x60mm",
			"quarter" : "LEONARDO CS 5,5 - 600x1000x60mm",
		},

		"block_names_classic": {
			"full"    : "Pannello 55-1200x2000",
			"lux"     : "Pannello Lux 1200x2000",
			"split"   : "Pannello 55-600x2000",
			"half"    : "Mezzo pannello 55-1200x1000",
			"quarter" : "Mezzo pannello 55-600x1000",
		},

		"code_names_classic": {
			"full"    : "6113121304",
			"lux"     : "6113120401",
			"split"   : "6113121303",
			"half"    : "6113121302",
			"quarter" : "6113121301",
		},


		"panel_names_hydro": {
			"full"    : "LEONARDO CS IDRO 5,5 - 1200x2000x60mm",
			"lux"     : "LEONARDO CS LUX IDRO - 1200x2000x60mm",
			"split"   : "LEONARDO CS IDRO 5,5 - 600x2000x60mm",
			"half"    : "LEONARDO CS IDRO 5,5 - 1200x1000x60mm",
			"quarter" : "LEONARDO CS IDRO 3,5 - 600x1000x60mm",
		},

		"block_names_hydro": {
			"full"    : "Pannello Idro 55-1200x2000",
			"lux"     : "Pannello Lux Idro 1200x2000",
			"split"   : "Pannello Idro 55-600x2000",
			"half"    : "Mezzo pannello Idro 55-1200x1000",
			"quarter" : "Mezzo pannello Idro 35-600x1000",
		},


		"code_names_hydro": {
			"full"    : "6114121302",
			"lux"     : "6114120401",
			"split"   : "6114110412",
			"half"    : "6114121301",
			"quarter" : "6114111301",
		},

    },

	"35": {

        "full_name"  : "Leonardo 3,5",
        "handler"    : "35",
        "rings"      : 9,
        "panels"     : 4.5,
        "flow_line"  : 252,
        "flow_ring"  : 28,
        "flow_panel" : 56,

		"panel_names_classic": {
			"full"    : "LEONARDO CS 3,5 - 1200x2000x60mm",
			"lux"     : "LEONARDO CS LUX - 1200x2000x60mm",
			"split"   : "LEONARDO CS 3,5 - 600x2000x60mm",
			"half"    : "LEONARDO CS 3,5 - 1200x1000x60mm",
			"quarter" : "LEONARDO CS 3,5 - 600x1000x60mm",
		},

		"block_names_classic": {
			"full"    : "Pannello 35-1200x2000",
			"lux"     : "Pannello Lux 1200x2000",
			"split"   : "Pannello 35-600x2000",
			"half"    : "Mezzo pannello 35-1200x1000",
			"quarter" : "Mezzo pannello 35-600x1000",
		},

		"code_names_classic": {
			"full"    : "6113111304",
			"lux"     : "6113120401",
			"split"   : "6113111303",
			"half"    : "6113111302",
			"quarter" : "6113111301",
		},


		"panel_names_hydro": {
			"full"    : "LEONARDO CS IDRO 3,5 - 1200x2000x60mm",
			"lux"     : "LEONARDO CS LUX IDRO - 1200x2000x60mm",
			"split"   : "LEONARDO CS IDRO 3,5 - 600x2000x60mm",
			"half"    : "LEONARDO CS IDRO 3,5 - 1200x1000x60mm",
			"quarter" : "LEONARDO CS IDRO 3,5 - 600x1000x60mm",
		},

		"block_names_hydro": {
			"full"    : "Pannello Idro 35-1200x2000",
			"lux"     : "Pannello Lux Idro 1200x2000",
			"split"   : "Pannello Idro 35-600x2000",
			"half"    : "Mezzo pannello Idro 35-1200x1000",
			"quarter" : "Mezzo pannello Idro 35-600x1000",
		},


		"code_names_hydro": {
			"full"    : "6114111304",
			"lux"     : "6114120401",
			"split"   : "6114111303",
			"half"    : "6114111302",
			"quarter" : "6114111301",
		},
	},

	"30": {
        "full_name"  : "Leonardo 3,0 plus",
        "handler"    : "30",
        "rings"      : 9,
        "panels"     : 4.5,
        "flow_line"  : 265,
        "flow_ring"  : 29.4,
        "flow_panel" : 58.9,

		"panel_names_classic": {
			"full"    : "LEONARDO CS 3,0 Plus - 1200x2000x60mm",
			"lux"     : "LEONARDO CS LUX - 1200x2000x60mm",
			"split"   : "LEONARDO CS 3,0 Plus - 600x2000x60mm",
			"half"    : "LEONARDO CS 3,0 Plus - 1200x1000x60mm",
			"quarter" : "LEONARDO CS 3,5 - 600x1000x60mm",
		},

		"block_names_classic": {
			"full"    : "Pannello 3Plus-1200x2000",
			"lux"     : "Pannello Lux 1200x2000",
			"split"   : "Pannello 3Plus-600x2000",
			"half"    : "Mezzo pannello 3Plus-1200x1000",
			"quarter" : "Mezzo pannello 35-600x1000",
		},

		"code_names_classic": {
			"full"    : "6113111004",
			"lux"     : "6113120401",
			"split"   : "6113111003",
			"half"    : "6113111002",
			"quarter" : "6113111301",
		},

		"panel_names_hydro": {
			"full"    : "LEONARDO CS IDRO 3,5 - 1200x2000x60mm",
			"lux"     : "LEONARDO CS LUX - 1200x2000x60mm",
			"split"   : "LEONARDO CS IDRO 3,5 - 600x2000x60mm",
			"half"    : "LEONARDO CS IDRO 3,5 - 1200x1000x60mm",
			"quarter" : "LEONARDO CS IDRO 3,5 - 600x1000x60mm",
		},

		"block_names_hydro": {
			"full"    : "Pannello Idro 35-1200x2000",
			"lux"     : "Pannello Lux Idro 1200x2000",
			"split"   : "Pannello Idro 35-600x2000",
			"half"    : "Mezzo pannello Idro 35-1200x1000",
			"quarter" : "Mezzo pannello Idro 35-600x1000",
		},

		"code_names_hydro": {
			"full"    : "6114111304",
			"lux"     : "6114120401",
			"split"   : "6114111303",
			"half"    : "6114111302",
			"quarter" : "6114111301",
		},
    },
}



air_handlers = [
	{
		"type": "dehum",
		"type_label": "Deumidificatore",
		"model": "DEUMIDIFICATORE 581 DC",
		"mount": "O",
		"width_mm": [756],
		"height_mm": [260],
		"depth_mm": [803],
		"flow_m3h": 300,
		"code": "7110010301",
		"accessories": {"sifone", "plenum"}
	},
	{
		"type": "dehum",
		"type_label": "Deumidificatore",
		"model": "DEUMIDIFICATORE 901 DC",
		"mount": "O",
		"width_mm": [706],
		"height_mm": [309],
		"depth_mm": [936],
		"flow_m3h": 580,
		"code": "7110010601",
		"accessories": {"sifone"}
	},
	{
		"type": "dehum",
		"type_label": "Deumidificatore",
		"model": "DEUMIDIFICATORE 320 DI (incasso)",
		"mount": "V",
		"width_mm": [402],
		"height_mm": [637],
		"depth_mm": [203],
		"flow_m3h": 200,
		"code": "7110020101",
		"accessories": {"sifone", "telaio1", "griglia1"}
	},
	{
		"type": "dehum",
		"type_label": "Deumidificatore",
		"model": "DEUMIDIFICATORE 581 DI (incasso)",
		"mount": "V",
		"width_mm": [732],
		"height_mm": [732],
		"depth_mm": [203],
		"flow_m3h": 300,
		"code": "7110020101",
		"accessories": {"sifone", "telaio2", "griglia2"}
	},
	{
		"type": "dehum_int",
		"type_label": "Deuclimatizzatore",
		"model": "DEU-CLIMATIZZATORE 582 DCC",
		"mount": "O",
		"width_mm": [756],
		"depth_mm": [260],
		"height_mm": [803],
		"flow_m3h": 300,
		"code": "7210020701",
		"accessories": {"sifone", "plenum"}
	},
	{
		"type": "dehum_int",
		"type_label": "Deuclimatizzatore",
		"model": "DEU-CLIMATIZZATORE 901 DCC",
		"mount": "O",
		"width_mm": [706],
		"height_mm": [309],
		"depth_mm": [936],
		"flow_m3h": 580,
		"code": "7210010602",
		"accessories": {"sifone"}
	},
	{
		"type": "dehum_int",
		"type_label": "Deuclimatizzatore",
		"model": "DEU-CLIMATIZZATORE 581 DCI (incasso)",
		"mount": "V",
		"width_mm": [732],
		"height_mm": [732],
		"depth_mm": [203],
		"flow_m3h": 300,
		"code": "7210020301",
		"accessories": {"sifone", "telaio2", "griglia2"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEUCLIMA-VMC 300S",
		"mount": "O",
		"width_mm": [1204.4],
		"height_mm": [979.5],
		"depth_mm": [244],
		"flow_m3h": 300,
		"code": "7410010103",
		"accessories": {("sifone",2), "filtro"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEUCLIMA-VMC 500S",
		"mount": "O",
		"width_mm": [1254.4],
		"height_mm": [810.5],
		"depth_mm": [294],
		"flow_m3h": 500,
		"code": "7410010105",
		"accessories": {("sifone",2), "filtro"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEUCLIMA-VMC 300V",
		"mount": "V",
		"width_mm": [1391.7],
		"height_mm": [700],
		"depth_mm": [342.3],
		"flow_m3h": 300,
		"code": "7510010101",
		"accessories": {"sifone", "filtro"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEUCLIMA-VMC 500V",
		"mount": "V",
		"width_mm": [1696.7],
		"height_mm": [700],
		"depth_mm": [421],
		"flow_m3h": 500,
		"code": "7510010102",
		"accessories": {"sifone", "filtro"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEU-CLIMATIZZATORE DCR 1000",
		"mount": "O",
		"width_mm": [805,1097],
		"height_mm": [691,723],
		"depth_mm": [350.5,350.5],
		"flow_m3h": 1000,
		"code": "7110011001",
		"accessories": {("sifone",2), "dcr1000"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEU-CLIMATIZZATORE DCR 2000",
		"mount": "O",
		"width_mm": [950.5,1097],
		"height_mm": [691,723],
		"depth_mm": [350.5,350.5],
		"flow_m3h": 2000,
		"code": "7110011002",
		"accessories": {("sifone", 2), "dcr2000"}
	},
	{
		"type": "dehum_int_ren",
		"type_label": "Deuclima VMC",
		"model": "DEUCLIMA-VMC 300SY",
		"mount": "O",
		"width_mm": [1070],
		"height_mm": [880],
		"depth_mm": [251],
		"flow_m3h": 300,
		"code": "7410010104",
		"accessories": {"sifone"}
	},
]


accessories = {
	"sifone": {
		"code": "7910080907",
		"desc": "Sifone"
	},
	"plenum": {
		"code": "7510030203",
		"desc": "Plenum di mandata 2/3xD160"
	},
	"telaio1": {
		"code": "7910010201",
		"desc": "Telaio da murare"
	},
	"griglia1": {
		"code": "7910010101",
		"desc": "Griglia in legno laccato"
	},
	"telaio2": {
		"code": "7910030201",
		"desc": "Telaio da murare"
	},
	"griglia2": {
		"code": "7910030101",
		"desc": "Griglia in legno laccato"
	},
	"filtro": {
		"code": "7910080980",
		"desc": "Box filtro con lampada UV e silenziatore"	
	},
	"dcr1000": {
		"code": "7910090901",
		"desc": "Silenziatore DCR1000"
	},
	"dcr2000": {
		"code": "7910090902",
		"desc": "Silenziatore DCR2000"
	},
}




def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)


debug = False

class Config:

	tolerance = 1.
	collector_size = 60.
	collector_margin_factor = 1.5
	flow_per_collector = 1700.
	feeds_per_collector = 13

	min_dist = 20.
	min_dist2 = min_dist*min_dist
	wall_depth = 101.
	max_clt_distance = 3000.

	input_layer = 'AREE LEONARDO'
	symbol_file = '/usr/local/src/eurotherm/Symbol_CS.dxf'
	font_size = 10.
	line_coverage_m2 = 12.001 
	boxzone_padding = 10.

	layer_text      = 'Eurotherm_text'
	layer_box       = 'Eurotherm_box'
	layer_panel     = 'Pannelli Leonardo'
	layer_panelp    = 'Eurotherm_prof'
	layer_link      = 'Eurotherm_link'
	layer_error     = 'Eurotherm_error'
	layer_lux       = 'Eurotherm_lux'
	layer_probes    = 'Eurotherm_probes'
	layer_struct    = 'Eurotherm_structure'
	layer_collector = 'Collettori'
	layer_fittings  = 'Raccorderia'

	color_text = 7
	color_collector = 1         ;# red
	color_obstacle = 2          ;# yellow
	color_bathroom = 3          ;# green
	color_valid_room = 5        ;# blue
	color_neutral = 8           ;# grey
	color_disabled_room = 6     ;# magenta
	color_zone = 4              ;# cyan
	color_box = 8               ;# grey
	color_tracks = 30           ;# orange
	color_panel_contour = 9     ;# light grey

	error_shade = "orange"

	max_room_area = 500
	target_eff = 0.7
	
	xlsx_template_ita = 'leo_template.xlsx'
	xlsx_template_eng = 'leo_template_eng.xlsx'

	sheet_templates_ita = [
		('LEONARDO 5.5', 'Dettaglio Stanze L55', 85.0, 51.8),
		('LEONARDO 3.5', 'Dettaglio Stanze L35', 84.2, 64.8),
		('LEONARDO 3.0 PLUS', 'Dettaglio Stanze 30p', 82.3, 80.9)
	]	

	sheet_templates_eng = [
		('LEONARDO 5.5','Room Breakdown L55', 85.0, 51.8),
		('LEONARDO 3.5','Room Breakdown L35', 84.2, 64.8),
		('LEONARDO 3.0 PLUS','Room Breakdown 30p', 82.3, 80.9)
	]	

	# sheet_breakdown_ita = [
	# 	('Dettaglio Stanze L55', 85.0, 51.8), 
	# 	('Dettaglio Stanze L35', 84.2, 64.8),
	# 	('Dettaglio Stanze 30p', 82.3, 80.9)
	# ]

	# sheet_breakdown_eng = [
	# 	('Room Breakdown L55', 85.0, 51.8), 
	# 	('Room Breakdown L35', 84.2, 64.8),
	# 	('Room Breakdown 30p', 82.3, 80.9)
	# ]


	offset_red = 4.15
	offset_blue = 16.12567
	indent_red = -2.0409
	indent_blue = 1.95951
	
	indent_cap_red_right = 0.95951
	indent_cap_blue_right = 4.95951
	indent_cap_red_left = 5.04049
	indent_cap_blue_left = 1.04049

	# # deprecated
	# indent_bend_red_left = 7.48974
	# indent_bend_blue_left = 3.48974
	# indent_bend_red_right = 3.40875
	# indent_bend_blue_right = 7.40875

	attach_red_left = 7.48974
	attach_blue_left = 3.48974
	attach_red_right = 3.40875
	attach_blue_right = 7.40875

	lux_hole_width = 147
	lux_hole_height = 24

	supply_out = 9.18099
	supply_in  = 5.18099
	color_supply_red = 11 
	color_supply_blue = 171
	supply_thick_mm = 2
	
	cos_beam_angle = 0.7071 
	leeway = 28
	inter_track = 50
	extra_track = 60
	track_thick_mm = 5

	search_step = 5
	size_smartp_icon = 10

	min_area_probe_th_m2 = 9.0
	step_retract = 5.0
	arc_step_deg = 2.0

	_handlers = dict() 

	@classmethod
	def panel_handlers(cls):
		if cls._handlers:
			return cls._handlers

		for typ in leo_types:

			for key, name in leo_types[typ]["block_names_classic"].items():
				cls._handlers[name] = key + "_classic"

			for key, name in leo_types[typ]["block_names_hydro"].items():
				cls._handlers[name] = key + "_hydro"

		return cls._handlers


	@classmethod
	def panel_catalog(cls):

		catalog = dict()

		for panels in leo_types.values():

			block_names = panels['block_names_classic']
			for key, block_name in block_names.items():
				panel_name = panels['panel_names_classic'][key]
				code_name  = panels['code_names_classic'][key]

				if not block_name in catalog.keys():
					catalog[block_name] = {
							"name": panel_name,
							"code": code_name,
							"type": key,
							"area": panel_sizes[key]}

			block_names = panels['block_names_hydro']
			for key, block_name in block_names.items():
				panel_name = panels['panel_names_hydro'][key]
				code_name  = panels['code_names_hydro'][key]

				if not block_name in catalog.keys():
					catalog[block_name] = {
							"name": panel_name,
							"code": code_name, 
							"type": key,
							"area": panel_sizes[key]}

		return catalog


	@classmethod
	def icon_catalog(cls) -> dict:

		leo_catalog = dict()

		for _ , value in leo_icons.items():
			leo_catalog[value["name"]] = value

		return leo_catalog


	@classmethod
	def _init_config(cls):

		if not os.path.exists(conf.settings_file):
			return

		with open(conf.settings_file, 'r') as f:
			data = json.loads(f.read())
			for key, value in data.items():
				parts = key.split("_")
				if len(parts) <= 1:
					continue
				
				var_type = parts[-1]
				var_name = "_".join(parts[:-1])
				if var_type == "int":
					value = int(value)
				elif var_type == "float":
					value = float(value)
				
				setattr(cls, var_name, value)


Config._init_config()
