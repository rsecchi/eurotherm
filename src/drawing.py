from math import pi, cos, sin
from ezdxf.addons.importer import Importer 
from ezdxf.entities.insert import Insert
from ezdxf.filemanagement import new, readfile
from ezdxf.lldxf import const
from engine.panels import panel_names, panel_map

from lines import Dorsal, Line 
from model import Model, Room
from planner import Panel

from settings import Config
from settings import debug
from settings import leo_types 
from settings import leo_icons
from reference_frame import dist

dxf_version = "AC1032"
from geometry import Picture, extend_pipes, norm, trim_segment_by_poly, xprod
from geometry import poly_t


def panel_tracks(panel: Insert):

	attribs = panel.dxfattribs()
	angle = attribs['rotation']
	name = attribs['name']
	scale = attribs['xscale']/10
	ptype = Config.panel_catalog()[name]['type']
	x, y, _ = attribs['insert']
	tracks = panel_map[ptype]['tracks']

	ux, uy = cos(pi*angle/180), sin(pi*angle/180)
	base = x*ux + y*uy
	step = Config.inter_track/scale
	coords: list[float] = []
	for i in range(tracks):
		coords.append(base - i*step)

	return coords


class DxfDrawing:

	def __init__(self, model: Model):

		self.doc = new(dxf_version)
		# self.doc.header["$LWDISPLAY"] = 1
		self.msp = self.doc.modelspace()
		self.create_layers()
		self.typology = dict()
		self.model = model
		self.picture = Picture()

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
		self.new_layer(Config.layer_struct, Config.color_tracks)

		self.doc.layers.get(Config.layer_lux).off()
		self.doc.layers.get(Config.layer_struct).off()


	def write_text(self, message, position, 
		align=const.MTEXT_MIDDLE_CENTER, 
		zoom=1., col=Config.color_text,
		layer=Config.layer_text):
		
		text = self.msp.add_mtext(message, 
			dxfattribs={"style": "Arial"})
		text.dxf.insert = position
		text.dxf.attachment_point = align
		text.dxf.char_height = (Config.font_size)*zoom
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
				   collector.pos, zoom=0.6/scale, 
				   layer=Config.layer_collector)


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


	def draw_end_caps(self, room: Room, dorsal: Dorsal):

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
		block.dxf.layer = Config.layer_link

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_link


	def draw_panel_links(self, room: Room, dorsal: Dorsal):

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
				continue

			pos = dorsal.dorsal_to_local(ofs_red, a)
			pos = frame.real_from_local(pos)
			block = self.msp.add_blockref(name, pos, attribs)
			block.dxf.layer = Config.layer_link

			pos = dorsal.dorsal_to_local(ofs_blue, a)
			pos = frame.real_from_local(pos)
			block = self.msp.add_blockref(name, pos, attribs)
			block.dxf.layer = Config.layer_link


	def draw_tlink(self, room: Room, dorsal: Dorsal):

		name = leo_icons["tlink"]["name"]
		frame = room.frame
		rot = (dorsal.rot + 2) % 4
		rot = frame.block_rotation(rot)
		attribs={
			'xscale': 0.1/room.frame.scale,
			'yscale': 0.1/room.frame.scale,
			'rotation': rot
		}

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

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings


	def draw_bend(self, room: Room, dorsal: Dorsal):

		name = leo_icons["bend"]["name"]
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

		pos = frame.real_from_local(local_blue)
		block = self.msp.add_blockref(name, pos, attribs)
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

	
	def draw_head_link(self, room: Room, dorsal: Dorsal):
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

		pos = dorsal.dorsal_to_local(ofs_blue, dorsal.front)
		pos = frame.real_from_local(pos)
		block = self.msp.add_blockref(name, pos, attribs)
		block.dxf.layer = Config.layer_fittings


	def draw_dorsal(self, room: Room, dorsal: Dorsal):
	
		if not dorsal.panels:
			return

		# dorsal.local_attachments()
		self.draw_end_caps(room, dorsal)
		self.draw_panel_links(room, dorsal)

		if dorsal.terminal:

			u = [dorsal.back, dorsal.front]
			u = norm(room.frame.real_coord(u))

			s = (0., 0.)
			if isinstance(room.collector, Room):
				front = room.frame.real_from_local(dorsal.front)
				s = norm([front, room.collector.pos]) 

			if dorsal.indented or (dorsal.detached and 
				xprod(u,s)>Config.cos_beam_angle):
				self.draw_nipples(room, dorsal)
			else:
				self.draw_bend(room, dorsal)
		else:
			self.draw_tlink(room, dorsal)

		self.draw_head_link(room, dorsal)


	def draw_frontline(self, room: Room, line: Line):

		if len(line.dorsals)<1:
			return

		redfront = room.frame.real_coord(line.red_frontline)
		bluefront = room.frame.real_coord(line.blue_frontline)

		if room.collector:
			redfront = list(reversed(redfront))
			bluefront = list(reversed(bluefront))
			pos = room.collector.pos
			lw = Config.leeway/room.frame.scale
			extend_pipes(redfront, bluefront, pos, leeway=lw)


		pline = self.msp.add_lwpolyline(redfront)
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_red
		pline.dxf.const_width = Config.supply_thick_mm/self.model.scale

		pline = self.msp.add_lwpolyline(bluefront)
		pline.dxf.layer = Config.layer_link
		pline.dxf.color = Config.color_supply_blue
		pline.dxf.const_width = Config.supply_thick_mm/self.model.scale


	def draw_lines(self, room: Room):

		for line in room.lines_manager.lines:
			self.draw_frontline(room, line)

			for dorsal in line.dorsals:
				self.draw_dorsal(room, dorsal)


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
			ucoords.extend(panel_tracks(panel))
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

		size = 2/room.frame.scale
		self.write_text("Locale %d" % room.pindex, room.pos, zoom=size)

		for panel in room.panels:
			self.draw_panel(room, panel)

		self.draw_lines(room)
		# self.draw_airlines(room)
		self.draw_passive(room)


	def draw_model(self):

		for room in self.model.processed:
			# self.draw_coord_system(room)
			self.draw_room(room)
			self.picture.add(room.points)

		self.picture.set_frame()
		self.picture.draw(self.model.outfile[:-4]+".png")

		self.draw_collector()
		
		for room in self.model.processed:
			self.draw_structure(room)


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
