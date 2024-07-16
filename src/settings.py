
# defaults
default_input_layer = 'AREE LEONARDO'
default_symbol_file = 'Symbol.dxf'
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

debug = False

class Config:
	input_layer = default_input_layer
	symbol_file = default_symbol_file
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

	max_room_area = 500

