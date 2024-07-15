from ezdxf.addons.importer import Importer 
from ezdxf.filemanagement import new, readfile
from ezdxf.lldxf import const

from settings import Config
from settings import debug


# block names (defaults)
block_blue_120x100  = "LEO_55_120"
block_blue_60x100   = "LEO_55_60"
block_green_120x100 = "LEO_55_120_IDRO"
block_green_60x100  = "LEO_55_60_IDRO"
block_collector     = "collettore"
block_collector_W   = "collettore_W"


dxf_version = "AC1032"

class DxfDrawing:

	def __init__(self):

		self.doc = new(dxf_version)
		self.doc.header["$LWDISPLAY"] = 1
		self.msp = self.doc.modelspace()
		self.outname = ""
		self.create_layers()


	def import_floorplan(self, filename):
		input_doc = readfile(filename)
		importer = Importer(input_doc, self.doc)

		floorplan = input_doc.query('*[layer=="%s"]' % Config.input_layer)

		importer.import_entities(floorplan)
		importer.finalize()


	def new_layer(self, layer_name, color):
		attr = {'linetype': 'CONTINUOUS', 'color': color}
		self.doc.layers.new(name=layer_name, dxfattribs=attr)


	def output_error(self, processed):
		self.doc.layers.remove(Config.layer_panel)
		self.doc.layers.remove(Config.layer_link)
		if (debug):
			self.doc.layers.remove(Config.layer_box)
			self.doc.layers.remove(Config.layer_panelp)

		for room in processed:
			room.draw_label(self.msp)

		self.doc.saveas(self.outname)


	def create_layers(self):
		self.new_layer(Config.layer_panel, 0)
		if (debug):
			self.new_layer(Config.layer_panelp, 0)
			self.new_layer(Config.layer_box, Config.color_box)
		self.new_layer(Config.layer_link, 0)
		self.new_layer(Config.layer_text, Config.color_text)
		self.new_layer(Config.layer_error, 0)
		self.new_layer(Config.layer_lux, 0)
		self.new_layer(Config.layer_probes, 0)
		self.new_layer(Config.layer_joints, 0)
		self.new_layer(Config.layer_struct, 0)

		self.doc.layers.get(Config.layer_lux).off()
		self.doc.layers.get(Config.layer_struct).off()

	# def draw_label(self, msp):
	# 	write_text(msp, "Locale %d" % self.pindex, self.pos, zoom=2)

	def draw_room(self, room):
		for panel in room.panels:
			panel.draw_panel(self.msp, 100)

	def write_text(self, msp, strn, pos, 
		align=const.MTEXT_MIDDLE_CENTER, 
				zoom=1, col=Config.color_text):
		
		text = msp.add_mtext(strn, 
			dxfattribs={"style": "Arial"})
		text.dxf.insert = pos
		text.dxf.attachment_point = align
		text.dxf.char_height = Config.font_size*zoom
		text.dxf.layer = Config.layer_text
		text.dxf.color = col

	def draw_model(self, model):
		for room in model.processed:
			self.draw_room(room)


	# def import_blocks(self):
	# 	self.source_dxf = readfile(Config.symbol_file)
	# 	importer = Importer(self.source_dxf, self.doc)

	# 	ctype = self.type
		
	# 	for ptype in panel_types:
	# 		if (ctype == ptype['full_name']):
	# 			self.ptype = ptype
	# 			handler = "LEO_" + ptype['handler'] + "_"
	# 			block_blue_120x100 = handler + "120"
	# 			block_blue_60x100 = handler + "60"
	# 			block_green_120x100 = handler + "120_IDRO"
	# 			block_green_60x100 = handler + "60_IDRO"

	# 			if handler == "LEO_30_":
	# 				block_green_120x100 = block_blue_120x100
	# 				block_green_60x100 = block_blue_60x100

	# 			area_per_feed_m2 = ptype['panels'] * 2.4
	# 			flow_per_m2 = ptype['flow_panel'] / 2.4
	# 			print('Area/line = %g m2' % area_per_feed_m2)
	# 			print('Flow_per_m2 = %g l/m2' % flow_per_m2)

	# 	importer.import_block(block_blue_120x100)
	# 	importer.import_block(block_blue_60x100)
	# 	importer.import_block(block_green_120x100)
	# 	importer.import_block(block_green_60x100)
	# 	importer.import_block(block_collector)
	# 	importer.import_block(block_collector_W)
	# 	importer.import_block("LEO_LUX_120")
	# 	importer.import_block("LEO_LUX_120_IDRO")


	# 	for fitting_name in fitting_names:
	# 		importer.import_block(fitting_name)

	# 	importer.finalize()

	def save(self, filename):
		self.doc.saveas(filename)
