from os import CLD_CONTINUED
from ezdxf.addons.importer import Importer 
from ezdxf.filemanagement import new, readfile
from ezdxf.lldxf import const
from engine.panels import panel_names

from lines import Dorsal
from model import Model, Room
from planner import Panel

from settings import Config
from settings import debug
from settings import leo_types 
from settings import leo_icons
from reference_frame import dist

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

	
	def draw_point(self, room, pos):
		frame = room.frame
		poly = frame.small_square(pos)
		self.msp.add_lwpolyline(poly)


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
		p0 = (orig[0] + 100*ux/scale, orig[1] + 100*uy/scale)
		p1 = (orig[0] + 100*vx/scale, orig[1] + 100*vy/scale)
		xaxis = [orig, p0]
		yaxis = [orig, p1]
		pline = self.msp.add_lwpolyline(xaxis)
		pline.dxf.layer = Config.layer_error
		poly = self.msp.add_lwpolyline(yaxis)
		poly.dxf.layer = Config.layer_error


	def draw_airlines(self, room: Room):

		poly = [room.collector.pos, room.pos]

		pline = self.msp.add_lwpolyline(poly)
		pline.dxf.layer = Config.layer_link



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


	def draw_panel(self, room: Room, panel: Panel):

		if (room.color==Config.color_valid_room):
			block_names = self.blocks["classic"]
		else:
			block_names = self.blocks["hydro"]

		name = block_names[panel_names[panel.type]]
		frame = room.frame
		pos = frame.real_from_local(panel.pos)
		rot = frame.block_rotation(panel.rot)

		block = self.msp.add_blockref(
					name,
					pos,
					dxfattribs={
						'xscale': 0.1/room.frame.scale,
						'yscale': 0.1/room.frame.scale,
						'rotation': rot
					}
		)
		block.dxf.layer = Config.layer_panel



	def draw_dorsal(self, room: Room, dorsal: Dorsal):
	
		if not dorsal.panels:
			return

		# Draw end caps
		name = leo_icons["cap"]
		frame = room.frame

		if dorsal.reversed:
			ofs_red  = (Config.indent_max, Config.offset_red)
			ofs_blue = (Config.indent_min, Config.offset_blue)
		else:
			ofs_red  = (Config.indent_min, Config.offset_red)
			ofs_blue = (Config.indent_max, Config.offset_blue)
		local_red = dorsal.dorsal_to_local(ofs_red, dorsal.back)
		local_blue = dorsal.dorsal_to_local(ofs_blue, dorsal.back)

		rot = dorsal.rot
		rot = frame.block_rotation(rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}

		pos = frame.real_from_local(local_red)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_link

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_link


		# Draw panel links
		name = leo_icons["link"]
		for i, _ in enumerate(dorsal.panels[1:]):
			a = dorsal.panels[i+1].front_corner
			b = dorsal.panels[i].rear_corner
			if dist(a,b) > 1:
				continue

			pos = dorsal.dorsal_to_local(ofs_red, a)
			pos = frame.real_from_local(pos)
			block = self.msp.add_blockref(name, pos, attribs)
			block.dxf.layer = Config.layer_link

			pos = dorsal.dorsal_to_local(ofs_blue, a)
			pos = frame.real_from_local(pos)
			block = self.msp.add_blockref(name, pos, attribs)
			block.dxf.layer = Config.layer_link


		# Draw dorsal heading fitting



	def draw_lines(self, room: Room):

		for line in room.lines:
			
			frontline = line.front_line()
			frontline = room.frame.real_coord(frontline)
			self.msp.add_lwpolyline(frontline)

			for dorsal in line.dorsals:
				self.draw_dorsal(room, dorsal)


			# # Corner fittings
			# rot = (rot_panel + 2) % 4
			# name = Config.block_fitting_corner
			# flip = (rot_panel==0 or rot_panel==2)
			# self.draw_block(room, name, pos, rot, flip, layer)
			# self.draw_point(room, pos)	

			# # T-shape fittings
			# for dorsal in line.dorsals[:-1]:
			# 	name = Config.block_fitting_tshape
			# 	pos = dorsal.front
			# 	if rot_panel==0 or rot_panel==2:
			# 		rot = (rot_panel - 1) % 4
			# 	else:
			# 		rot = (rot_panel + 1) % 4 

			# 	self.draw_block(room, name, pos, rot, False, layer)
			# 	self.draw_point(room, pos)	


	def draw_room(self, room: Room):

		size = 2/room.frame.scale
		self.write_text("Locale %d" % room.pindex, room.pos, zoom=size)

		for panel in room.panels:
			self.draw_panel(room, panel)

		# self.draw_dorsals(room)
		self.draw_lines(room)
		self.draw_airlines(room)


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
		importer.import_block(Config.block_fitting_corner)
		importer.import_block(Config.block_fitting_tshape)

		for _, block in leo_icons.items():
			importer.import_block(block)

		importer.finalize()


	def save(self):
		self.doc.saveas(self.model.outfile)
