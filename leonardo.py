#!/usr/local/bin/python3

import ezdxf
from ezdxf.addons import Importer

import openpyxl
import queue
import bisect
import threading
import numpy as np
from openpyxl.styles.borders import Border, Side
import os.path
from math import ceil, floor, sqrt
from copy import copy, deepcopy
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import askyesno

dxf_version = "AC1024"

# block names
block_blue_120x100  = "Leo 55_120"
block_blue_60x100   = "Leo 55_60"
block_green_120x100 = "Leo 55_120 idro"
block_green_60x100  = "Leo 55_60 idro"


# Parameter settings (values in cm)
default_scale = 1  # scale=100 if the drawing is in m
default_tolerance    = 1   # ignore too little variations

extra_len    = 20
zone_cost = 1
min_room_area = 1
max_room_area = 500
default_max_clt_distance = 1500
max_clt_break = 5

feeds_per_collector = 8
area_per_feed_m2 = 14.4
target_eff = 0.7

default_font_size = 35

# Half panels default dimensions in cm
default_panel_width = 100
default_panel_height = 60
default_hatch_width = 15
default_hatch_height = 10

default_search_tol = 5
default_min_dist = 20
default_min_dist2 = default_min_dist*default_min_dist
default_wall_depth = 50

default_input_layer = 'AREE LEONARDO'
layer_text   = 'Eurotherm_text'
layer_box    = 'Eurotherm_box'
layer_panel  = 'Eurotherm_panel'
layer_panelp = 'Eurotherm_prof'
layer_link   = 'Eurotherm_link'

text_color = 7
box_color = 8
collector_color = 1
ask_for_write = False

MAX_COST = 1000000
MAX_DIST = 1e20

RIGHT = 1
LEFT = 0
TOP = 1
BOTTOM = 0

xlsx_template = 'leo_template.xlsx'
sheet_template_1 = 'LEONARDO 5.5'
sheet_template_2 = 'LEONARDO 3.5'
sheet_template_3 = 'LEONARDO 3.0 PLUS'

sheet_breakdown = 'Panels BOM'
show_panel_list = True

alphabet = {
	' ': [],
	'A': [12,3,1,5,14,8,6],
	'B': [0,1,5,7,6,7,11,13,12,0],
	'C': [2,1,3,9,13,14],
	'D': [0,1,5,11,13,12,0],
	'E': [2,0,6,7,6,12,14],
	'F': [2,0,6,7,6,12],
	'G': [2,1,3,9,13,14,8,7],
	'H': [0,12,6,8,2,14],
	'I': [1,13],
	'J': [9,13,1,0,1,2],
	'K': [0,6,2,6,12,6,14],
	'L': [0,12,14],
	'M': [12,0,7,2,14],
	'N': [12,0,14,2],
	'O': [3,1,5,11,13,9,3],
	'P': [12,0,1,5,7,6],
	'Q': [13,11,5,1,3,9,13,14,13,10],
	'R': [12,0,1,5,7,6,7,11,14],
	'S': [12,13,11,3,1,2],
	'T': [0,2,1,13],
	'U': [0,9,13,11,2],
	'V': [0,13,2],
	'W': [0,13,2],
	'X': [0,14,7,2,12],
	'Y': [0,7,2,7,13],
	'Z': [0,2,12,14],
	'0': [1,3,9,13,11,5,1],
	'1': [3,1,13,12,14],
	'2': [3,1,5,12,14],
	'3': [0,1,5,7,6,7,11,13,12],
	'4': [0,6,8,2,14],
	'5': [2,0,6,7,11,13,12],
	'6': [2,1,3,9,13,11,7,6],
	'7': [0,2,12],
	'8': [3,1,5,9,12,14,11,3],
	'9': [8,6,3,1,5,11,13,12]
}


max_iterations = 5e6


def pletter(letter,pos,scale):
	path = alphabet[letter]
	poly = []
	for p in path:
		x = p % 3
		y = 4 - (p//3)
		poly.append((pos[0]+x*scale[0], pos[1]+y*scale[1]))
	return poly

def writedxf(msp, strn, pos, scale):

	slen = len(strn)*scale[0]*3
	pos = (pos[0]-slen/2, pos[1]-scale[1]*2)
	
	for l in strn:
		poly = pletter(l, pos, scale)
		pl = msp.add_lwpolyline(poly)
		pl.dxf.layer = layer_text
		pos = (pos[0]+scale[0]*3, pos[1])

def write_text(msp, strn, pos):
	
	text = msp.add_mtext(strn, 
		dxfattribs={"style": "Arial"})
	text.dxf.insert = pos
	text.dxf.attachment_point = ezdxf.lldxf.const.MTEXT_MIDDLE_CENTER
	text.dxf.char_height = font_size
	text.dxf.layer = layer_text
	

def spread(a,b,size):
	l = []
	n = ceil(abs(a-b)/size) - 1
	L = abs(a-b)/(n+1)
	for i in range(0,n):
		l.append((i+1)*L+a)
	return l

def center(a,b,size):
	l = []
	n = ceil(abs(b-a)/size) - 1
	L = (abs(b-a) - size*n)/2
	for i in range(0,n+1):
		l.append(a+L+i*size)	
	return l

def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)
	

def intersects(p, x):
		
	ints = []
	eps = 1e-6
		
	for i in range(0, len(p)-1):
		vx, vy = p[i+1][0]-p[i][0], p[i+1][1]-p[i][1]

		if (p[i+1][0]==x or p[i][0]==x):
				x += eps

		if (p[i][0] < p[i+1][0]):
			x0, y0 = p[i][0], p[i][1]
			x1, y1 = p[i+1][0], p[i+1][1]
		else:
			x0, y0 = p[i+1][0], p[i+1][1]
			x1, y1 = p[i][0], p[i][1]
					
		if (x0<x and x<x1):
			delta = x1 - x0
			py = (y0*(x1-x) - y1*(x0-x))/delta
			ints.append(py)
	
	return sorted(ints)


# Check if line crosses box
def cross(box, line):

	p0, p1 = line[0], line[1]
	p0x = p0[0]; p0y = p0[1]
	p1x = p1[0]; p1y = p1[1]
	ax = box[0]; bx = box[1]
	ay = box[2]; by = box[3]

	# both left/right/up/down
	if ( (p0x<=ax and p1x<=ax) or
	     (p0x>=bx and p1x>=bx) or
		 (p0y<=ay and p1y<=ay) or
		 (p0y>=by and p1y>=by)):
		return False

	# vertical or horizontal line inside
	if (p0x == p1x or p0y == p1y):
		return True

	# lateral crossing 
	A1 = (ay - p0y) * (p1x - p0x)
	A2 = (ax - p0x) * (p1y - p0y)
	A3 = (by - p0y) * (p1x - p0x)
	A4 = (bx - p0x) * (p1y - p0y)

	if (p1x>p0x):
		if (p1y>p0y):
			return  ((A1<=A2 and A2<=A3) or
				     (A2<=A1 and A1<=A4) or
				     (A1<=A4 and A4<=A3) or
				     (A2<=A3 and A3<=A4))
		else:
			return  ((A1<=A2 and A2<=A3) or
				     (A2>=A1 and A1>=A4) or
				     (A1<=A4 and A4<=A3) or
				     (A2>=A3 and A3>=A4))
	else:
		if (p1y>p0y):
			return  ((A1>=A2 and A2>=A3) or
				     (A2<=A1 and A1<=A4) or
				     (A1>=A4 and A4>=A3) or
				     (A2<=A3 and A3<=A4))
			
		else:
			return  ((A1>=A2 and A2>=A3) or
				     (A2>=A1 and A1>=A4) or
				     (A1>=A4 and A4>=A3) or
				     (A2>=A3 and A3>=A4))
	return False


def hdist(line, point):
	(xp,yp) = point
	(x0,y0),(x1,y1) = line
	
	(x0,y0) = (x0-xp,y0-yp)
	(x1,y1) = (x1-xp,y1-yp)

	if ((y0>0 and y1>0) or (y0<0 and y1<0)):
		return MAX_DIST

	if (y0==y1):
		return min(x1,x0)

	return abs((x0*y1-x1*y0)/(y1-y0))


def dist2(line, point):
	(xp,yp) = point
	(x0,y0),(x1,y1) = line
	
	(ux, uy) = (x1-x0, y1-y0)
	(px, py) = (xp-x0, yp-y0)
	
	u2 = ux*ux + uy*uy
	p2 = px*px + py*py
	up = ux*px + uy*py

	if (u2==0):
		return (0, False, point)

	q = (x0 + up*ux/u2, y0 + up*uy/u2)

	if (up>u2):
		return (u2+p2-2*up, False, line[1])

	if (up<=0 or u2==0):
		return (p2, False, line[0])

	return (p2-up*up/u2, True, q)



# Project line1 into line2 and returns the 
# facing segments
def is_gate(line, target):
	
	(xa0,ya0), (xa1,ya1) = (a0,a1) = line
	(xb0,yb0), (xb1,yb1) = (b0,b1) = target

	# reference on target
	(ux, uy) = (xb1-xb0, yb1-yb0)
	u = sqrt(ux*ux + uy*uy)
	(uvx, uvy) = (ux/u, uy/u)
	(uox, uoy) = (-uvy, uvx)
	
	# change of reference for p and q
	(px, py) = (xa0-xb0, ya0-yb0)
	(qx, qy) = (xa1-xb0, ya1-yb0)
	(npx, npy) = (uvx*px+uvy*py, uox*px+uoy*py)
	(nqx, nqy) = (uvx*qx+uvy*qy, uox*qx+uoy*qy)

	w = abs(npx - nqx)

	if ((w <= min_dist) or
		(npx<=0 and nqx<=0) or (npx>=u and nqx>=u)):
		return (False, (None, None))

	if (npx<0):
		p1 = (xb0,yb0)
		l1 = 0
	else:
		if (npx>u):
			p1 = (xb1,yb1)
			l1 = u
		else:
			p1 = (xb0+uvx*npx, yb0+uvy*npx)
			l1 = npx

	if (nqx<0):
		p2 = (xb0,yb0)
		l2 = 0
	else:
		if (nqx>u):
			p2 = (xb1,yb1)
			l2 = u
		else:
			p2 = (xb0+uvx*nqx, yb0+uvy*nqx)
			l2 = nqx

	if (abs(l1-l2)<=min_dist):
		return (False, (None, None))

	d1 = abs((npy*(nqx-l1) - (npx-l1)*nqy)/w)
	d2 = abs((npy*(nqx-l2) - (npx-l2)*nqy)/w)
	
	if (d1<= wall_depth and d2<=wall_depth):
		return (True, (p1, p2))

	return (False, (None, None))


# This class represents the radiating panel
# with its characteristics
# side=00  -->  water feed over top edge, left panel
# side=01  -->  water feed over bottom edge, left panel
# side=10  -->  water feed over top edge, right panel
# side=11  -->  water feed over bottom edge, right panel
class Panel:
	def __init__(self, cell, size, side):
		self.side = side
		self.cell = cell
		self.xcoord = self.cell.box[0]
		self.ycoord = self.cell.box[2]
		self.width  = (self.cell.box[1] - self.xcoord) * size[0]
		self.height = (self.cell.box[3] - self.ycoord) * size[1]
		self.size = size
		self.color = cell.color
		self.mode = cell.mode
		self.pos = (self.xcoord, self.ycoord)


	def draw_whole(self, msp):

		ax = self.xcoord; bx = ax + self.width
		ay = self.ycoord; by = ay + self.height

		if (self.side==0 or self.side==2):
			if (self.mode==0):
				orig1 = (ax, by)
				orig2 = (bx, by)
			else:
				orig1 = (by, ax)
				orig2 = (by, bx)
		else:
			if (self.mode==0):
				orig1 = (ax, ay)
				orig2 = (bx, ay)
			else:
				orig1 = (ay, ax)
				orig2 = (ay, bx)

		if (self.side==0 or self.side==2):
			if (self.mode==0):
				rot1, xs1, ys1 = 90, 0.1, 0.1
				rot2, xs2, ys2 = 90, 0.1, -0.1
			else:
				rot1, xs1, ys1 = 0, 0.1, -0.1
				rot2, xs2, ys2 = 0, 0.1, 0.1
		else:
			if (self.mode==0):
				rot1, xs1, ys1 = 90, -0.1, 0.1
				rot2, xs2, ys2 = 90, -0.1, -0.1
			else:
				rot1, xs1, ys1 = 0, -0.1, -0.1
				rot2, xs2, ys2 = 0, -0.1, 0.1

		xs1, ys1 = xs1/scale, ys1/scale
		xs2, ys2 = xs2/scale, ys2/scale

		block1 = msp.add_blockref(self.panel_type, orig1, 
			dxfattribs={'xscale': xs1, 'yscale': ys1, 'rotation': rot1})

		block2 = msp.add_blockref(self.panel_type, orig2, 
			dxfattribs={'xscale': xs2, 'yscale': ys2, 'rotation': rot2})

		block1.dxf.layer = layer_panel
		block2.dxf.layer = layer_panel


	def draw_half(self, msp):

		ax = self.xcoord; bx = ax + self.width
		ay = self.ycoord; by = ay + self.height
	
		if (self.side==0):
			orig = (ax, by)
			if (self.mode==0):
				rot, xs, ys = 90, 0.1, 0.1
			else:
				rot, xs, ys = 0, 0.1, -0.1

		if (self.side==1):
			orig = (ax, ay)
			if (self.mode==0):
				rot, xs, ys = 90, -0.1, 0.1
			else:
				rot, xs, ys = 0, -0.1, -0.1

		if (self.side==2):
			orig = (bx,by)
			if (self.mode==0):
				rot, xs, ys = 90, 0.1, -0.1
			else:
				rot, xs, ys = 0, 0.1, 0.1

		if (self.side==3):
			orig = (bx,ay)
			if (self.mode==0):
				rot, xs, ys = 90, -0.1, -0.1
			else:
				rot, xs, ys = 0, -0.1, 0.1

		if (self.mode==1):
			orig = (orig[1], orig[0])

		xs, ys = xs/scale, ys/scale

		block = msp.add_blockref(self.panel_type, orig, 
			dxfattribs={'xscale': xs, 'yscale': ys, 'rotation': rot})

		block.dxf.layer = layer_panel


	def draw(self, msp):

		if (self.size[1]==2):
			if (self.color==3):
				self.panel_type = block_green_120x100	
			else:
				self.panel_type = block_blue_120x100	
		else:
			if (self.color==3):
				self.panel_type = block_green_60x100	
			else:
				self.panel_type = block_blue_60x100	

		if (self.size[0]==2):
			self.draw_whole(msp)
		else:
			self.draw_half(msp)


	def draw_profile(self, msp):
		ax = self.xcoord; bx = ax + self.width
		ay = self.ycoord; by = ay + self.height
		dx = hatch_width; dy = hatch_height

		pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
		
		if (self.size==(2,2) or self.size==(2,1)):
			if (self.side==1 or self.side==3):
				pline = [(ax,ay+dy),(ax,by),(bx,by),(bx,ay+dy),
					(bx-dx,ay+dy),(bx-dx,ay),(ax+dx,ay),(ax+dx,ay+dy),(ax,ay+dy)]

			if (self.side==0 or self.side==2):
				pline = [(ax,ay),(ax,by-dy),(ax+dx,by-dy),(ax+dx,by),(bx-dx,by),
					(bx-dx,by-dy),(bx,by-dy),(bx,ay),(ax,ay)]

		if (self.size==(1,1) or self.size==(1,2)):
			if (self.side==1):
				pline = [(ax,ay+dy),(ax,by),(bx,by),(bx,ay),(ax+dx,ay),
						 (ax+dx,ay+dy),(ax,ay+dy)]
			if (self.side==0):
				pline = [(ax,by-dy),(ax+dx,by-dy),(ax+dx,by),(bx,by),
						 (bx,ay),(ax,ay),(ax,by-dy)]
			if (self.side==3):
				pline = [(ax,ay),(ax,by),(bx,by),(bx,ay+dy),
						 (bx-dx,ay+dy),(bx-dx,ay),(ax,ay)]
			if (self.side==2):
				pline = [(ax,ay),(ax,by),(bx-dx,by),(bx-dx,by-dy),
						 (bx,by-dy),(bx,ay),(ax,ay)]


		if (self.mode==1):
			for i in range(0,len(pline)):
				pline[i] = (pline[i][1], pline[i][0])

		pl = msp.add_lwpolyline(pline)
		pl.dxf.layer = layer_panelp
		pl.dxf.color = self.color


	# Check if the distance from the wall is smaller 
	# than the minimum allowed and updates gapl and gapr
	def dist_from_walls(self):

		room = self.cell.room

		ax = self.xcoord; bx = ax + self.width
		ay = self.ycoord; by = ay + self.height

		if (self.side==0 or self.side==2):
			lft = (ax,by)
			rgt = (bx,by)
			self.gapl = room.hdist_from_poly(lft)
			self.gapr = room.hdist_from_poly(rgt)
		else:
			lft = (ax,ay)
			rgt = (bx,ay)
			self.gapl = room.hdist_from_poly(lft)
			self.gapr = room.hdist_from_poly(rgt)

		# dist from internal walls
		for obs in room.obstacles:
			self.gapl = min(obs.hdist_from_poly(lft), self.gapl)
			self.gapr = min(obs.hdist_from_poly(rgt), self.gapr)

class Dorsal:
	def __init__(self, grid, pos, side):
		self.panels = list()
		self.pos = pos
		self.grid = grid
		self.side = side
		self.elems = 0
		self.gapl = MAX_DIST
		self.gapr = MAX_DIST
		self.gap = 0

	# (row, start)  is the position of the top-left element
	def make_dorsal(self):

		m = self.grid
		self.cost = 0
		self.lost = 0
		j = self.pos[1] - 2
		i = self.pos[0]

		side = self.side

		while(j<m.shape[1]-3):

			j += 2

			if (m[i,j] and m[i+1,j] and m[i,j+1] and m[i+1,j+1]):
				self.new_panel(m[i,j],(2,2),side)
				continue
		
			if side==1:
				if (m[i,j] and m[i,j+1] and
					(not m[i+1,j]) and (not m[i+1,j+1])):
					self.new_panel(m[i,j],(2,1))
					continue

				# half panels vertical
				if m[i+1,j]:
					if m[i,j]:
						self.new_panel(m[i,j],(1,2),0)
						self.cost += 1
					else:
						self.cost += 4
						self.lost += 1	
				else:
					if m[i,j]:
						self.new_panel(m[i,j],(1,1),0)
						self.cost += 1

				if m[i+1,j+1]:
					if m[i,j+1]:
						self.new_panel(m[i,j+1],(1,2),1)
						self.cost += 1
					else:
						self.cost += 4
						self.lost += 1	
				else:
					if m[i,j+1]:
						self.new_panel(m[i,j+1],(1,1),1)
						self.cost += 1

			else:
				if (m[i+1,j] and m[i+1,j+1] and
					(not m[i,j]) and (not m[i,j+1])):
					self.new_panel(m[i+1,j],(2,1))
					continue

				# half panels vertical
				if m[i,j]:
					if m[i+1,j]:
						self.new_panel(m[i,j],(1,2),0)
						self.cost += 1
					else:
						self.cost += 4
						self.lost += 1	
				else:
					if m[i+1,j]:
						self.new_panel(m[i+1,j],(1,1),0)
						self.cost += 1

				if m[i,j+1]:
					if m[i+1,j+1]:
						self.new_panel(m[i,j+1],(1,2),1)
						self.cost += 1
					else:
						self.cost += 4
						self.lost += 1	
				else:
					if m[i+1,j+1]:
						self.new_panel(m[i+1,j+1],(1,1),1)
						self.cost += 1

	# handside 0=left, 1=right
	def new_panel(self, cell, size, handside=0):

		panel = Panel(cell,size,self.side+handside*2)
		self.elems += size[0]*size[1]

		panel.dist_from_walls()

		# Calculate water entry point
		ax = panel.xcoord; bx = ax + panel.width
		ay = panel.ycoord; by = ay + panel.height
		if (self.side==0):
			lft = (ax,by)
			rgt = (bx,by)
		else:
			lft = (ax,ay)
			rgt = (bx,ay)
		
		if (self.room.clt_xside == LEFT):
			if (len(self.panels)==0 or
			    self.attach[0] > lft[0]):
				self.attach = lft
		else:
			if (len(self.panels)==0 or
			    self.attach[0] < rgt[0]):
				self.attach = rgt

		self.panels.append(panel)

		if (panel.gapl < self.gapl):
			self.gapl = panel.gapl

		if (panel.gapr < self.gapr):
			self.gapr = panel.gapr


class Dorsals(list):
	def __init__(self, room):
		self.cost = 0 
		self.gapl = MAX_DIST
		self.gapr = MAX_DIST
		self.gap = 0
		self.elems = 0
		self.panels = list()
		self.room = room
	
	def add(self, dorsal):	
		global min_dist
		self.cost += dorsal.cost
		self.elems += dorsal.elems
		self.panels += dorsal.panels

		if (len(dorsal.panels)>0):
			self.append(dorsal)
		
		self.gapr = min(self.gapr, dorsal.gapr)
		self.gapl = min(self.gapl, dorsal.gapl)

		if (self.room.clt_xside==LEFT):
			if (self.gapl<min_dist):
				return False
			else:
				self.gap = self.gapl

		if (self.room.clt_xside==RIGHT):
			if (self.gapr<min_dist):
				return False
			else:
				self.gap = self.gapr

		return True

# Cell of the grid over which panels are laid out
class Cell:
	def __init__(self, pos, box, room, mode):
		self.pos = pos
		self.box = box
		self.room = room
		self.color = room.color
		self.mode = mode

	def draw(self, msp):
		box = self.box
		ax = box[0]; bx = box[1]
		ay = box[2]; by = box[3]
		pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
		if (self.mode==1):
			for i in range(0,len(pline)):
				pline[i] = (pline[i][1], pline[i][0])
		pl = msp.add_lwpolyline(pline)
		pl.dxf.layer = layer_box


# This class represents the grid over which the panels
# are laid out.
class PanelArrangement:

	def __init__(self, room):
		self.best_grid = self.cells = list()
		self.dorsals = Dorsals(room)
		self.dorsals.cost = MAX_COST
		self.room = room
		self.elems = 0
		self.alloc_mode = -1

	def len(self):
		return len(self.cells)

	def make_grid(self, origin):

		self.cells = list()

		(sx, sy) = origin
	
		col = 0
		sax = sx
		while(sax+panel_width <= self.room.bx):
			say = sy
			row = 0
			while(say+panel_height <= self.room.by):
				pos = (row, col)
				box = (sax, sax+panel_width, say, say+panel_height)
				flag = True
				if self.room.is_box_inside(box):
					for obstacle in self.room.obstacles:
						if not obstacle.is_box_outside(box):
							flag = False
							break
				else:
					flag = False

				if (flag):
					self.cells.append(Cell(pos, box, self.room, self.mode))
				say += panel_height
				row += 1

			sax += panel_width
			col += 1

		if (len(self.cells)==0):
			return False

		maxr = self.rows = max([c.pos[0] for c in self.cells]) + 7
		maxc = self.cols = max([c.pos[1] for c in self.cells]) + 3

		m = self.grid = np.full((maxr, maxc), None)

		for cell in self.cells:
			m[(cell.pos[0]+3, cell.pos[1]+1)] = cell

		return True

	def build_dorsals(self, pos):

		dorsals = Dorsals(self.room)

		i = pos[0]
		while(i<self.rows-3):
			init_pos = (i, pos[1]) 

			bottomdorsal = Dorsal(self.grid, init_pos, 0)
			bottomdorsal.room = self.room
			bottomdorsal.make_dorsal()

			init_pos = (i+2, pos[1]) 
			topdorsal = Dorsal(self.grid, init_pos, 1)
			topdorsal.room = self.room
			topdorsal.make_dorsal()

			if (not dorsals.add(topdorsal) or
			    not dorsals.add(bottomdorsal)):
				return None
				
			i += 4

		return dorsals
	
	def alloc_panels(self, origin):

		if (not self.make_grid(origin)):
			return

		for j in range(0,2):
			for i in range(0,4):
				# set origin of dorsals
				pos = (i, j)
				trial_dorsals = self.build_dorsals(pos)
				if ((not trial_dorsals == None ) and
					((trial_dorsals.elems > self.dorsals.elems) or
					(trial_dorsals.elems == self.dorsals.elems and
					 trial_dorsals.cost < self.dorsals.cost) or
					(trial_dorsals.elems == self.dorsals.elems and
					 trial_dorsals.cost == self.dorsals.cost and
					 trial_dorsals.gap > self.dorsals.gap))):
						self.dorsals = trial_dorsals
						self.best_grid = self.cells
						self.alloc_mode = self.mode

	def draw_grid(self, msp):	
		for cell in self.best_grid:
			cell.draw(msp)

# This class represents the rrom described by a 
# polyline
class Room:

	index = 1

	def __init__(self, poly, output):

		self.index = Room.index
		Room.index = Room.index + 1
		self.output = output
		self.ignore = False
		self.errorstr = ""
		self.contained_in = None
		self.obstacles = list()
		self.gates = list()

		tol = tolerance
		self.orient = 0
		self.boxes = list()
		self.coord = list()

		self.points = list(poly.vertices())	

		# Add a final point to closed polylines
		p = self.points
		if (poly.is_closed):
			self.points.append((p[0][0], p[0][1]))

		# Check if the polyine is open with large final gap
		n = len(p)-1
		if (abs(p[0][0]-p[n][0])>tol or abs(p[0][1]-p[n][1])>tol):
			self.errorstr = "Error: open polyline in Zone %d \n" % self.index 
			self.ignore = True
			return

		# Straighten up walls
		finished = False
		while not finished:
			for i in range(1, len(p)):
				if (abs(p[i][0]-p[i-1][0]) < tol):
					p[i] = (p[i-1][0], p[i][1])

				if (abs(p[i][1]-p[i-1][1]) < tol):
					p[i] = (p[i][0], p[i-1][1])

			if (p[0] == p[n]):
				finished = True
			else:
				p[0] = p[n]

		# Projections of coordinates on x and y
		self.xcoord = sorted(set([p[0] for p in self.points]))	
		self.ycoord = sorted(set([p[1] for p in self.points]))	

		self.color = poly.dxf.color
		self.arrangement = PanelArrangement(self)
		self.panels = list()
		self.bounding_box()
		self.area = self._area()
		self.pos = self._barycentre()
		self.perimeter = self._perimeter()

	def _area(self):
		a = 0
		p = self.points
		for i in range(0, len(p)-1):
			a += (p[i+1][0]-p[i][0])*(p[i+1][1] + p[i][1])/2
		return abs(a/10000)

	def _centre(self):
		(cx, cy) = (0, 0)
		p = self.points
		n = len(p)-1
		for i in range(0,n):
			p = self.points[i]
			(cx, cy) = (cx+p[0], cy+p[1])

		return (cx/n, cy/n)
		

	def _perimeter(self):
		p = self.points
		d = 0
		for i in range(0, len(p)-1):
			d += sqrt(pow(p[i+1][0]-p[i][0],2)+pow(p[i+1][1]-p[i][1],2))
		return d

	def _barycentre(self):
		
		p = self.points
		(xb, yb) = (0, 0)
		Ax = Ay = 0
		for i in range(len(p)-1):
			(x0, y0) = p[i]
			(x1, y1) = p[i+1]
			xb += (y1-y0)*(x0*x0+x0*x1+x1*x1)/6
			yb += (x1-x0)*(y0*y0+y0*y1+y1*y1)/6
			Ax += (y1-y0)*(x0+x1)/2
			Ay += (x1-x0)*(y0+y1)/2

		return (xb/Ax, yb/Ay)

	def bounding_box(self):
		self.ax = min(self.xcoord)
		self.bx = max(self.xcoord)
		self.ay = min(self.ycoord)
		self.by = max(self.ycoord)
		
	def dist_linear(self, collector):

		dorsals = self.arrangement.dorsals
		d = MAX_DIST
		for dorsal in dorsals:
			cltr_dist = dist(dorsal.pos, collector.pos)
			if (d > cltr_dist):
				d = cltr_dist 
				attachment = dorsal.pos
		return (d, attachment)

	def dist_on_tree(self, collector):

		dorsals = self.arrangement.dorsals
		d = MAX_DIST
		attachment = None
		for dorsal in dorsals:
			cltr_dist = dist(dorsal.pos, collector.pos)
			if (d >= cltr_dist):
				d = cltr_dist 
				attachment = dorsal.pos

		d = MAX_DIST
		uplink = None
		for cltr, walk, next_room in self.links:
			if (cltr == collector):
				d = walk
				uplink = next_room

		return (d, attachment, uplink)


	def wall(self, room):
		for nroom, nwall in self.gates:
			if (room==nroom):
				return nwall

	# Building Room
	def alloc_panels(self):
		global panel_height, panel_width, search_tol

		self.arrangement.mode = 0   ;# horizontal
		while self.arrangement.mode < 2:
			self.bounding_box()
			# search within a small panel range
			sx = 0
			while sx<panel_width:
				sy = 0
				while sy<panel_height:
					origin = (sx + self.ax, sy + self.ay)
					self.arrangement.alloc_panels(origin)
					self.panels = self.arrangement.dorsals.panels
				
					sy += search_tol
				sx += search_tol

			for i in range(0,len(self.points)):
				self.points[i] = (self.points[i][1], self.points[i][0])
			(self.xcoord, self.ycoord) = (self.ycoord, self.xcoord)

			for obs in self.obstacles:
				for i in range(0,len(obs.points)):
					obs.points[i] = (obs.points[i][1], obs.points[i][0])
				(obsxcoord, obs.ycoord) = (obs.ycoord, obs.xcoord)
	
			(self.clt_xside,self.clt_yside) = (self.clt_yside,self.clt_xside) 
	
			self.arrangement.mode += 1  


	def is_point_inside(self, point):


		p = self.points
		x, y = point
		ints = 0

		for i in range(0, len(p)-1):
	
			if (p[i][0]==x and p[i+1][0]==x):
				if (max(p[i][1], p[i+1][1]) >= y
				  and min(p[i][1], p[i+1][1]) <=y):
					return True

			#if (p[i][1]==y and p[i+1][1]==y and
			#	min(p[i][0], p[i+1][0]) <= x <= max(p[i][0], p[i+1][0])):
			#		return True

			if (p[i][0] == p[i+1][0]):
				continue	

			if (p[i][0] < p[i+1][0]):
				x0, y0 = p[i][0], p[i][1]
				x1, y1 = p[i+1][0], p[i+1][1]
			else:
				x0, y0 = p[i+1][0], p[i+1][1]
				x1, y1 = p[i][0], p[i][1]

			
			if (x0<=x and x<x1):
				if (y0==y1 and y0==y):
					return True

				delta = x1 - x0
				py = (y0*(x1-x) - y1*(x0-x))/delta
				if (py>=y):
					ints += 1

		return (ints % 2 == 1)


	def is_box_inside(self, box):

		# Check if the center is inside
		center = ((box[0]+box[1])/2, (box[2]+box[3])/2)
		if (not self.is_point_inside(center)):
			return False

		# Does polyline cross box?
		p = self.points
		for i in range(0, len(p)-1):
			line = (p[i], p[i+1]) 
			if (cross(box, line)):
				return False

		return True

	def is_box_outside(self, box):

		# Check if the center is inside
		center = ((box[0]+box[1])/2, (box[2]+box[3])/2)
		if (self.is_point_inside(center)):
			return False

		# Does polyline cross box?
		p = self.points
		for i in range(0, len(p)-1):
			line = (p[i], p[i+1]) 
			if (cross(box, line)):
				return False

		return True

	def dist2_from_poly(self, point):

		cd = MAX_DIST
		p = self.points
		for i in range(0, len(p)-1):
			line = (p[i], p[i+1]) 
			d2 = dist2(line, point)
			if (d2<cd):
				cd = d2
		return cd

	def hdist_from_poly(self, point):

		cd = MAX_DIST
		p = self.points
		for i in range(0, len(p)-1):
			line = (p[i], p[i+1]) 
			d2 = hdist(line, point)
			if (d2<cd):
				cd = d2
		return cd

	def contains(self, room):
		for point in room.points:
			if (self.is_point_inside(point)):
				return True

		return False

	def add_gates(self, room):
		
		p1 = self.points
		p2 = room.points
		for i in range(0, len(p1)-1):
			line1 = (p1[i], p1[i+1]) 
			for j in range(0, len(p2)-1):
				line2 = (p2[j], p2[j+1]) 
				cond, wall = is_gate(line2, line1)
				if (cond):
					self.gates.append((room, wall))

	def set_as_root(self, queue, collector):
		self.visited = True
		for room, wall in self.gates:
			if (not room.visited):
				if (collector.contained_in == self):
					pos = collector.pos
				else:
					pos = self.pos
				distance = dist(pos, room.pos)
				walk = self.walk + distance
				if (walk < room.walk):
					room.walk = walk
					room.uplink = self

		# select next room
		if (len(queue)>0):
			queue.sort(key=lambda x: x.walk)
			next_room = queue.pop(0)
			next_room.set_as_root(queue, collector)

	# Reporting Room
	def report(self):
		txt = ""
		p2x2 = 0
		p2x1 = 0
		p1x2 = 0
		p1x1 = 0

		p1x1_r = 0
		p1x1_l = 0
		p1x2_r = 0
		p1x2_l = 0

		w = default_panel_width
		h = default_panel_height

		for panel in self.panels:
			if (panel.size == (2,2)):
				p2x2 += 1
			if (panel.size == (2,1)):
				p2x1 += 1
			if (panel.size == (1,2)):
				p1x2 += 1
				if (panel.side == 0 or panel.side == 2):
					p1x2_r += 1
				else:
					p1x2_l += 1

			if (panel.size == (1,1)):
				p1x1 += 1
				if (panel.side == 0 or panel.side == 2):
					p1x1_r += 1
				else:
					p1x1_l += 1

		area = self.area * scale * scale	
		active_area = w*h*(4*p2x2 + 2*p2x1 + 2*p1x2 + p1x1)/10000
		active_ratio = 100*active_area/area

		txt += "Room area: %.4g m2 \n" % area
		txt += "Active area: %.4g m2 (%.4g%%)\n" % (active_area, active_ratio)
		txt += "  %5d panels %dx%d cm\n" % (p2x2, 2*w, 2*h) 
		txt += "  %5d panels %dx%d cm\n" % (p2x1, 2*w, h) 
		txt += "  %5d panels %dx%d cm - " % (p1x2, w, 2*h) 
		txt += " %d left, %d right\n" % (p1x2_r, p1x2_l)
		txt += "  %5d panels %dx%d cm - " % (p1x1, w, h) 
		txt += " %d left, %d right\n" % (p1x1_r, p1x1_l)

		return (txt, area, active_area, 
			(p2x2,p2x1,p1x2,p1x1,p1x1_l,p1x1_r,p1x2_l,p1x2_r))


	def draw(self, msp):
		
		self.arrangement.draw_grid(msp)

		write_text(msp, "Room %d" % self.pindex, self.pos)

		for panel in self.panels:
			panel.draw(msp)
			#       <<<  MODIFIED LINE
			panel.draw_profile(msp)


class Model(threading.Thread):
	def __init__(self, output):
		super(Model, self).__init__()
		self.rooms = list()
		self.collectors = list()
		self.zone = list()
		self.output = output
		self.best_list = list()

	def new_layer(self, layer_name, color):
		attr = {'linetype': 'CONTINUOUS', 'color': color}
		self.doc.layers.new(name=layer_name, dxfattribs=attr)
		

	def create_layers(self):
		self.new_layer(layer_text, text_color)
		self.new_layer(layer_box, box_color)
		self.new_layer(layer_panel, 0)
		self.new_layer(layer_panelp, 0)
		self.new_layer(layer_link, 0)

		#self.doc.layers.get(layer_box).off()

	def find_gates(self):
		
		for room1 in self.processed:
			for room2 in self.processed:
				if (room1 != room2):
					room1.add_gates(room2)

	def collector_side(self):

		for room in self.processed:
			if (not room.collector):
				self.output.print("CRITICAL: Room %d disconnected\n" % room.index)
				continue

			cltr = room.collector
			(vx, vy) = (cltr.pos[0]-room.pos[0], 
							cltr.pos[1]-room.pos[1])

			if (vx>=0):
				room.clt_xside = RIGHT
			else:
				room.clt_xside = LEFT

			if (vy>=0):
				room.clt_yside = TOP
			else:
				room.clt_yside = BOTTOM

	def route(self):

		# reverse path from rooms
		for room in self.processed:
			#print(room.links)
			pass


	def create_trees(self):

		# create trees
		self.find_gates()
		for room in self.processed:
			room.links = list()
			room.zone = None

		zone = 1
		for collector in self.collectors:
			collector.is_leader = False

			for room in self.processed:
				room.visited = False
				room.uplink = None
				room.walk = MAX_DIST

			root = collector.contained_in
			root.walk = 0
			root.uplink = root
			
			root.set_as_root(self.processed.copy(), collector)

			leader = None
			for room in self.processed:

				# create new zone for unlinked collectors
				if ((not room.zone) and room.walk<MAX_DIST):
					if (not collector.is_leader):
						collector.is_leader = True
						collector.zone_num = zone
						collector.number = 1
						collector.name = 'C' + str(zone) + '+1'
						zone += 1
					room.zone = collector
				else:
					if (room.zone):
						leader = room.zone
 
				link_item = (collector, room.walk, room.uplink)
				room.links.append(link_item)

			if (not collector.is_leader):
				if (leader):
					collector.zone_num = leader.zone_num
					leader.number += 1
					collector.number = leader.number
					collector.name = 'C' + str(leader.zone_num)
					collector.name += '+' + str(leader.number)
				else:
					collector.name ="unassigned"
					collector.zone_num = 0
					collector.number = 0
					

		self.best_dist = MAX_DIST
		for collector in self.collectors:
			collector.freespace = feeds_per_collector 
			collector.items = list()

		self.processed.sort(key=lambda x: x.links[0][1], reverse=True)

		# trim distance vectors
		for room in self.processed:
			room.links.sort(key=lambda x: x[1])
			if (room.links[0][1]> max_clt_distance):
				self.output.print(
					"No collectors from Room %d, " % room.pindex)
				self.output.print("ignoring room")
				self.processed.remove(room)

		bound = 0
		for room in reversed(self.processed):
			room.bound = bound
			bound += room.links[0][1]
			#print(room.pindex, room.bound, room.links[0][1])

		for room in self.processed:

			for i, link in enumerate(room.links):
				if (link[1]>max_clt_distance 
					or i>=max_clt_break):
					break

			if (i+1 < len(room.links)):
				del room.links[i:]



	def run(self):
		global font_size
		global scale, tolerance
		global default_panel_width
		global default_panel_height
		global default_search_tol
		global default_hatch_width
		global default_hatch_height
		global default_min_dist
		global default_min_dist2
		global default_wall_depth
		global default_max_clt_distance
		global panel_width 
		global panel_height 
		global search_tol 
		global hatch_width
		global hatch_height
		global min_dist
		global min_dist2
		global wall_depth
		global max_clt_distance
 
		global tot_iterations, max_iterations

		scale = self.scale

		tolerance    = default_tolerance/scale
		font_size  = default_font_size/scale

		panel_width = default_panel_width/scale
		panel_height = default_panel_height/scale
		search_tol = default_search_tol/scale
		hatch_width = default_hatch_width/scale
		hatch_height = default_hatch_height/scale
		min_dist = default_min_dist/scale
		min_dist2 = default_min_dist2/scale
		wall_depth = default_wall_depth/scale
		max_clt_distance = default_max_clt_distance/scale

		Room.index = 1
		self.create_layers()

		for e in self.msp.query('*[layer=="%s"]' % self.inputlayer):
			if (e.dxftype() != 'LWPOLYLINE'):
				wstr = "WARNING: layer contains non-polyline: %s\n" % e.dxftype()
				self.textinfo.insert(END, wstr)

		searchstr = 'LWPOLYLINE[layer=="'+self.inputlayer+'"]'
		query = self.msp.query(searchstr)
		if (len(query) == 0):
			wstr = "WARNING: layer %s does not contain polylines\n" % self.inputlayer
			self.output.print(END, wstr)

		# Create list of rooms
		for poly in query:
			room = Room(poly, self.output)
			self.rooms.append(room)
			room.error = False
			if (len(room.errorstr)>0):
				self.textinfo.insert(END,room.errorstr)
				room.error = True
			else:
				area = scale * scale * room.area
				if (area > max_room_area):
					wstr = "ABORT: Zone %d larger than %d m2\n" % (room.index, 
						max_room_area)
					wstr += "Consider splitting area \n\n"
					self.output.print(wstr)
					room.errorstr = wstr
					room.error = True
	
		# get valid rooms
		self.valid_rooms = list()
		for room in self.rooms:
			if (not room.error):
				self.valid_rooms.append(room)
			if (room.color == collector_color):
				self.collectors.append(room)
				room.is_collector = True
			else:
				room.is_collector = False
					
		# check if collectors exist
		if (not self.collectors):
			wstr = "ABORT: No collectors found"
			self.output.print(wstr)
			return

		# check if an area is contained in a room
		self.valid_rooms.sort(key=lambda room: room.ax)	
		room = self.valid_rooms
		for i in range(len(room)):
			j=i+1
			while (j<len(room) and room[j].ax < room[i].bx):
				if (room[i].contains(room[j]) or 
					room[j].contains(room[i])):
					if (room[i].area > room[j].area):
						room[i].obstacles.append(room[j])
						room[j].contained_in = room[i]
					else:
						room[j].obstacles.append(room[i])
						room[i].contained_in = room[j]
				j += 1
	
		# check if the room is too small to be processed
		self.processed = list()
		pindex = 1
		for room in self.valid_rooms:
			area = scale * scale * room.area
			if (room.contained_in == None):
				if  (area < min_room_area):
					wstr = "WARNING: area less than %d m2: " % min_room_area
					wstr += "Consider changing scale!\n"
					self.output.print(wstr)
					room.errorstr = wstr
					room.error = True
				else:
					if (not room.is_collector):
						room.pindex = pindex
						pindex += 1
						self.processed.append(room)

	
		self.output.print("Detected %d rooms\n" % len(self.processed))
		self.output.print("Detected %d collectors\n" % len(self.collectors))

		# Check if enough collectors
		w = panel_width/100
		h = panel_height/100
		tot_area = 0
		for room in self.processed:
			room.feeds = ceil(room.area/(w*h)/area_per_feed_m2*target_eff)
			tot_area += room.area

		full_cover_feeds = self.full_cover_feeds = tot_area/(w*h)/area_per_feed_m2
		needed_feeds = self.needed_feeds = ceil(target_eff * full_cover_feeds)
		available_feeds = feeds_per_collector * len(self.collectors)
		self.output.print("Available pipes %g\n" % available_feeds)
		self.output.print("Estimated pipes for 70%% cover: %d\n" % needed_feeds)
		self.output.print("Estimated pipes for 100%% cover: %d\n" % full_cover_feeds)
		if (needed_feeds > available_feeds):
			self.output.print("ABORT: Too few collectors\n")
			return

		if (full_cover_feeds > available_feeds):
			self.output.print("WARNING: Low number of collectors\n")


		################################################################
		self.create_trees()


		################################################################

		#  Mapping rooms to collectors

		self.processed.append(None)    ;# Add sentinel
		room_iter = iter(self.processed)
		tot_iterations = 0
		self.found_one = False
		self.output.print("Linking Rooms:")
		self.connect_rooms(room_iter, 0)
		self.output.print("\n")
		self.processed.pop()           ;# Remove sentinel
		if (not self.found_one):
			self.output.print("CRITICAL: Could not connect rooms\n")

		#self.draw_uplinks()
		#print("Done allocating collectors")
		#self.draw_trees(self.collectors[3])

		# Determine which side is collector in each room
		self.collector_side()

		################################################################

		# allocating panels in room	
		self.output.print("Processing Room:")
		for room in self.processed:
			self.output.print("%d " % room.pindex)
			room.alloc_panels()
			room.draw(self.msp)
		self.output.print("\n")


		# find attachment points of dorsals
		self.dorsals = list()
		for room in self.processed:
			room_dors = room.arrangement.dorsals
			mode = room.arrangement.alloc_mode
			self.dorsals += room_dors
			uplink_dist = MAX_DIST
			for dorsal in room_dors:
				# dorsal.cltrs = list()
				if (mode==0):
					dorsal.pos = dorsal.attach
				else:
					dorsal.pos = (dorsal.attach[1], dorsal.attach[0])

				d = dist(dorsal.pos, room.uplink.pos)
				if (d <= uplink_dist):
					uplink_dist = d
					room.attachment = dorsal.pos

		print("Attachment done")

		## drawing connections
		self.draw_links2()
		#for collector in self.collectors:
		#	self.draw_trees(collector)
		# self.draw_gates()
		print("Links done")

		# summary
		# self.output.clear()
		summary = self.print_report()
		self.output.print(summary)
		f = open(self.outname+".txt", "w")
		print(summary, file = f)

		if (os.path.isfile(self.outname) and ask_for_write==True):
			if askyesno("Warning", "File 'leo' already exists: Overwrite?"):
				self.doc.saveas(self.outname)
		else:
			self.doc.saveas(self.outname)

		# save data in XLS
		self.save_in_xls()

		print("DONE")

	def draw_links(self):	
		# draw connections
		for collector, items in self.best_list:
			for room in items:
				if (len(room.panels) == 0):
					continue

				pos = room.attachment
				while (room != collector.contained_in):
					(p1, p2) = room.wall(room.uplink)
					med = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
					pline = (pos, med)
					pl = self.msp.add_lwpolyline(pline)
					pl.dxf.layer = layer_panel
					pl.dxf.color = 4
					pos = med
					room = room.uplink
				
				pline = (pos, collector.pos)
				pl = self.msp.add_lwpolyline(pline)
				pl.dxf.layer = layer_panel
				pl.dxf.color = 4

	def draw_links2(self):	
		# draw connections
		for collector, items in self.best_list:

			for room in items:
				if (len(room.panels) == 0):
					continue

				pos = room.pos
				while (room != collector.contained_in):
					med = room.pos
					pline = (pos, med)
					pl = self.msp.add_lwpolyline(pline)
					pl.dxf.layer = layer_panel
					pl.dxf.color = 4
					pos = med
					room = room.uplink
				
				pline = (pos, collector.pos)
				pl = self.msp.add_lwpolyline(pline)
				pl.dxf.layer = layer_panel
				pl.dxf.color = 4

	def draw_trees(self, collector):

		for room in self.processed:

			uplink = None
			for item in room.links:
				if (collector == item[0]):
					cltr, walk, uplink = item
					break

			if (not uplink):
				continue

			(x0, y0) = room.pos
			pl = self.msp.add_circle(room.pos,2*search_tol)
			pl.dxf.layer = layer_link
			pl.dxf.color = 1

			(x1, y1) = uplink.pos
			pline = ((x0,y0), (x1,y1))
			pl = self.msp.add_lwpolyline(pline)
			pl.dxf.layer = layer_link
			pl.dxf.color = 1
			pl = self.msp.add_circle(room.uplink.pos,2*search_tol)
			pl.dxf.layer = layer_link
			pl.dxf.color = 1

	def draw_uplinks(self):

		for room in self.processed:

			if (not room.uplink):
				continue

			(x0, y0) = room.pos
			pl = self.msp.add_circle(room.pos,2*search_tol)
			pl.dxf.layer = layer_link
			pl.dxf.color = 1

			(x1, y1) = room.uplink.pos
			pline = ((x0,y0), (x1,y1))
			pl = self.msp.add_lwpolyline(pline)
			pl.dxf.layer = layer_link
			pl.dxf.color = 1
			pl = self.msp.add_circle(room.uplink.pos,2*search_tol)
			pl.dxf.layer = layer_link
			pl.dxf.color = 1


	def draw_gates(self):

		for room in self.processed:
			for newroom, wall in room.gates:
				pl = self.msp.add_lwpolyline(wall)
				pl.dxf.layer = layer_link
				pl.dxf.color = 6
				pline = (room.pos, newroom.pos)
				pl = self.msp.add_lwpolyline(pline)
				pl.dxf.layer = layer_link
				pl.dxf.color = 5

				pl = self.msp.add_circle(room.pos,4*search_tol)
				pl.dxf.layer = layer_link
				pl.dxf.color = 5

	# Connect rooms to collectors using branch-and-bound
	def connect_rooms(self, room_iter, partial):

		global tot_iterations, max_iterations

		# Check if time to give up
		if (tot_iterations % 100e3 == 0):
			self.output.print("#")
		tot_iterations += 1
		if (tot_iterations > max_iterations):
			return

		room = next(room_iter)

		# Terminal case
		if (room == None):
			if (partial < self.best_dist):
				# Found solution
				self.found_one = True

				self.best_dist = partial
				self.best_list = list()
				ir = iter(self.processed)
				while (x:=next(ir)) != None:
					x.downlinks = list()
					x.uplink = x._uplink
					x.collector = x._collector

				for collector in self.collectors:
					for room in collector.items:
						room.uplink.downlinks.append(room)
					item = (collector, copy(collector.items))
					self.best_list.append(item)
				return

		# Recursive cases
		for link in room.links:
			collector, room_dist, uplink = link
			new_partial = partial + room_dist
			if (new_partial+room.bound<self.best_dist and 
				collector.freespace>=room.feeds):
				collector.items.append(room)
				collector.freespace -= room.feeds
				room._uplink = uplink
				room._collector = collector
				self.connect_rooms(copy(room_iter), new_partial)
				collector.items.remove(room)
				collector.freespace += room.feeds
					
	def print_report(self):
		
		txt = "\n ------- Room Report ----------\n\n"

		area = 0 
		active_area = 0 
		p2x2 = 0
		p2x1 = 0
		p1x2 = 0
		p1x2_l = 0
		p1x2_r = 0
		p1x1 = 0
		p1x1_l = 0
		p1x1_r = 0
		w = default_panel_width
		h = default_panel_height
		failed_rooms = 0
		feeds = 0
		for room in self.processed:

			if (len(room.errorstr)>0):
				failed_rooms += 1
				continue

			txt += "Room %d  --------- \n" % room.pindex
			roomtxt, rarea, ractive, panel_count = room.report()
			area += rarea
			active_area += ractive
			txt += roomtxt + "\n"
			p2x2 += panel_count[0]
			p2x1 += panel_count[1]
			room.panels_200x120 = panel_count[0]
			room.panels_200x60 = panel_count[1]

			p1x2 += panel_count[2]
			p1x1 += panel_count[3]
			room.panels_100x120 = panel_count[2]
			room.panels_100x60 = panel_count[3]

			p1x1_l += panel_count[4]
			p1x1_r += panel_count[5]
			p1x2_l += panel_count[6]
			p1x2_r += panel_count[7]
			room.actual_feeds = ceil(ractive/(w*h)/area_per_feed_m2)
			feeds += room.actual_feeds
			
		self.area = area
		self.active_area = active_area		
		self.feeds = feeds
	
		# Summary of all areas
		smtxt =  "\n\nTotal rooms %d  (%d failed)\n" % (len(self.processed), failed_rooms)
		smtxt += "Total collectors %d\n" % (len(self.collectors))
		smtxt += "Total area %.5g m2\n" % area
		smtxt += "Total active area %.5g m2" % active_area
		smtxt += " (%.4g %%)\n" % (100*active_area/area)
		smtxt += "Total pipes %d\n" % self.feeds
		smtxt += "  %5d panels %dx%d cm\n" % (p2x2, 2*w, 2*h) 
		smtxt += "  %5d panels %dx%d cm\n" % (p2x1, 2*w, h) 
		smtxt += "  %5d panels %dx%d cm - " % (p1x2, w, 2*h)
		smtxt += "  %d left, %d right\n" % (p1x2_l, p1x2_r)
		smtxt += "  %5d panels %dx%d cm - " % (p1x1, w, h) 
		smtxt += "  %d left, %d right\n" % (p1x1_l, p1x1_r)
		smtxt += "\n> requirements:\n"
		p2x2_cut = min(p1x2_r,p1x2_l) + abs(p1x2_r-p1x2_l)
		self.panels_200x120 = p2x2_tot = p2x2 + p2x2_cut 
		p2x2_spr = abs(p1x2_r-p1x2_l)
		smtxt += "  %d panels %dx%d, \n" % (p2x2_tot, 2*w, 2*h)
		smtxt += "    of which %d to cut and %d halves spares\n" % (p2x2_cut, p2x2_spr)
		p1x1_cut = min(p1x1_r,p1x1_l) + abs(p1x1_r-p1x1_l)
		self.panels_200x60 = p1x1_tot = p1x1 + p1x1_cut 
		p1x1_spr = abs(p1x1_r-p1x1_l)
		smtxt += "  %d panels %dx%d, \n" % (p1x1_tot, 2*w, 2*h)
		smtxt += "    of which %d to cut and %d halves spares\n" % (p1x1_cut, p1x1_spr) 

		return smtxt + txt

	def save_in_xls(self):
		wb = openpyxl.load_workbook(xlsx_template)
		ws1 = wb[sheet_template_1]
		ws2 = wb[sheet_template_2]
		ws3 = wb[sheet_template_3]

		no_collectors = len(self.collectors)

		# copy total area
		ws1['D3'] = self.area
		ws2['D3'] = self.area
		ws3['D3'] = self.area
		ws1['D4'] = self.area
		ws2['D4'] = self.area
		ws3['D4'] = self.area

		# copy total coverage
		ws1['C3'] = self.active_area
		ws2['C3'] = self.active_area
		ws3['C3'] = self.active_area
		ws1['C4'] = self.active_area
		ws2['C4'] = self.active_area
		ws3['C4'] = self.active_area

		# copy total panels
		ws1['F3'] = ws1['F4'] = self.panels_200x120
		ws1['F3'] = ws1['F4'] = self.panels_200x120
		ws2['F3'] = ws2['F4'] = self.panels_200x120
		ws2['F3'] = ws2['F4'] = self.panels_200x120
		ws3['F3'] = ws3['F4'] = self.panels_200x120
		ws3['F3'] = ws3['F4'] = self.panels_200x120

		ws1['G3'] = ws1['G4'] = self.panels_200x60
		ws1['G3'] = ws1['G4'] = self.panels_200x60
		ws2['G3'] = ws2['G4'] = self.panels_200x60
		ws2['G3'] = ws2['G4'] = self.panels_200x60
		ws3['G3'] = ws3['G4'] = self.panels_200x60
		ws3['G3'] = ws3['G4'] = self.panels_200x60

		# copy number of feeds
		ws1['H3'] = ws1['H4'] = self.feeds
		ws1['H3'] = ws1['H4'] = self.feeds
		ws2['H3'] = ws2['H4'] = self.feeds
		ws2['H3'] = ws2['H4'] = self.feeds
		ws3['H3'] = ws3['H4'] = self.feeds
		ws3['H3'] = ws3['H4'] = self.feeds

		# copy number of collectors 
		ws1['I3'] = ws1['I4'] = no_collectors 
		ws1['I3'] = ws1['I4'] = no_collectors 
		ws2['I3'] = ws2['I4'] = no_collectors 
		ws2['I3'] = ws2['I4'] = no_collectors 
		ws3['I3'] = ws3['I4'] = no_collectors 
		ws3['I3'] = ws3['I4'] = no_collectors 

		if show_panel_list:
			ws = wb.create_sheet(sheet_breakdown)

			# header
			ws['B3'] = "Zone"
			ws['C3'] = "Collector"
			ws['D3'] = "Room"
			ws['E3'] = "Panels 200x120"
			ws['F3'] = "Panels 200x60"
			ws['G3'] = "Panels 100x120"
			ws['H3'] = "Panels 100x60"

			ws.column_dimensions['B'].width = 20
			ws.column_dimensions['C'].width = 10
			ws.column_dimensions['D'].width = 10
			ws.column_dimensions['E'].width = 20
			ws.column_dimensions['F'].width = 20
			ws.column_dimensions['G'].width = 20
			ws.column_dimensions['H'].width = 20

			self.processed.sort(key=lambda x: 
				(x.collector.zone_num, x.collector.number, x.pindex))

			zone = 0
			index = 4
			for room in self.processed:

				while (room.collector.zone_num>zone):
					zone += 1
					pos = 'B' + str(index)
					ws[pos] = "Zone %d" % zone

				pos = 'C' + str(index)
				ws[pos] = room.collector.name
				
				pos = 'D' + str(index)
				ws[pos] = room.pindex

				pos = 'E' + str(index)
				ws[pos] = room.panels_200x120

				pos = 'F' + str(index)
				ws[pos] = room.panels_200x60

				pos = 'G' + str(index)
				ws[pos] = room.panels_100x120

				pos = 'H' + str(index)
				ws[pos] = room.panels_100x60

				#ws[pos_area].number_format = "0.00"
				index += 1

		out = self.filename[:-4] + ".xlsx"	
		wb.save(out)


class App:

	def __init__(self):
		self.loaded = False
		self.queue = queue.Queue()
		self.model = None

		self.root = Tk()
		root = self.root
		#root.geometry('500x300')
		root.title("Eurotherm Leonardo Planner")
		root.resizable(width=False, height=False)

		# Control section
		ctlname = Label(root, text="Control")
		ctlname.grid(row=0, column=0, padx=(25,0), pady=(10,0), sticky="w")

		ctl = Frame(root)
		self.ctl = ctl
		ctl.config(borderwidth=1, relief='ridge')
		ctl.grid(row=1, column=0, padx=(25,25), pady=(0,20))

		button = Button(ctl, text="Open", width=5, command=self.search)
		button.grid(row=1, column=1, sticky="e")

		self.text = StringVar()
		flabel = Label(ctl, textvariable=self.text, width=30, anchor="w")
		flabel.config(borderwidth=1, relief='solid')
		flabel.grid(row=1, column=0, padx=(10,30), pady=(20,10))

		self.text1 = StringVar()
		flabel = Label(ctl, textvariable=self.text1, width=30, anchor="w")
		flabel.config(borderwidth=1, relief='solid')
		flabel.grid(row=2, column=0, padx=(10,30), pady=(10,20))

		self.var = StringVar() # variable for select layer menu

		self.button1 = Button(ctl, text="Build", width=5, command=self.create_model, pady=5)
		self.button1.grid(row=3, column=1, pady=(30,10))

		# Parameters section
		parname = Label(root, text="Settings")
		parname.grid(row=2, column=0, padx=(25,0), pady=(1,0), sticky="w")
		self.params = params = Frame(root)
		params.config(borderwidth=1, relief='ridge')
		params.grid(row=3, column=0, sticky="ew", padx=(25,25), pady=(0,2))

		Label(params, text="A drawing unit in cm").grid(row=0, column=0, sticky="w")
		self.entry1 = Entry(params, justify='right', width=10)
		self.entry1.grid(row=0, column=1, sticky="w")
		self.entry1.insert(END, str(default_scale))

		#Label(params, text="zone cost (m2)").grid(row=1, column=0, sticky="w")
		#self.entry2 = Entry(params, justify='right', width=10)
		#self.entry2.grid(row=1, column=1)
		#self.entry2.insert(END, str(default_zone_cost))

		#Label(params, text="transversal cuts").grid(row=2, column=0, sticky="e")
		#self.tcuts = IntVar()
		#self.entry3 = Checkbutton(params, variable=self.tcuts)
		#self.entry3.grid(row=2, column=1)

		# Info Section
		ctlname = Label(root, text="Report")
		ctlname.grid(row=4, column=0, padx=(25,0), pady=(10,0), sticky="w")

		self.textinfo = Text(root, height=20, width=58)
		self.textinfo.config(borderwidth=1, relief='ridge')
		self.textinfo.grid(row=5, column=0, pady=(0,15)) 
		#sb = Scrollbar(root, command=self.textinfo.yview)
		#sb.grid(row=3, column=1, sticky="nsw")


		self.reset()
		self.root.mainloop()

	def print(self, text):
		self.textinfo.insert(END, text)

	def clear(self):
		self.textinfo.delete('1.0', END)

	def search(self,event=None):
		self.filename = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
		self.loadfile()

	def reset(self):
		self.text.set("Select DXF")
		self.text1.set("Modified DXF")
		self.button1["state"] = "disabled"
		self.textinfo.delete('1.0', END)

		if (hasattr(self,'opt')): self.opt.destroy()	
		self.var.set("Select layer")
		self.opt = OptionMenu(self.ctl, self.var,['0'])
		self.opt.config(width=26)
		self.opt.grid(row=3, column=0, padx=(10,40), sticky="w")

	def loadfile(self):
		try:
			self.doc_src = ezdxf.readfile(self.filename)
		except IOError:
			self.reset()
			return
		except ezdxf.DXFStructureError:
			self.textinfo.insert(END, 'Invalid or corrupted DXF file.')
			self.reset()
			return

		self.loaded = True

		self.text.set(self.filename)
		self.outname = self.filename[:-4]+"_leo.dxf"
		self.text1.set(self.outname)

		layers = [layer.dxf.name for layer in self.doc_src.layers]
		sel = layers[0]
		for layer in layers:
			if (layer == default_input_layer):
				sel = default_input_layer
				break

		self.opt.destroy()
		self.var.set(sel)
		self.opt = OptionMenu(self.ctl,self.var,*layers)
		self.opt.config(width=26)
		self.opt.grid(row=3, column=0, padx=(10,40), sticky="w")
		self.button1["state"] = "normal" 


	def create_model(self):

		if self.model and self.model.is_alive():
			return

		self.textinfo.delete('1.0', END)

		if (not self.loaded):
			self.textinfo(END, "File not loaded")
			return

		# create model and initialise it
		self.model = Model(self)

		# reload file
		self.doc = ezdxf.readfile(self.filename)	
		#self.model.doc = ezdxf.new(dxf_version)
		self.model.doc = self.doc     # <<<<<<<<< MODIFIED LINE <<<<<<<
		self.model.msp = self.model.doc.modelspace()
		self.model.scale = float(self.entry1.get())

		self.model.inputlayer = self.var.get()
		self.model.textinfo = self.textinfo
		self.model.outname = self.outname
		self.model.filename = self.filename

		# copy input layer from source
		#importer = Importer(self.doc, self.model.doc)
		#ents = self.doc.modelspace().query('*[layer=="%s"]' 
		#		% self.model.inputlayer)
		#importer.import_entities(ents)

		## copy blocks from panels
		source_dxf = ezdxf.readfile("panels.dxf")
		importer = Importer(source_dxf, self.model.doc)
		importer.import_block(block_blue_120x100)
		importer.import_block(block_blue_60x100)
		importer.import_block(block_green_120x100)
		importer.import_block(block_green_60x100)


		self.model.start()
	
App()

