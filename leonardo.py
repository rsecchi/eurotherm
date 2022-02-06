#!/usr/local/bin/python3

import ezdxf
import openpyxl
import queue
import threading
import numpy as np
from openpyxl.styles.borders import Border, Side
import os.path
from math import ceil, floor, sqrt
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import askyesno

# Parameter settings (values in cm)
default_scale = 0.1  # scale=100 if the drawing is in m
default_tolerance    = 1   # ignore too little variations

extra_len    = 20
zone_cost = 1
min_room_area = 1
max_room_area = 500

feeds_per_collector = 16
area_per_feed_m2 = 14.4
target_eff = 0.7

default_x_font_size  = 20
default_y_font_size  = 30

# Half panels default dimensions in cm
default_panel_width = 100
default_panel_height = 60
default_hatch_width = 15
default_hatch_height = 10

default_search_tol = 5
default_min_dist = 20
default_min_dist2 = default_min_dist*default_min_dist

default_input_layer = 'aree sapp'
layer_text   = 'Eurotherm_text'
layer_box    = 'Eurotherm_box'
layer_panel  = 'Eurotherm_panel'

text_color = 7
box_color = 8
collector_color = 1
ask_for_write = True

MAX_COST = 1000000
MAX_DIST = 1e20

RIGHT = 1
LEFT = 0
TOP = 1
BOTTOM = 0

xlsx_template = 'template.xlsx'
sheet_template = 'BoM'



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

	#cx1 = p0x + A1/(p1y-p0y)
	#cx2 = p0x + A3/(p1y-p0y)
	#cy1 = p0y + A2/(p1x-p0x)
	#cy2 = p0y + A4/(p1x-p0x)

	#if ((ax<=cx1 and cx1<=bx) or 
	#	(ax<=cx2 and cx2<=bx) or
	#	(ay<=cy1 and cy1<=by) or
	#	(ay<=cy2 and cy2<=by)):
	#	return True
	#
	#return False

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


#  v_par = <v,p> / <v,v>

def dist2(line, point):
	(xp,yp) = point
	(x0,y0),(x1,y1) = line
	
	(ux, uy) = (x1-x0, y1-y0)
	(px, py) = (xp-x0, yp-y0)
	
	u2 = ux*ux + uy*uy
	p2 = px*px + py*py
	up = ux*px + uy*py

	if (up>u2):
		return u2+p2-2*up

	if (up<=0 or u2==0):
		return p2

	return p2-up*up/u2


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

	def draw(self, msp):
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
		pl.dxf.layer = layer_panel
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
		self.pos = self._centre()
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
		n = len(p) 
		for p in self.points:
			(cx, cy) = (cx+p[0], cy+p[1])

		return (cx/n, cy/n)
		

	def _perimeter(self):
		p = self.points
		d = 0
		for i in range(0, len(p)-1):
			d += sqrt(pow(p[i+1][0]-p[i][0],2)+pow(p[i+1][1]-p[i][1],2))
		return d

	def bounding_box(self):
		self.ax = min(self.xcoord)
		self.bx = max(self.xcoord)
		self.ay = min(self.ycoord)
		self.by = max(self.ycoord)
		

	# Building Room
	def alloc_panels(self):
		global panel_height, panel_width, search_tol

		self.output.print("Processing Room %d\n" % self.index)
	
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
		x = point[0]; y = point[1]
		ints = 0

		for i in range(0, len(p)-1):
	
			if (p[i][0]==x and p[i+1][0]==x):
				if (max(p[i][1], p[i+1][1]) >= y
				  and min(p[i][1], p[i+1][1]) <=y):
					return True

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

		for panel in self.panels:
			panel.draw(msp)


class Model(threading.Thread):
	def __init__(self, output):
		super(Model, self).__init__()
		self.rooms = list()
		self.collectors = list()
		self.output = output

	def new_layer(self, layer_name, color):
		attr = {'linetype': 'CONTINUOUS', 'color': color}
		self.doc.layers.new(name=layer_name, dxfattribs=attr)
		

	def create_layers(self):
		self.new_layer(layer_text, text_color)
		self.new_layer(layer_box, box_color)
		self.new_layer(layer_panel, 0)

	def run(self):
		global x_font_size, y_font_size  
		global scale, tolerance
		global default_panel_width
		global default_panel_height
		global default_search_tol
		global default_hatch_width
		global default_hatch_height
		global default_min_dist
		global default_min_dist2
		global panel_width 
		global panel_height 
		global search_tol 
		global hatch_width
		global hatch_height
		global min_dist
		global min_dist2
 
		scale = self.scale

		tolerance    = default_tolerance/scale
		x_font_size  = default_x_font_size/scale
		y_font_size  = default_y_font_size/scale

		panel_width = default_panel_width/scale
		panel_height = default_panel_height/scale
		search_tol = default_search_tol/scale
		hatch_width = default_hatch_width/scale
		hatch_height = default_hatch_height/scale
		min_dist = default_min_dist/scale
		min_dist2 = default_min_dist2/scale

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


		# check if a room is contained in some other room
		self.valid_rooms.sort(key=lambda room: room.ax)	
		room = self.valid_rooms
		for i in range(0,len(room)):
			j=i+1
			while (j<len(room) and room[j].ax < room[i].bx):
				if room[i].contains(room[j]):
					room[i].obstacles.append(room[j])
					room[j].contained_in = room[j]
				if room[j].contains(room[i]):
					room[j].obstacles.append(room[i])
					room[i].contained_in = room[j]
				j += 1
		
		# check if the room is too small to be processed
		self.processed = list()
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
						self.processed.append(room)


		# Check if enough collectors
		w = panel_width/100
		h = panel_height/100
		tot_area = 0
		for room in self.processed:
			tot_area += room.area

		full_cover_feeds = tot_area/(w*h)/area_per_feed_m2
		needed_feeds = ceil(target_eff * full_cover_feeds)
		available_feeds = feeds_per_collector * len(self.collectors)
		self.output.print("Available water feed pipes %g\n" % available_feeds)
		self.output.print("Minimum required feed pipes: %d\n" % needed_feeds)
		if (needed_feeds > available_feeds):
			self.output.print("ABORT: Too few collectors\n")
			return

		if (full_cover_feeds > available_feeds):
			self.output.print("WARNING: Low number of collectors\n")

		# Assign collectors to rooms
		for room in self.processed:
			dist_cltr = MAX_DIST
			for cltr in self.collectors:
				(vx, vy) = (cltr.pos[0]-room.pos[0], 
								cltr.pos[1]-room.pos[1])
				d = sqrt(vx*vx+vy*vy)
				if (d<dist_cltr):
					dist_ctlr = d
					room.collector = cltr
					if (vx>=0):
						room.clt_xside = RIGHT
					else:
						room.clt_xside = LEFT

					if (vy>=0):
						room.clt_yside = TOP
					else:
						room.clt_yside = BOTTOM
			

		# allocating panels in room
		for room in self.processed:
			room.alloc_panels()
			room.draw(self.msp)

		# Now connect the Dorsals
		self.connect_dorsals()

		# summary
		# self.output.clear()
		summary = self.print_report()
		self.output.print(summary)

		if (os.path.isfile(self.outname) and ask_for_write==True):
			if askyesno("Warning", "File 'leo' already exists: Overwrite?"):
				self.doc.saveas(self.outname)
		else:
			self.doc.saveas(self.outname)


	def connect_dorsals(self):

		self.output.print("connecting dorsals\n")
		dorsals = self.dorsals = list()
		collectors = self.collectors
		self.panels = list()

		for room in self.processed:
			room_dors = room.arrangement.dorsals
			mode = room.arrangement.alloc_mode
			dorsals += room_dors
			self.panels += room_dors.panels
			for dorsal in room_dors:
				dorsal.cltrs = list()
				if (mode==0):
					dorsal.pos = dorsal.attach
				else:
					dorsal.pos = (dorsal.attach[1], dorsal.attach[0])


		for collector in collectors:
			collector.items = list()

		np = len(dorsals)
		cap = len(collectors) * feeds_per_collector
		free = cap - np

		if (free<0):
			print("ABORT: Not enough collectors")
			return

		for dorsal in dorsals:
			dorsal.bogus = False

		for i in range(free):
			p = type('NoItem', (), {})()
			p.bogus = True
			dorsals.append(p)


    	# alloc to first free
		dors = iter(self.dorsals)
		for c in self.collectors:
			for i in range(0, feeds_per_collector):
				p = next(dors)
				c.items.append(p)
				p.cltr = c

		done = False
		while not done:
			done = True
			for p1 in dorsals:
				for p2 in dorsals:
					if (p1.bogus and p2.bogus):
						continue

					if ((p1.bogus and dist(p2.pos, p1.cltr.pos) < dist(p2.pos, p2.cltr.pos)) or
                       (p2.bogus and dist(p1.pos, p2.cltr.pos) < dist(p1.pos, p1.cltr.pos)) or
                       ((not p1.bogus) and (not p2.bogus) and
                       (dist(p1.pos, p2.cltr.pos) + dist(p2.pos, p1.cltr.pos) <
                       dist(p1.pos, p1.cltr.pos) + dist(p2.pos, p2.cltr.pos)))):
						p1.cltr.items.remove(p1)
						p2.cltr.items.remove(p2)
						p1.cltr, p2.cltr = p2.cltr, p1.cltr
						p1.cltr.items.append(p1)
						p2.cltr.items.append(p2)
		
		for c in self.collectors:
			for item in c.items:
				if item.bogus: continue
				pline = [c.pos, item.pos]
				pl = self.msp.add_lwpolyline(pline)
				pl.dxf.layer = layer_panel
				pl.dxf.color = 0

	def print_report(self):
		
		txt = "\n ------- Zone Report ----------\n\n"

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
		for room in self.processed:

			if (len(room.errorstr)>0):
				failed_rooms += 1
				continue

			txt += "Zone%d  --------- \n" % room.index
			roomtxt, rarea, ractive, panel_count = room.report()
			area += rarea
			active_area += ractive
			txt += roomtxt + "\n"
			p2x2 += panel_count[0]
			p2x1 += panel_count[1]
			p1x2 += panel_count[2]
			p1x1 += panel_count[3]
			p1x1_l += panel_count[4]
			p1x1_r += panel_count[5]
			p1x2_l += panel_count[6]
			p1x2_r += panel_count[7]
			
			
		# Summary of all areas
		smtxt =  "Total rooms %d  (%d failed)\n" % (len(self.processed), failed_rooms)
		smtxt += "Total area %.5g m2\n" % area
		smtxt += "Total active area %.5g m2" % active_area
		smtxt += " (%.4g %%)\n" % (100*active_area/area)
		smtxt += "  %5d panels %dx%d cm\n" % (p2x2, 2*w, 2*h) 
		smtxt += "  %5d panels %dx%d cm\n" % (p2x1, 2*w, h) 
		smtxt += "  %5d panels %dx%d cm - " % (p1x2, w, 2*h)
		smtxt += "  %d left, %d right\n" % (p1x2_l, p1x2_r)
		smtxt += "  %5d panels %dx%d cm - " % (p1x1, w, h) 
		smtxt += "  %d left, %d right\n" % (p1x1_l, p1x1_r)
		smtxt += "\n> requirements:\n"
		p2x2_cut = min(p1x2_r,p1x2_l) + abs(p1x2_r-p1x2_l)
		p2x2_tot = p2x2 + p2x2_cut 
		p2x2_spr = abs(p1x2_r-p1x2_l)
		smtxt += "  %d panels %dx%d, \n" % (p2x2_tot, 2*w, 2*h)
		smtxt += "    of which %d to cut and %d halves spares\n" % (p2x2_cut, p2x2_spr)
		p1x1_cut = min(p1x1_r,p1x1_l) + abs(p1x1_r-p1x1_l)
		p1x1_tot = p1x1 + p1x1_cut 
		p1x1_spr = abs(p1x1_r-p1x1_l)
		smtxt += "  %d panels %dx%d, \n" % (p1x1_tot, 2*w, 2*h)
		smtxt += "    of which %d to cut and %d halves spares\n" % (p1x1_cut, p1x1_spr) 

		return smtxt + txt

class App:

	def __init__(self):
		self.loaded = False
		self.queue = queue.Queue()
		self.model = Model(self)

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

		self.textinfo = Text(root, height=10, width=58)
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
			self.doc = ezdxf.readfile(self.filename)
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

		layers = [layer.dxf.name for layer in self.doc.layers]
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
		self.textinfo.delete('1.0', END)

		if (not self.loaded):
			self.textinfo(END, "File not loaded")
			return

		# reload file
		self.model.doc = self.doc = ezdxf.readfile(self.filename)	
		self.model.msp = self.msp = self.doc.modelspace()
		self.model.scale = float(self.entry1.get())

		self.model.inputlayer = self.var.get()
		self.model.textinfo = self.textinfo
		self.model.outname = self.outname

		self.model.start()

		# Creating XLS
		#self.save_xls()
		#wb = openpyxl.Workbook()
		#ws = wb.active
		#ws.title = "Bill of Materials"
		#if (len(self.rooms)>0):
		#	self.save_crocs_xls(ws)
		#	self.save_omegas_xls(ws)
		#out = self.filename[:-4] + "_struct.xlsx"	
		#wb.save(out)


	def save_xls(self):
		wb = openpyxl.load_workbook(xlsx_template)
		ws = wb[sheet_template]

		index = 0
		for room in self.rooms:

			if (len(room.errorstr)>0):
				curr_row = str(index+6)
				index = index + 1
				pos_name = 'B' + curr_row
				pos_err = 'C' + curr_row
				ws[pos_name] = 'Zone ' + str(room.index)
				continue

			for box in room.boxes:
				curr_row = str(index+6)
				index = index + 1

				pos_name = 'B' + curr_row
				pos_paneltype = 'C' + curr_row
				pos_start_profile = 'D' + curr_row
				pos_len = 'E' + curr_row
				pos_end_profile = 'F' + curr_row
				pos_width = 'G' + curr_row
				pos_perimeter = 'H' + curr_row
				pos_omega = 'I' + curr_row

				if (len(room.boxes) == 1):
					ws[pos_name] = "Zone %d" % (room.index) 
				else:
					ws[pos_name] = "Zone %d " % (room.index) + chr(64+box.number)
					perimeter = 0.0

				if (box.number == 1):
					perimeter = room.perimeter*scale/100
				else:
					perimenter = 0.0

				width = (box.bx - box.ax)*scale
				length = (box.by - box.ay)*scale + extra_len

				ws[pos_width] = ceil(width/5)*5/100
				ws[pos_paneltype] = 'BLH'
				ws[pos_start_profile] = 'NONE'
				ws[pos_len] = round(length/5)*50
				ws[pos_start_profile] = 'NONE'
				ws[pos_end_profile] = 'NONE'
				ws[pos_perimeter] = perimeter
				ws[pos_omega] = '0.0'

				#ws[pos_area].number_format = "0.00"

		out = self.filename[:-4] + "_doghe.xlsx"	
		wb.save(out)


	
App()


