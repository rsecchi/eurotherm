from typing import TYPE_CHECKING, Optional, Tuple
from planner import Panel
from collector import Collector
from connector import Connector
from reference_frame import adv, invert, mul, versor
from settings import Config
from geometry import dist, poly_t


if TYPE_CHECKING:
	from room import Room

class Dorsal():
	def __init__(self, room: 'Room'):
		self.room = room
		self.panels: list[Panel] = []
		self.front = (0., 0.)
		self.side = (0., 0.)
		self.back = (0., 0.)
		self.back_side = (0., 0.)

		self.area_m2 = 0.
		self.dorsal_row = 0
		self.front_dorsal = True
		self.upright = False
		self.terminal = False
		self.detached = False
		self.reversed = False
		self.boxed = False
		self.water_from_left = False
		self.indented = False
		self.facing_forward = False
		self.facing_inward = False
		self.indent_front = (0., 0.)
		self.indent_side = (0., 0.)

		self.red_attach = (0., 0.)
		self.blue_attach = (0., 0.)
		self.exit_dir = (0., 0.)
		self.red_end = (0., 0.)
		self.blue_end = (0., 0.)
		self.bridged = False
		self.red_bridge: poly_t = []
		self.blue_bridge: poly_t = []
		self.top = 0.
		self.bottom = 0.
		self.level = 0.
		self.wide_size = False

		self.x_axis = (0., 0.)
		self.y_axis = (0., 0.)
		self.rot = 0


	def flow(self) -> float:
		flow = 0.
		for panel in self.panels:
			print(panel)
		return flow


	def dorsal_to_local(self, point: Tuple, orig: Tuple):

		x0, y0 = point
		ux, uy = self.x_axis
		vx, vy = self.y_axis

		rx = ux * x0 + vx * y0
		ry = uy * x0 + vy * y0

		return (rx + orig[0], ry + orig[1])


	def local_attachments(self):

		if not self.water_from_left:
			offs_red = (Config.attach_red_left, Config.offset_red)
			offs_blue = (Config.attach_blue_left, Config.offset_blue)
		else:
			offs_red = (Config.attach_red_right, Config.offset_red)
			offs_blue = (Config.attach_blue_right, Config.offset_blue)

		self.red_attach = self.dorsal_to_local(offs_red, self.front)
		self.blue_attach = self.dorsal_to_local(offs_blue, self.front)


	def insert(self, panel: Panel):

		self.dorsal_row = panel.dorsal_row
		self.area_m2 += panel.area_m2

		self.front = panel.front_corner
		self.side = panel.front_side

		self.wide_size = True if panel.type in [0, 1, 3] else False

		if not self.panels:
			self.rot = panel.rot
			self.water_from_left = (self.rot==0 or self.rot==3)
			self.upright = (panel.rot == 1 or panel.rot == 3)
			self.reversed = (self.rot == 2 or self.rot == 3)
			self.back = panel.rear_corner
			self.back_side = panel.rear_side

			# self.x_axis = versor(self.back, self.front)
			# self.y_axis = versor(self.back, self.back_side)

			dx = dist(self.front, self.back)
			dy = dist(self.back_side, self.back)
			dx_x = self.front[0] - self.back[0]
			dx_y = self.front[1] - self.back[1]
			dy_x = self.back_side[0] - self.back[0]
			dy_y = self.back_side[1] - self.back[1]
			self.x_axis = (dx_x/dx, dx_y/dx)
			self.y_axis = (dy_x/dy, dy_y/dy)
			# ux, uy = self.x_axis
			# vx, vy = self.y_axis
			# if ux*vy < vx*uy:
			# 	self.reversed = True


		if self.upright:
			self.top = min(self.front[0], self.side[0])
			self.bottom = max(self.front[0], self.side[0])
			self.level = self.front[1]
		else:
			self.top = max(self.front[1], self.side[1])
			self.bottom = min(self.front[1], self.side[1])
			self.level = self.front[0]

		self.local_attachments()
		self.panels = [panel] + self.panels



class Line:

	def __init__(self, dorsals: list[Dorsal]):
		self.dorsals = dorsals
		self.flipped = False
		self.area_m2 = 0.
		self.red_frontline: poly_t = []
		self.blue_frontline: poly_t = []
		self.collector: Optional[Collector] = None
		self.collector_link: poly_t = []

		self.uplink_red: poly_t = []
		self.uplink_blue: poly_t = []
		self.red_attach = (0., 0.)
		self.blue_attach = (0., 0.)
		self.dir_attach = (1., 0.)

		for dorsal in dorsals:
			self.area_m2 += dorsal.area_m2

		if len(dorsals)>0:
			self.dorsals[-1].terminal = True

		if len(dorsals)==1:
			self.dorsals[0].detached = True


	def __str__(self) -> str:
		_string = ""
		for dorsal in self.dorsals:
			_string += "[" + str(dorsal.area_m2) + "]"

		return _string


	def front_line(self, offset) -> list[Tuple]:

		_line = []
		for dorsal in self.dorsals:
			ofs = (offset, .0)
			if dorsal.indented:
				front = dorsal.dorsal_to_local(ofs, dorsal.indent_front)
				side = dorsal.dorsal_to_local(ofs, dorsal.indent_side)
			else:
				front = dorsal.dorsal_to_local(ofs, dorsal.front)
				side = dorsal.dorsal_to_local(ofs, dorsal.side)

			if dorsal.rot == 2 or dorsal.rot == 3:
				front, side = side, front

			_line.append(front)
			_line.append(side)


		return _line


	def make_frontline(self):

		dorsals = self.dorsals

		if not dorsals:
			return

		for dorsal in reversed(dorsals):
			v = versor(dorsal.back, dorsal.front)
			u = versor(dorsal.front, dorsal.side)

			ur = mul(Config.tfit_offset_red, u)
			ub = mul(Config.tfit_offset_blue, u)
			vs = mul(Config.tfit_offset_front_cm, v)
			dorsal.red_end = adv(dorsal.red_attach, vs)
			dorsal.blue_end = adv(dorsal.blue_attach, vs)

			if dorsal.boxed and not dorsal.terminal:
				red_bridge_end = adv(dorsal.red_end, ur)
				blue_bridge_end = adv(dorsal.blue_end, ub)
				dorsal.bridged = True
				dorsal.red_bridge = [dorsal.red_end, red_bridge_end]
				dorsal.blue_bridge = [dorsal.blue_end, blue_bridge_end]
				dorsal.red_end = red_bridge_end
				dorsal.blue_end = blue_bridge_end

		self.red_attach = dorsals[0].red_end
		self.blue_attach = dorsals[0].blue_end


		scale = dorsals[0].room.frame.scale
		for i in range(len(dorsals)-1, 0, -1):
			connector = Connector()
			connector.stub_length = Config.stub_length_cm/scale
			connector.link_width = Config.link_width_cm/scale
			d0 = dorsals[i]
			d1 = dorsals[i-1]

			u0 = versor(d0.front,d0.side)
			u1 = invert(u0)
			v = versor(d0.back, d0.front)

			if d0.boxed:
				dir0 = u0 if d0.reversed else v
			else:
				dir0 = u0 if d0.reversed else u1

			u0 = versor(d1.front,d1.side)
			u1 = invert(u0)
			v = versor(d1.back, d1.front)

			if d1.boxed:
				dir1 = v if d1.reversed else u0
				d1.exit_dir = u0 if d1.reversed else v
			else:
				dir1 = u1 if d1.reversed else u0
				d1.exit_dir = u0 if d1.reversed else u1

			frame = d0.room.frame
			red_end = tuple(frame.real_from_local(d0.red_end))
			blue_end = tuple(frame.real_from_local(d0.blue_end))
			dir0 = frame.real_versor(dir0)
			connector.attach(red_end, blue_end, dir0)

			frame = d1.room.frame
			red_end = tuple(frame.real_from_local(d1.red_end))
			blue_end = tuple(frame.real_from_local(d1.blue_end))
			dir1 = frame.real_versor(dir1)
			connector.attach(red_end, blue_end, dir1)
			connector.point_to_point()
			self.red_frontline += connector.red_path
			self.blue_frontline += connector.blue_path



