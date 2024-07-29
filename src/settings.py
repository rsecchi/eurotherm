
# defaults
default_input_layer = 'AREE LEONARDO'
default_font_size = 10

fitting_names = [
	"Rac_20_10_20_blu",
	"Rac_20_10_20_rosso",
	"Rac_20_10_blu",
	"Rac_20_10_rosso",
	"Rac_20_10_10_20_blu",
	"Rac_20_10_10_20_rosso",
	"Rac_20_10_10_blu",
	"Rac_20_10_10_rosso",
	"Rac_20_10_20_10_blu",
	"Rac_20_10_20_10_rosso",
	"Rac_10_20_10_blu",
	"Rac_10_20_10_rosso",
	"Rac_10_20_10_10_blu",
	"Rac_10_20_10_10_rosso",
	"Rac_20_10_10_20_10_10_blu",
	"Rac_20_10_10_20_10_10_rosso",
	"Rac_10_10_20_10_10_blu",
	"Rac_10_10_20_10_10_rosso",
	"Rac_20_20_dritto",
	"Rac_20_20_curva",
	"Rac_20_20_20_blu",
	"Rac_20_20_20_rosso",
	"Rac_10_10_dritto",
	"sonda T",
	"sonda T_U",
]

panel_map = ["full", "lux", "split", "half", "quarter"]


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
			"full"    : "LEONARDO 5,5 MS - 1200x2000x50mm",
			"lux"     : "LEONARDO 5,5 MS - 1200x2000x50mm",
			"split"   : "LEONARDO 5,5 MS - 1200x2000x50mm",
			"half"    : "LEONARDO 5,5 MS - 600x2000x50mm",
			"quarter" : "LEONARDO 5,5 MS - 600x2000x50mm",
		},

		"block_names_classic": {
			"full"    : "Pannello 55-1200x2000",
			"lux"     : "Pannello Lux 1200x2000",
			"split"   : "Pannello 55-600x2000",
			"half"    : "Mezzo pannello 55-1200x1000",
			"quarter" : "Mezzo pannello 55-600x1000",
		},

		"code_names_classic": {
			"full"    : "6113010431",
			"lux"     : "6113010432",
			"split"   : "6114010411",
			"half"    : "6114010412",
			"quarter" : "6114010412",
		},


		"panel_names_hydro": {
			"full"    : "LEONARDO 5,5 IDRO MS - 1200x2000x50mm",
			"lux"     : "LEONARDO 5,5 IDRO MS - 1200x2000x50mm",
			"split"   : "LEONARDO 5,5 IDRO MS - 1200x2000x50mm",
			"half"    : "LEONARDO 5,5 IDRO MS - 600x2000x50mm",
			"quarter" : "LEONARDO 5,5 IDRO MS - 600x2000x50mm",
		},

		"block_names_hydro": {
			"full"    : "Pannello Idro 55-1200x2000",
			"lux"     : "Pannello Lux Idro 1200x2000",
			"split"   : "Pannello 55-600x2000",
			"half"    : "Mezzo pannello Idro 55-1200x1000",
			"quarter" : "Mezzo pannello 55-600x1000",
		},


		"code_names_hydro": {
			"full"    : "6113010431",
			"lux"     : "6113010432",
			"split"   : "6114010411",
			"half"    : "6114010412",
			"quarter" : "6114010412",
		},

    },
}


debug = False

class Config:
	input_layer = default_input_layer
	symbol_file = '/usr/local/src/eurotherm/Symbol_CS.dxf'
	font_size = default_font_size

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

	color_text = 7
	color_collector = 1         ;# red
	color_obstacle = 2          ;# yellow
	color_bathroom = 3          ;# green
	color_valid_room = 5        ;# blue
	color_neutral = 8           ;# grey
	color_disabled_room = 6     ;# magenta
	color_zone = 4              ;# cyan
	color_box = 8               ;# grey

	block_collector     = "collettore"
	block_collector_W   = "collettore_W"

	max_room_area = 500
	collector_size = 60

