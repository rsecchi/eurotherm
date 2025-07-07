from math import  pi, cos, sin
from types import SimpleNamespace
from ezdxf.addons.importer import Importer 
from ezdxf.entities.insert import Insert
from ezdxf.filemanagement import new, readfile
from ezdxf.lldxf import const
from collector import Collector
from element import Element
from engine.panels import panel_names, panel_map

from lines import Dorsal, Line 
from model import Model, Room
from planner import Panel

from settings import Config
from settings import debug
from settings import leo_types 
from settings import leo_icons
from geometry import point_t
from reference_frame import adv, diff, dist, mul, versor

dxf_version = "AC1032"
from geometry import Picture, extend_pipes, norm, trim_segment_by_poly, xprod
from geometry import poly_t


MAX_DIST  = 1e20



def panel_tracks(panel: Insert, u: point_t, scale: float) -> list[float]:

	uscale = (u[0]/scale, u[1]/scale)
	attribs = panel.dxfattribs()
	angle = attribs['rotation']
	name = attribs['name']
	ptype = Config.panel_catalog()[name]['type']
	x, y, _ = attribs['insert']
	tracks = panel_map[ptype]['tracks']

	ux, uy = cos(pi*angle/180), sin(pi*angle/180)

	base = x*u[0] + y*u[1]

	step = Config.inter_track*uscale[0], Config.inter_track*uscale[1]
	coords: list[float] = []
	for i in range(tracks):
		point = base - i*step[0]*ux - i*step[1]*uy
		coords.append(point)

	return coords



class Preview:

	def __init__(self, model: Model):
		self.model = model
		self.picture = Picture()


	def draw_model(self):

		for room in self.model.processed:
			if room.error:
				self.picture.add_shaded_area(room.points, 
					color=Config.error_shade)

		col = "black"
		for room in self.model.processed:

			for obs in room.obstacles:
				if obs.color == Config.color_obstacle:
					col = "yellow"
				if obs.color == Config.color_neutral:
					col = "silver"
				if obs.color == Config.color_panel_contour:
					if room.color == Config.color_valid_room:
						col = "lightblue"
					else:
						col = "lightgreen"

				self.picture.add(obs.points, color=col)

			if room.color == Config.color_valid_room:
				col = "blue"
			
			if room.color == Config.color_bathroom:
				col = "green"

			if room.color == Config.color_disabled_room:
				col = "magenta"

			self.picture.text(room.pos, "%d" % room.pindex, color=col)	
			self.picture.add(room.points, color=col)

		for collector in self.model.collectors:
			px, py = collector.pos
			offs = Config.collector_size/2/self.model.scale
			collector_shape = [(px-offs, py-offs), 
							  (px+offs, py-offs),
							  (px+offs, py+offs),
							  (px-offs, py+offs),
							  (px-offs, py-offs)]
					
			self.picture.add(collector_shape, color="red")

		self.picture.set_frame()


	def save(self):
		self.picture.draw(self.model.outfile[:-4]+".png")


class DxfDrawing:

	def __init__(self, model: Model):

		self.doc = new(dxf_version)
		# self.doc.header["$LWDISPLAY"] = 1
		self.msp = self.doc.modelspace()
		self.create_layers()
		self.typology = dict()
		self.model = model

		self.blocks = {}


	def add_attrib(self, insert: Insert, tag: str, value: str):
		insert.add_attrib(
				tag=tag,
				text=value,
				insert=insert.dxf.insert,
				dxfattribs={
					'height': Config.tag_height_cm/self.model.scale,
				})

	def import_layer(self, filename:str, layer_name:str):
		input_doc = readfile(filename)
		importer = Importer(input_doc, self.doc)

		if layer_name == Config.layer_fittings:
			floorplan = input_doc.query('INSERT[layer=="%s"]' % layer_name)
		else:
			floorplan = input_doc.query('*[layer=="%s"]' % layer_name)

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
			self.write_text("Locale %d" % 
				   room.pindex, room.pos, zoom=2.0)

			if room.error:
				hatch = self.msp.add_hatch(color=41)
				hatch.set_pattern_fill("ANSI31", scale=2/self.model.scale)
				hatch.paths.add_polyline_path(room.points, 
					is_closed=True,
					flags=const.BOUNDARY_PATH_EXTERNAL)
				hatch.dxf.layer = Config.layer_error

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
		self.new_layer(Config.layer_struct, Config.color_tracks)

		self.doc.layers.get(Config.layer_lux).off()
		self.doc.layers.get(Config.layer_struct).off()


	def write_text(self, message:str, position: tuple[float, float],
				align: int=const.MTEXT_MIDDLE_CENTER, 
		zoom=1., col=Config.color_text,
		layer=Config.layer_text):
		
		text = self.msp.add_mtext(message, 
			dxfattribs={"style": "Arial"})
		text.dxf.insert = position
		text.dxf.attachment_point = align
		text.dxf.char_height = Config.font_size*zoom/self.model.scale
		text.dxf.layer = layer
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


	def draw_zones(self):

		scale = self.model.scale

		# Box zones
		for clt in self.model.collectors:
			if (not clt.is_leader):
				continue

			# Box zones
			if not clt.user_zone:
				margin = 2*Config.boxzone_padding/scale
				ax = min([c.ax for c in clt.zone_rooms]) - margin
				ay = min([c.ay for c in clt.zone_rooms]) - margin
				bx = max([c.bx for c in clt.zone_rooms]) + margin
				by = max([c.by for c in clt.zone_rooms]) + margin
			
				pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
				pl = self.msp.add_lwpolyline(pline)
				pl.dxf.layer = Config.layer_text
				pl.dxf.color = Config.color_zone
				pl.dxf.linetype = 'CONTINUOUS'
			else:
				ax = -MAX_DIST
				by = -MAX_DIST

				for p in clt.user_zone.poly:
					if p[1] > by or (p[1] == by and p[0] < ax):
						ax = p[0]; by = p[1]

			self.write_text("Zone %d" % clt.zone_num, 
			  (ax, by + Config.boxzone_padding/scale), 
				const.MTEXT_BOTTOM_LEFT, zoom=0.6)


			# if not clt.user_zone:
			# 	self.zone_bb.append([ax,ay,bx,by])


	def draw_airlines(self, room: Room):

		if not isinstance(room.collector, Room):
			return

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
				leo_icons["collector"]["name"],
				pos,
				dxfattribs={
					'xscale': 0.1/scale,
					'yscale': 0.1/scale,
					'rotation': 0 
				}
			)

			block.dxf.layer = Config.layer_collector
			self.write_text("%s" % collector.name, 
				   collector.pos, zoom=0.6, 
				   layer=Config.layer_collector)


	def draw_panel(self, room: Room, panel: Panel, ref: str):

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
		self.add_attrib(block, 'collector', ref)



	def draw_end_caps(self, room: Room, dorsal: Dorsal, ref: str):

		name = leo_icons["cap"]["name"]
		frame = room.frame

		if dorsal.reversed:
			ofs_red  = (Config.indent_cap_red_left, Config.offset_red)
			ofs_blue = (Config.indent_cap_blue_left, Config.offset_blue)
		else:
			ofs_red  = (Config.indent_cap_red_right, Config.offset_red)
			ofs_blue = (Config.indent_cap_blue_right, Config.offset_blue)
		local_red = dorsal.dorsal_to_local(ofs_red, dorsal.back)
		local_blue = dorsal.dorsal_to_local(ofs_blue, dorsal.back)


		rot = dorsal.rot
		if dorsal.water_from_left:
			rot = (rot+2)%4
		rot = frame.block_rotation(rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}

		pos = frame.real_from_local(local_red)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)


	def draw_panel_links(self, room: Room, dorsal: Dorsal, ref: str):

		frame = room.frame
		rot = (dorsal.rot + 2) % 4
		rot = frame.block_rotation(rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}

		if dorsal.reversed:
			ofs_red  = (-Config.indent_red, Config.offset_red)
			ofs_blue = (-Config.indent_blue, Config.offset_blue)
		else:
			ofs_red  = (Config.indent_red, Config.offset_red)
			ofs_blue = (Config.indent_blue, Config.offset_blue)
		
		name = leo_icons["link"]["name"]
		for i, _ in enumerate(dorsal.panels[1:]):
			a = dorsal.panels[i+1].front_corner
			b = dorsal.panels[i].rear_corner

			if dist(a,b) > 1:
				self.draw_gap(room, dorsal, a, b)

				pos = dorsal.dorsal_to_local(ofs_red, b)
				pos = frame.real_from_local(pos)
				block = self.msp.add_blockref(name, pos, attribs)
				block.dxf.layer = Config.layer_fittings
				self.add_attrib(block, 'collector', ref)

				pos = dorsal.dorsal_to_local(ofs_blue, b)
				pos = frame.real_from_local(pos)
				block = self.msp.add_blockref(name, pos, attribs)
				block.dxf.layer = Config.layer_fittings
				self.add_attrib(block, 'collector', ref)

			pos = dorsal.dorsal_to_local(ofs_red, a)
			pos = frame.real_from_local(pos)
			block = self.msp.add_blockref(name, pos, attribs)
			block.dxf.layer = Config.layer_fittings
			self.add_attrib(block, 'collector', ref)

			pos = dorsal.dorsal_to_local(ofs_blue, a)
			pos = frame.real_from_local(pos)
			block = self.msp.add_blockref(name, pos, attribs)
			block.dxf.layer = Config.layer_fittings
			self.add_attrib(block, 'collector', ref)


	def draw_tlink(self, room: Room, dorsal: Dorsal, ref: str):

		name = leo_icons["tlink"]["name"]
		frame = room.frame

		local_red = dorsal.red_attach
		local_blue = dorsal.blue_attach

		sign = 1 if dorsal.upright else -1
		rot = 3 if dorsal.upright else 0
		rot = frame.block_rotation(rot)

		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': sign*0.1/room.frame.scale,
			'rotation': rot
		}
		pos = frame.real_from_local(local_red)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)


	def draw_bridge(self, room: Room, dorsal: Dorsal, ref: str):

		name = leo_icons["tfit"]["name"]
		frame = room.frame

		u = versor(dorsal.front, dorsal.side)
		if dorsal.wide_size:
			centre = Config.bridge_centre_offset_wide_cm
			u_red = mul(centre, u) 
			u_blue = mul(centre, u)
		else:
			centre = Config.bridge_centre_offset_narrow_cm
			u_red = mul(centre, u) 
			u_blue = mul(centre, u)

		v = versor(dorsal.back, dorsal.front)
		v = mul(Config.bridge_indent, v)
		u_red = adv(u_red, v)
		u_blue = adv(u_blue, v) 

		local_red = adv(dorsal.red_attach, u_red)
		local_blue = adv(dorsal.blue_attach, u_blue)


		rot = 0 if dorsal.upright else 1
		rot = frame.block_rotation(rot)

		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}
		pos = frame.real_from_local(local_red)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)


	def draw_bend(self, room: Room, dorsal: Dorsal):

		name = leo_icons["bend"]["name"]
		frame = room.frame

		local_red = dorsal.red_attach
		local_blue = dorsal.blue_attach

		sign = 1 if dorsal.upright else -1
		rot = 3 if dorsal.upright else 0
		rot = frame.block_rotation(rot)
		
		if (dorsal.boxed and 
			not (dorsal.reversed ^ dorsal.upright)):
			sign = -sign

		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': sign*0.1/room.frame.scale,
			'rotation': rot
		}
		pos = frame.real_from_local(local_red)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings


	def draw_gap(self, room: Room, dorsal: Dorsal, a: point_t, b: point_t):
		frame = room.frame

		# draw pipes
		if dorsal.reversed:
			ofs_red  = (-Config.indent_red, Config.offset_red)
			ofs_blue = (-Config.indent_blue, Config.offset_blue)
			ofs_red_rev  = (Config.indent_blue, Config.offset_red)
			ofs_blue_rev = (Config.indent_red, Config.offset_blue)
		else:
			ofs_red  = (Config.indent_red, Config.offset_red)
			ofs_blue = (Config.indent_blue, Config.offset_blue)
			ofs_red_rev  = (-Config.indent_blue, Config.offset_red)
			ofs_blue_rev = (-Config.indent_red, Config.offset_blue)

		local_red = dorsal.dorsal_to_local(ofs_red, a)
		local_blue = dorsal.dorsal_to_local(ofs_blue, a)
		real_red = frame.real_from_local(local_red)
		real_blue = frame.real_from_local(local_blue)

		local_red_rev = dorsal.dorsal_to_local(ofs_red_rev, b)
		local_blue_rev = dorsal.dorsal_to_local(ofs_blue_rev, b)
		real_red_rev = frame.real_from_local(local_red_rev)
		real_blue_rev = frame.real_from_local(local_blue_rev)

		pline = self.msp.add_lwpolyline([real_red, real_red_rev])
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_red
		pline.dxf.const_width = Config.supply_thick_mm/self.model.scale

		pline = self.msp.add_lwpolyline([real_blue,real_blue_rev])
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_blue
		pline.dxf.const_width = Config.supply_thick_mm/self.model.scale

		# draw nipples
		if dorsal.reversed:
			ofs_red = (Config.attach_red_left, Config.offset_red)
			ofs_blue = (Config.attach_blue_left, Config.offset_blue)
			ofs_red_rev = (-Config.attach_red_right, Config.offset_red)
			ofs_blue_rev = (-Config.attach_blue_right, Config.offset_blue)
		else:
			ofs_red = (Config.attach_red_right, Config.offset_red)
			ofs_blue = (Config.attach_blue_right, Config.offset_blue)
			ofs_red_rev = (-Config.attach_red_left, Config.offset_red)
			ofs_blue_rev = (-Config.attach_blue_left, Config.offset_blue)

		local_red = dorsal.dorsal_to_local(ofs_red, a)
		local_blue = dorsal.dorsal_to_local(ofs_blue, a)
		real_red = frame.real_from_local(local_red)
		real_blue = frame.real_from_local(local_blue)

		local_red_rev = dorsal.dorsal_to_local(ofs_red_rev, b)
		local_blue_rev = dorsal.dorsal_to_local(ofs_blue_rev, b)
		real_red_rev = frame.real_from_local(local_red_rev)
		real_blue_rev = frame.real_from_local(local_blue_rev)

		name = leo_icons["nipple"]["name"]
		rot = frame.block_rotation(dorsal.rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot + 180*dorsal.upright
		}
		block = self.msp.add_blockref(name, real_red, attribs)
		block.dxf.layer = Config.layer_fittings

		block = self.msp.add_blockref(name, real_blue, attribs)
		block.dxf.layer = Config.layer_fittings

		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot + 180*(1-dorsal.upright)
		}
		block = self.msp.add_blockref(name, real_red_rev, attribs)
		block.dxf.layer = Config.layer_fittings

		block = self.msp.add_blockref(name, real_blue_rev, attribs)
		block.dxf.layer = Config.layer_fittings


	def draw_nipples(self, room: Room, dorsal: Dorsal):

		name = leo_icons["nipple"]["name"]
		frame = room.frame

		local_red = dorsal.red_attach
		local_blue = dorsal.blue_attach

		rot = frame.block_rotation(dorsal.rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}
		pos = frame.real_from_local(local_red)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings

	
	def draw_head_link(self, room: Room, dorsal: Dorsal, ref: str):
		frame = room.frame
		rot = (dorsal.rot + 2) % 4
		rot = frame.block_rotation(rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}
		if dorsal.reversed:
			ofs_red  = (-Config.indent_red, Config.offset_red)
			ofs_blue = (-Config.indent_blue, Config.offset_blue)
		else:
			ofs_red  = (Config.indent_red, Config.offset_red)
			ofs_blue = (Config.indent_blue, Config.offset_blue)

		name = leo_icons["link"]["name"]
		pos = dorsal.dorsal_to_local(ofs_red, dorsal.front)
		pos = frame.real_from_local(pos)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)

		pos = dorsal.dorsal_to_local(ofs_blue, dorsal.front)
		pos = frame.real_from_local(pos)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings
		self.add_attrib(block, 'collector', ref)


	def draw_dorsal(self, room: Room, dorsal: Dorsal, ref: str):
	
		if not dorsal.panels:
			return

		# dorsal.local_attachments()
		self.draw_end_caps(room, dorsal, ref)
		self.draw_panel_links(room, dorsal, ref)

		if dorsal.terminal:

			u = [dorsal.back, dorsal.front]
			u = norm(room.frame.real_coord(u))

			s = (0., 0.)
			if room.collector:
				front = room.frame.real_from_local(dorsal.front)
				s = norm([front, room.collector.pos]) 

			if dorsal.indented or (dorsal.detached and 
				xprod(u,s)>Config.cos_beam_angle):
				self.draw_nipples(room, dorsal)
			else:
				self.draw_bend(room, dorsal)
		else:
			if dorsal.boxed:
				self.draw_bend(room, dorsal)
				self.draw_bridge(room, dorsal, ref)
			else:
				self.draw_tlink(room, dorsal, ref)

		self.draw_head_link(room, dorsal, ref)


	def draw_frontline(self, room: Room, line: Line):

		if len(line.dorsals)<1:
			return

		redfront = room.frame.real_coord(line.red_frontline)
		bluefront = room.frame.real_coord(line.blue_frontline)


		scale = self.model.scale

		pline = self.msp.add_lwpolyline(redfront)
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_red
		pline.dxf.const_width = Config.supply_thick_mm/scale

		pline = self.msp.add_lwpolyline(bluefront)
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_blue
		pline.dxf.const_width = Config.supply_thick_mm/scale

		for dorsal in line.dorsals:
			if dorsal.bridged:
				bridge_red = room.frame.real_coord(dorsal.red_bridge)
				pline = self.msp.add_lwpolyline(bridge_red)
				pline.dxf.layer = Config.layer_link
				pline.dxf.color = Config.color_supply_red
				pline.dxf.const_width = Config.supply_thick_mm/scale

				bridge_blue = room.frame.real_coord(dorsal.blue_bridge)
				pline = self.msp.add_lwpolyline(bridge_blue)
				pline.dxf.layer = Config.layer_link
				pline.dxf.color = Config.color_supply_blue
				pline.dxf.const_width = Config.supply_thick_mm/scale


	def draw_collector_link(self, room: Room, line: Line):

		if not room.collector:
			return

		if line.collector:
			pos = line.collector.pos
		else:
			pos = room.collector.pos
		lw = Config.leeway/room.frame.scale
		scale = self.model.scale

		red_link = room.frame.real_coord(line.uplink_red)
		blue_link = room.frame.real_coord(line.uplink_blue)
		extend_pipes(red_link, blue_link, pos, leeway=lw)	

		pline = self.msp.add_lwpolyline(red_link)
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_red
		pline.dxf.const_width = Config.supply_thick_mm/scale

		pline = self.msp.add_lwpolyline(blue_link)
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_blue
		pline.dxf.const_width = Config.supply_thick_mm/scale	


	def draw_lines(self, room: Room):

		for line in room.lines_manager.lines:
			self.draw_frontline(room, line)
			# self.draw_collector_link(room, line)

			for dorsal in line.dorsals:
				ref = line.collector.name if line.collector else ""
				self.draw_dorsal(room, dorsal, ref)


	def find_free_box(self, room: Room, u: point_t) -> point_t:

		scale = room.frame.scale
		step = Config.search_step/scale

		if not isinstance(room.collector, Collector):
			return (0,0)

		v = -u[1], u[0]
		col = room.collector.pos
		ux  = [xprod(diff(col,p), u) for p in room.points]

		ux_min = min(ux)
		ux_max = max(ux)

		sd0 = False 

		coord = ux_min
		while coord<ux_max:
			p = adv(mul(coord, u), col)
			coord += step

			segs = trim_segment_by_poly(room.points, [p, adv(p,v)])
			for seg in segs:
				if dist(seg[0], seg[1]) < step:
					continue
				ss = versor(seg[0], seg[1])
				d = dist(seg[0], seg[1]) - step
				sd = adv(mul(d,ss), seg[0])

				if sd0 is False:
					sd0 = sd

				while d>0:
					sd = adv(mul(d,ss), seg[0])
					d -= step
					bsize = Config.size_smartp_icon/scale
					box = SimpleNamespace(points = 
						   [(sd[0] + bsize, sd[1] + bsize),
					        (sd[0] + bsize, sd[1] - bsize),
					        (sd[0] - bsize, sd[1] - bsize),
					        (sd[0] - bsize, sd[1] + bsize),
					        (sd[0] + bsize, sd[1] + bsize)])

					if not room.embeds(box):
						continue

					flag = True
					for obs in room.obstacles:
						if obs.contains(box):
							flag = False
							break

					if flag:
						return sd

		return sd0 or (0,0)


	def draw_probes(self, room: Room):

		if not isinstance(room.collector, Collector):
			return

		if (room.color == Config.color_disabled_room or
			len(room.panels) == 0):
			return
		scale = room.frame.scale
		col = room.collector.pos
		vers = versor(col, room.pos)

		pos = self.find_free_box(room, vers)

		if (self.model.data["head"] == "none" or
			  (room.color == Config.color_bathroom  and 
			  room.area_m2() <= Config.min_area_probe_th_m2)):
			icon = leo_icons["probe_T"]["name"]
		else:
			icon = leo_icons["probe_TH"]["name"]

		block = self.msp.add_blockref(
				icon,
				pos,
				dxfattribs={
					'xscale': 0.05/scale,
					'yscale': 0.05/scale,
					'rotation': 0 
					}
				)

		block.dxf.layer = Config.layer_probes


	def draw_structure(self, room: Room):

		panels = self.doc.query('*[layer=="%s"]' % Config.layer_panel)
		scale = room.frame.scale
		step = Config.inter_track/scale

		room_panels: list[Insert] = []
		for panel in panels:
			if not isinstance(panel, Insert):
				continue
			attribs = panel.dxfattribs()
			panelx, panely, _ = attribs["insert"]
			if room.is_point_inside((panelx, panely)):
				room_panels.append(panel)

		if not room_panels:
			return

		# Derive main axes
		u = ux, uy = Panel.versor(room_panels[0])
		vx, vy = -uy, ux

		ucoords: list[float] = []
		for panel in room_panels:
			ucoords.extend(panel_tracks(panel, u, scale))
		ucoords.sort()

		ux_min = min([xprod(p, u) for p in room.points])
		ux_max = max([xprod(p, u) for p in room.points])

		# lateral tracks
		lcoords = []
		rcoords = []
		step = Config.extra_track/scale
		lgap = ucoords[0] - ux_min
		if lgap>step:
			ltracks = int(lgap/step)
			incr = lgap/(ltracks+1)
			lcoords = [ux_min + i*incr for i in range(1,ltracks+1)]
	
		rgap = ux_max - ucoords[-1]
		if rgap>step:
			rtracks = int(rgap/step)
			incr = rgap/(rtracks+1)
			rcoords = [ucoords[-1] + i*incr for i in range(1,rtracks+1)]
		
		ucoords = lcoords + ucoords + rcoords


		# remove duplicates and intermediate tracks
		pcoords: list[float] = []
		prev = min(ucoords) - 10/scale
		for ucoord in ucoords:
			gap = ucoord - prev
			if gap < 1/scale:
				continue

			if gap > step:
				incr = gap/(int(gap/step) + 1)
				offset = prev + incr
				while offset < ucoord:
					pcoords.append(offset)
					offset += incr

			pcoords.append(ucoord)
			prev = ucoord


		# trim tracks
		tracks: poly_t = []
		for ucoord in pcoords:
			posx = ux*ucoord
			posy = uy*ucoord
			vect = [(posx, posy), (posx-vx, posy-vy)]
			seg_list = trim_segment_by_poly(room.points, vect)

			for seg in seg_list:
				tracks.append(seg)

		for track in tracks:
			line = self.msp.add_lwpolyline(track)
			line.dxf.layer = Config.layer_struct
			line.dxf.const_width = Config.track_thick_mm/scale
			

	def draw_room(self, room: Room):

		self.write_text("Locale %d" % room.pindex, room.pos, zoom=2.0)

		for line in room.lines_manager.lines:
			if not line.collector:
				continue
			
			for dorsal in line.dorsals:
				for panel in dorsal.panels:
					self.draw_panel(room, panel, line.collector.name)


		self.draw_lines(room)
		# self.draw_airlines(room)
		self.draw_passive(room)

		frame = room.frame
		for panel in room.panels:
			contour = frame.real_coord(panel.contour())
			panel_obs = Element.from_points(contour)
			panel_obs.color = Config.color_panel_contour
			room.obstacles.append(panel_obs)


	def draw_model(self):

		self.draw_zones()

		for room in self.model.processed:
			# self.draw_coord_system(room)
			self.draw_room(room)

		self.draw_collector()
		
		for room in self.model.processed:
			self.draw_structure(room)
			if not self.model.data["control"] == "noreg":
				self.draw_probes(room)

		self.doc.layers.remove(Config.layer_error)


	def draw_passive(self, room: Room):

		hatch = self.msp.add_hatch(color=41)
		hatch.set_pattern_fill("ANSI31", scale=2/self.model.scale)

		hatch.paths.add_polyline_path(room.points, 
			is_closed=True,
			flags=const.BOUNDARY_PATH_EXTERNAL)

		hatch.dxf.layer = Config.layer_lux

		for panel in room.panels:
			poly = room.frame.real_coord(panel.contour())
			hatch.paths.add_polyline_path(poly, 
				is_closed=True,
				flags=const.BOUNDARY_PATH_OUTERMOST)
								 
			lux_poly = panel.lux_poly()
			if lux_poly:
				luxp = room.frame.real_coord(lux_poly)
				lux = self.msp.add_hatch(color=Config.color_collector)
				lux.dxf.layer = Config.layer_lux
				lux.set_pattern_fill("ANSI31", scale=2/self.model.scale)
				lux.paths.add_polyline_path(luxp, is_closed=True)
				pl = self.msp.add_lwpolyline(luxp)
				pl.dxf.layer = Config.layer_lux	


		for obstacle in room.obstacles:
			if obstacle.color == Config.color_obstacle:
				continue
			hatch.paths.add_polyline_path(obstacle.points, 
				is_closed=True,
				flags=const.BOUNDARY_PATH_OUTERMOST)


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

		for _, block in leo_icons.items():
			importer.import_block(block['name'])

		importer.finalize()


	def save(self):
		self.doc.saveas(self.model.outfile)
