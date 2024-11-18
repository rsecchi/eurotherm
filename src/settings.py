from math import sqrt

MAX_DIST  = 1e20

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
		"code": "6910022300"
	},
	"bend": {
		"name": "Gomito 20-CS",
		"code": "6910022306"
	},
	"nipple": {
		"name": "Nipples 20-CS",
		"code": "6910022304"
	},
	"link": {
		"name": "Manicotto CS-CS",
		"code": "6910022302"
	},
	"tlink": {
		"name": "T 20-CS-20",
		"code": "6910022305"
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
			"half"    : "LEONARDO CS 5,5 - 1200x2000x60mm",
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
			"quarter" : "6113131301",
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


def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)


debug = False

class Config:
	input_layer = 'AREE LEONARDO'
	symbol_file = '/usr/local/src/eurotherm/Symbol_CS.dxf'
	font_size = 10 
	line_coverage_m2 = 12.001 
	min_dist = 10

	layer_text      = 'Eurotherm_text'
	layer_box       = 'Eurotherm_box'
	layer_panel     = 'Pannelli Leonardo'
	layer_panelp    = 'Eurotherm_prof'
	layer_link      = 'Eurotherm_link'
	layer_error     = 'Eurotherm_error'
	layer_lux       = 'Eurotherm_lux'
	layer_probes    = 'Eurotherm_probes'
	layer_joints    = 'Eurotherm_joints'
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

	max_room_area = 500
	collector_size = 60
	target_eff = 0.7
	
	xlsx_template_ita = 'leo_template.xlsx'
	xlsx_template_eng = 'leo_template_eng.xlsx'
	sheet_template_1 = 'LEONARDO 5.5'
	sheet_template_2 = 'LEONARDO 3.5'
	sheet_template_3 = 'LEONARDO 3.0 PLUS'

	sheet_breakdown_ita = [
		('Dettaglio Stanze L55', 85.0, 51.8), 
		('Dettaglio Stanze L35', 84.2, 64.8),
		('Dettaglio Stanze 30p', 82.3, 80.9)
	]

	sheet_breakdown_eng = [
		('Room Breakdown L55', 85.0, 51.8), 
		('Room Breakdown L35', 84.2, 64.8),
		('Room Breakdown 30p', 82.3, 80.9)
	]


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

	lux_hole_width = 145
	lux_hole_height = 18	

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
