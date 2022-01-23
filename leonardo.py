#!/usr/local/bin/python3

# Cose da fare:

# Dislocazione moduli semplici 60x100
# Raggruppamento moduli semplici in moduli 
# Orientamento dei connettori
# Stanze oblique
# Colorazione dei moduli in base alla tipologia
# Impedimenti interni alla stanza: colonne e lucernari
# Salvataggio Aree e Rapporti in Excel


import ezdxf
import openpyxl
import numpy as np
from openpyxl.styles.borders import Border, Side
import os.path
from math import ceil, floor, sqrt
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import askyesno

# Parameter settings (values in cm)
default_scale = 1          # multiplier to transform in cm (scale=100 if the drawing is in m)
default_tolerance    = 1   # ignore too little variations

extra_len    = 20
zone_cost = 1

default_x_font_size  = 20
default_y_font_size  = 30

panel_width = 100
panel_height = 60
search_tol = 5

default_input_layer = 'AREE_SAPP'
layer_text   = 'Eurotherm_text'
layer_box    = 'Eurotherm_box'
layer_panel  = 'Eurotherm_panel'

text_color = 7
box_color = 8

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


# This class represents the radiating panel
# with its characteristics
class Panel:
	def __init__(self, cell, size):
		self.cell = cell
		self.xcoord = self.cell.box[0]
		self.ycoord = self.cell.box[2]
		self.width  = (self.cell.box[1] - self.xcoord) * size[0]
		self.height = (self.cell.box[3] - self.ycoord) * size[1]
		self.size = size


# Cell of the grid over which panels are lai ouut
class Cell:
	def __init__(self, pos, box):
		self.pos = pos
		self.box = box


# This class represents the grid over which the panels
# are laid out.
class Grid():

	def __init__(self):
		self.cells = list()
		self.panels = list()

	def len(self):
		return len(self.cells)

	def addcell(self, pos, box):
		self.cells.append(Cell(pos, box))

	def make_matrix(self):

		maxr = self.rows = max([c.pos[0] for c in self.cells]) + 3
		maxc = self.cols = max([c.pos[1] for c in self.cells]) + 3

		m = self.matrix = np.full((maxr, maxc), None)
		for cell in self.cells:
			m[(cell.pos[0]+1, cell.pos[1]+1)] = cell

	def alloc_strip(self, row, start):

		m = self.matrix.copy()
		panels = list()

		cost = 0
		j = row
		i = start
		while(i<self.rows-1):
			if (m[i,j] and m[i+1,j] and m[i,j+1] and m[i+1,j+1]):
				panels.append(Panel(m[i,j],(2,2)))
				i += 2
				continue
		
			if (m[i,j] and m[i+1,j] and
				(not m[i,j+1]) and (not m[i+1,j+1])):
				panels.append(Panel(m[i,j], (2,1)))
				i += 2
				cost += 1
				continue

			if ((not m[i,j]) and (not m[i+1,j]) and
				m[i,j+1] and m[i+1,j+1]):
				panels.append(Panel(m[i,j+1], (2,1)))
				i += 2
				cost += 1
				continue

			if (m[i,j] and m[i,j+1]):
				panels.append(Panel(m[i,j], (1,2)))
				cost += 1
				m[i,j] = m[i,j+1] = None

			if (m[i+1,j] and m[i+1,j+1]):
				panels.append(Panel(m[i+1,j], (1,2)))
				cost += 1
				m[i+1,j] = m[i+1,j+1] = None

			if m[i,j]:
				panels.append(Panel(m[i,j],(1,1)))
				cost += 2
			
			if m[i+1,j]:
				panels.append(Panel(m[i+1,j],(1,1)))
				cost += 2

			if m[i,j+1]:
				panels.append(Panel(m[i,j+1],(1,1)))
				cost += 2
				
			if m[i+1,j+1]:
				panels.append(Panel(m[i+1,j+1],(1,1)))
				cost += 2

			i += 2

		return panels, cost 

	def panels_alloc(self, start):
		
		panels = list()

		j = start
		cost = 0
		while(j<self.cols-1):
			local0, cost0 = self.alloc_strip(j, 0)
			local1, cost1 = self.alloc_strip(j, 1)
			if (cost0<cost1):
				panels += local0
				cost += cost0
			else:
				panels += local1
				cost += cost1
				
			j += 2
		
		return panels, cost
	
	def alloc_panels(self):
	
		self.make_matrix()

		# single dorsal
		panels0, cost0 = self.panels_alloc(0)
		panels1, cost1 = self.panels_alloc(1)

		if (cost0<cost1):
			self.panels = panels0
		else:
			self.panels = panels1
				


# This class represents the rrom described by a 
# polyline
class Room:

	index = 1

	def __init__(self, poly):

		self.index = Room.index
		Room.index = Room.index + 1
		self.ignore = False
		self.errorstr = ""

		# Scale points to get cm
		#color = poly.dxf.color
		#if (color>3 or color<2):
		#	self.ignore = True
		#	self.errorstr = "WARNING: color=%d not supported, " % color
		#	self.errorst += "ignoring Zone %d\n" % self.index
		#	return

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

		# Mirror if polyline is green
		#if (poly.dxf.color==3):
		#	self.orient = 1
		#	for i in range(0,len(self.points)):
		#		self.points[i] = (self.points[i][1], self.points[i][0])
		#	self.xcoord, self.ycoord = self.ycoord, self.xcoord


	def area(self):
		a = 0
		p = self.points
		for i in range(0, len(p)-1):
			a += (p[i+1][0]-p[i][0])*(p[i+1][1] + p[i][1])/2
		return abs(a/10000)

	def perimeter(self):
		p = self.points
		d = 0
		for i in range(0, len(p)-1):
			d += sqrt( pow(p[i+1][0]-p[i][0], 2) + pow(p[i+1][1]-p[i][1], 2))
		return d

	# Building Room
	def make_grid(self):
				
		# get bounding box
		self.ax = min(self.xcoord)
		self.bx = max(self.xcoord)
		self.ay = min(self.ycoord)
		self.by = max(self.ycoord)

		# grid for panels
		self.grid = Grid()

		# search within panel range
		for sx in range(0, panel_width, search_tol):
			for sy in range(0, panel_height, search_tol):
				local = self.grid_list(sx+self.ax, sy+self.ay)
				if (local.len() > self.grid.len()):
					self.grid = local
		

	# return a list of valid boxex from sx, sy
	def grid_list(self, sx, sy):

		boxes = Grid()		

		# Horizontal panels
		row = 0
		sax = sx
		while(sax+panel_width <= self.bx):
			say = sy
			col = 0
			while(say+panel_height <= self.by):
				pos = (row, col)
				box = (sax, sax+panel_width, say, say+panel_height)
				if self.is_box_inside(box):
					boxes.addcell(pos, box)
				say += panel_height
				col += 1

			sax += panel_width
			row += 1

		# Vertical panels
		# TBD

		return boxes


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

			
			if (x0<=x and x<=x1):
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


	# Reporting Room
	def report(self):
		pass

	# Drawing Room
	def draw_box(self, msp, box):
		ax = box[0]; bx = box[1]
		ay = box[2]; by = box[3]
		pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
		pl = msp.add_lwpolyline(pline)
		pl.dxf.layer = layer_box

	def draw_panel(self, msp, panel):
		ax = panel.xcoord; bx = ax + panel.width
		ay = panel.ycoord; by = ay + panel.height
		pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
		pl = msp.add_lwpolyline(pline)
		pl.dxf.layer = layer_panel
		

	def draw_room(self, msp):
		
		for cell in self.grid.cells:
			self.draw_box(msp, cell.box)

		for panel in self.grid.panels:
			self.draw_panel(msp, panel)


class App:

	def __init__(self):
		self.loaded = False

		self.root = Tk()
		root = self.root
		#root.geometry('500x300')
		root.title("Eurotherm Leonardo planner")
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

		self.button1 = Button(ctl, text="Build", width=5, command=self.build_model, pady=5)
		self.button1.grid(row=3, column=1, pady=(30,10))

		# Parameters section
		parname = Label(root, text="Settings")
		parname.grid(row=2, column=0, padx=(25,0), pady=(1,0), sticky="w")
		self.params = params = Frame(root)
		params.config(borderwidth=1, relief='ridge')
		params.grid(row=3, column=0, sticky="ew", padx=(25,25), pady=(0,2))

		Label(params, text="scale (100=1m)").grid(row=0, column=0, sticky="w")
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
	

	def search(self,event=None):
		self.filename = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
		self.loadfile()

	def reset(self):
		self.text.set("Select DXF File")
		self.text1.set("Modified DXF File")
		self.button1["state"] = "disabled"
		self.textinfo.delete('1.0', END)

		if (hasattr(self,'opt')): self.opt.destroy()	
		self.var.set("Select layer")
		self.opt = OptionMenu(self.ctl, self.var,['Select layer'])
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
		self.outname = self.filename[:-4]+"_sapp.dxf"
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

	def new_layer(self, layer_name, color):
		attr = {'linetype': 'CONTINUOUS', 'color': color}
		self.doc.layers.new(name=layer_name, dxfattribs=attr)
		

	def create_layers(self):
		self.new_layer(layer_text, text_color)
		self.new_layer(layer_box, box_color)
		self.new_layer(layer_panel, 0)

	def print_report(self, txt):
		txt(END, "Design Report ----------------\n\n")
		
		for room in self.rooms:

			if (len(room.errorstr)>0):
				continue

			rep = room.report()
			txt(END,"Zone%d  - surface %.3f m2\n" % (room.index, room.area()))
			txt(END,"\n")

		

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
					perimeter = room.perimeter()*scale/100
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


	def build_model(self):
		global x_font_size, y_font_size  
		global scale, tolerance

		self.textinfo.delete('1.0', END)

		if (not self.loaded):
			self.textinfo(END, "File not loaded")
			return

		scale = float(self.entry1.get())

		tolerance    = default_tolerance/scale
		x_font_size  = default_x_font_size/scale
		y_font_size  = default_y_font_size/scale

		# reload file
		self.doc = ezdxf.readfile(self.filename)	
		self.msp = self.doc.modelspace()
		Room.index = 1
		self.rooms = []

		self.create_layers()
		inputlayer = self.var.get()

		for e in self.msp.query('*[layer=="%s"]' % inputlayer):
			if (e.dxftype() != 'LWPOLYLINE'):
				wstr = "WARNING: layer contains non-polyline: %s\n" % e.dxftype()
				self.textinfo.insert(END, wstr)

		searchstr = 'LWPOLYLINE[layer=="'+inputlayer+'"]'
		query = self.msp.query(searchstr)
		if (len(query) == 0):
			wstr = "WARNING: layer %s does not contain polylines\n" % inputlayer
			self.textinfo.insert(END, wstr)

		for poly in query:
			room = Room(poly)
			room.surf = 0
			self.rooms.append(room)
			if (len(room.errorstr)>0):
				self.textinfo.insert(END,room.errorstr)
			else:
				room.make_grid()
				room.grid.alloc_panels()
				if (room.area() < zone_cost):
					wstr = "WARNING: area less than %d m2: " % zone_cost
					wstr += "Consider changing scale!\n"
					self.textinfo.insert(END, wstr)
				room.draw_room(self.msp)

		self.print_report(self.textinfo.insert)

		if (os.path.isfile(self.outname)):
			if askyesno("Warning", "File 'sapp' already exists: Overwrite?"):
				self.doc.saveas(self.outname)
		else:
				self.doc.saveas(self.outname)

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

	
App()


