from ezdxf.addons.importer import Importer 
from ezdxf.filemanagement import new, readfile
from ezdxf.lldxf import const
from model import Model, Room

from settings import Config
from settings import debug
from settings import leo_types 
from settings import panel_map


dxf_version = "AC1032"


class DxfDrawing:

	def __init__(self, model: Model):

		self.doc = new(dxf_version)
		self.doc.header["$LWDISPLAY"] = 1
		self.msp = self.doc.modelspace()
		self.create_layers()
		self.typology = dict()
		self.model = model

		self.blocks = {}


	def import_floorplan(self, filename):
		input_doc = readfile(filename)
		importer = Importer(input_doc, self.doc)

		floorplan = input_doc.query('*[layer=="%s"]' % Config.input_layer)

		importer.import_entities(floorplan)
		importer.finalize()


	def new_layer(self, layer_name, color):
		attr = {'linetype': 'CONTINUOUS', 'color': color}
		self.doc.layers.new(name=layer_name, dxfattribs=attr)


	def output_error(self):
		self.doc.layers.remove(Config.layer_panel)
		self.doc.layers.remove(Config.layer_link)
		if (debug):
			self.doc.layers.remove(Config.layer_box)
			self.doc.layers.remove(Config.layer_panelp)

		for room in self.model.processed:
			size = 2/room.frame.scale
			self.write_text("Locale %d" % 
				   room.pindex, room.pos, zoom=size)

		self.doc.saveas(self.model.outfile)


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


	def write_text(self, message, position, 
		align=const.MTEXT_MIDDLE_CENTER, zoom=1., col=Config.color_text):
		
		text = self.msp.add_mtext(message, 
			dxfattribs={"style": "Arial"})
		text.dxf.insert = position
		text.dxf.attachment_point = align
		text.dxf.char_height = (Config.font_size)*zoom
		text.dxf.layer = Config.layer_text
		text.dxf.color = col


	def draw_coord_system(self, room: Room):
		frame = room.frame
		scale = frame.scale
		orig = frame.rot_orig
		
		(ux, uy) = frame.vector
		(vx, vy) = (-uy, ux)
		p0 = (orig[0] + ux*scale, orig[1] + uy*scale)
		p1 = (orig[0] + vx*scale, orig[1] + vy*scale)
		xaxis = [orig, p0]
		yaxis = [orig, p1]
		pline = self.msp.add_lwpolyline(xaxis)
		pline.dxf.color = Config.color_collector
		self.msp.add_lwpolyline(yaxis)


	def draw_collector(self):

		scale = self.model.scale
		for collector in self.model.collectors:
			pos = collector.pos
			size = Config.collector_size/scale
			pos = (pos[0] - size/2, pos[1] - size/2) 
			block = self.msp.add_blockref(
				Config.block_collector,
				pos,
				dxfattribs={
					'xscale': 0.1/scale,
					'yscale': 0.1/scale,
					'rotation': 0 
				}
			)

			block.dxf.layer = Config.layer_panel
			self.write_text("%s" % collector.name, 
				   collector.pos, zoom=0.6/scale)


	def draw_room(self, room: Room):

		size = 2/room.frame.scale
		self.write_text("Locale %d" % room.pindex, room.pos, zoom=size)

	 
		if (room.color==Config.color_valid_room):
			block_names = self.blocks["classic"]
		else:
			block_names = self.blocks["hydro"]

		for panel in room.panels:
			panel.draw_panel(self.msp, room.frame)
			name = panel_map[panel.type]
			block_name = block_names[name]

			orig = room.frame.real_from_local(panel.pos)
			panel_rotation = panel.block_rotation(room)
			block = self.msp.add_blockref(
						block_name,
						orig,
						dxfattribs={
							'xscale': 0.1/room.frame.scale,
							'yscale': 0.1/room.frame.scale,
							'rotation': panel_rotation
						}
			)

			block.dxf.layer = Config.layer_panel



	def draw_model(self):
		for room in self.model.processed:
			# self.draw_coord_system(room)
			self.draw_room(room)
			self.draw_collector()

	def import_blocks(self, ptype):
		self.source_dxf = readfile(Config.symbol_file)
		importer = Importer(self.source_dxf, self.doc)
		self.typology = leo_types[ptype]

		self.blocks["classic"] = leo_types[ptype]["block_names_classic"]
		self.blocks["hydro"]  = leo_types[ptype]["block_names_hydro"]

		for block in self.blocks["classic"].values():
			importer.import_block(block)

		for block in self.blocks["hydro"].values():
			importer.import_block(block)

		# 	for fitting_name in fitting_names:
		# 		importer.import_block(fitting_name)

		importer.import_block(Config.block_collector)

		importer.finalize()

	def save(self):
		self.doc.saveas(self.model.outfile)
