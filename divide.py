#!/usr/local/bin/python3

import ezdxf
from math import ceil, floor
from tkinter import *
from tkinter import filedialog

# Parameter settings
tolerance    = 1         # ignore too little variation
width_doga   = 20
space_omega  = 60
croc_first   = 15
croc_second  = 60
croc_maxd    = 120
croc_tol     = 10

layer_text   = 'Eurotherm_text'
x_font_size  = 10
y_font_size  = 20
layer_box    = 'Eurotherm_box'
layer_croc   = 'Eurotherm_crocodile'
layer_omega   = 'Eurotherm_omega'


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


class Croc:
	def __init__(self, x1, x2, y):
		self.x1 = x1
		self.x2 = x2
		self.y  = y 

	def fit(self, y1, y2):
		tol = croc_tol
		return (self.y>=y1 and self.y<=y2)


	def extend_right(self, x2):
		self.x2 = x2

class Zone:
	def __init__(self, ax, ay, bx, by):
		self.ax = min(ax, bx)
		self.bx = max(ax, bx)
		self.ay = min(ay, by)
		self.by = max(ay, by)
		self.TR = (max(ax, bx), max(ay, by))
		self.TL = (min(ax, bx), max(ay, by))
		self.BR = (max(ax, bx), min(ay, by))
		self.BL = (min(ax, bx), min(ay, by))

	def pline(self, orient):
		ax = self.ax; bx = self.bx
		ay = self.ay; by = self.by
		if (orient == 0):
			return [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
		else:	
			return [(ay,ax),(by,ax),(by,bx),(ay,bx),(ay,ax)]

	def extend_right(self, coord):
		self.TR = (coord, self.TR[1])
		self.BR = (coord, self.BR[1])
		self.bx = coord

	def extend_crocs(self, crocs, y1, y2):
		crocs_list = list()
		for c in crocs:
			print("BOX",self.ax,y1,y2)
			if (c.x2 == self.ax and c.y>=y1 and c.y<=y2):
				print("exte",c.x1,c.x2,c.y)
				c.extend_right(self.bx)
				crocs_list.append(c)
		return crocs_list

	def draw_box(self, msp, orient):
		pl = msp.add_lwpolyline(self.pline(orient))
		pl.dxf.layer = layer_box

	def draw_text(self, msp, ind, subind, orient):
		
		scale = (x_font_size/2, y_font_size/4)
		text = 'ZONE' + str(ind) + chr(65+subind) 
		if (orient==0):
			pos = ((self.ax+self.bx)/2, (self.ay+self.by)/2)
		else:
			pos = ((self.ay+self.by)/2, (self.ax+self.bx)/2)
	
		writedxf(msp, text, pos, scale)


class Room:

	def __init__(self, poly):

		tol = tolerance
		self.orient = 0
		self.boxes = list()
		self.coord = list()
		self.crocs = list()
		self.omegas = list()

		self.index = Room.index
		Room.index = Room.index + 1

		self.points = list(poly.vertices())

		# Add a final point to closed polylines
		p = self.points
		if (poly.is_closed):
			self.points.append((p[0][0], p[0][1]))

		# Check if the polyine is open with large final gap
		n = len(p)-1
		if (abs(p[0][0]-p[n][0])>tol or abs(p[0][1]-p[n][1])>tol):
			print("Error: Open polyline") 
			return

		# Straighten up walls
		finished = False
		while not finished:
			for i in range(1, len(p)):
				if (abs(p[i][0]-p[i-1][0]) < tol):
					p[i] = (p[i-1][0], p[i][1])

				if (abs(p[i][1]-p[i-1][1]) < tol):
					p[i] = (p[i][0], p[i-1][1])

			if (p[0][0]==p[n][0] and p[0][1]==p[n][1]):
				finished = True
			else:
				p[0] = p[n]

		#for i in range(1, len(p)):
		#	print(abs(p[i][0]-p[i-1][0]), abs(p[i][1]-p[i-1][1]))

		# Projections of coordinates on x and y
		self.xcoord = sorted(set([p[0] for p in poly.vertices()]))	
		self.ycoord = sorted(set([p[1] for p in poly.vertices()]))	

		# Mirror if polyline is green
		if (poly.dxf.color==3):
			self.orient = 1
			for i in range(0,len(self.points)):
				self.points[i] = (self.points[i][1], self.points[i][0])
			self.xcoord, self.ycoord = self.ycoord, self.xcoord

		self.get_boxes()
		#self.get_crocs()
		self.simple_crocs()
		self.get_omegas()


	# This function divides a polyline into boxes
	# and returns the list of boxes
	def get_boxes(self):
		
		tol = tolerance
		boxes = self.boxes
		p = self.points
		xc = self.xcoord

		for i in range(0,len(xc)-1):
			ax = xc[i]
			bx = xc[i+1]
			mid = (ax + bx)/2

			lr = list()
			ll = list()

			for j in range(0, len(p)-1):
				if (p[j][0] < p[j+1][0]):
					x0, y0 = p[j][0], p[j][1]
					x1, y1 = p[j+1][0], p[j+1][1]
				else:
					x0, y0 = p[j+1][0], p[j+1][1]
					x1, y1 = p[j][0], p[j][1]
					
				if (x0<mid and mid<x1):
					delta = x1 - x0
					ay = (y0*(x1-ax) - y1*(x0-ax))/delta
					by = (y0*(x1-bx) - y1*(x0-bx))/delta
					ll.append(ay)
					lr.append(by)

			ll.sort()
			lr.sort()

			for j in range(0,len(ll),2):
				ay = min(ll[j], lr[j])
				by = max(ll[j+1], lr[j+1])
				flag = 0
				for b in boxes:
					if (b.BR==(ax,ay) and b.TR==(ax,by)):
						b.extend_right(bx)
						flag = 1
				if (flag==0):
					boxes.append(Zone(ax,ay,bx,by))


	def get_crocs(self):
		
		q = croc_first
		t = croc_tol

		for box in self.boxes:
			
			# get the list of crocs
			# cuts = list()
			# for c in self.crocs:
			#	if (c.x2 == box.ax and c.y>box.bx and c.y<box.by):
			#		cuts.append(c)
		
			# add the crocs at 15cm
			low = box.extend_crocs(self.crocs, box.ay+q, box.ay+q+t)
			if (not low):
				print("NEW", box.ax, box.bx, box.ay+q)
				low.append(Croc(box.ax,box.bx,box.ay+q))
				self.crocs = self.crocs + low
			inf = max([c.y for c in low])

			# add the crocs at -15cm
			high = box.extend_crocs(self.crocs, box.by - q, box.by - q - t)
			if (not high):
				high.append(Croc(box.ax,box.bx,box.by-q))
				self.crocs = self.crocs + high
			sup = min([c.y for c in high])
			
			print("----------------")
			# for c in self.crocs:
			#	print(c.x1, c.x2, c.y)


	def simple_crocs(self):

		q = croc_first
		p = croc_second

		for box in self.boxes:
			# crocs at +15cm and -15cm
			self.crocs.append(Croc(box.ax, box.bx, box.by - q))
			self.crocs.append(Croc(box.ax, box.bx, box.ay + q))

			# crocs at +60cm and -60cm
			if (box.by-box.ay - 2*q > 3*p):
				self.crocs.append(Croc(box.ax, box.bx, box.by - p))
				self.crocs.append(Croc(box.ax, box.bx, box.ay + p))
				
				# crocs every 120cm
				for lev in spread(box.ay+p, box.by-p, croc_maxd):
					self.crocs.append(Croc(box.ax, box.bx, lev))

			else:
				H = (box.by - box.ay - 2*q)/3
				self.crocs.append(Croc(box.ax, box.bx, box.ay + p + H))
				self.crocs.append(Croc(box.ax, box.bx, box.ay + p + 2*H))

	def get_omegas(self):	
		for box in self.boxes:			
			for d in center(box.ax, box.bx, space_omega):
				self.omegas.append((d,box.ay,box.by))


	def draw_crocs(self, msp, orient):
		for c in self.crocs:
			if (orient==0):
				line = msp.add_line((c.x1,c.y),(c.x2,c.y))
			else:
				line = msp.add_line((c.y,c.x1),(c.y,c.x2))

			line.dxf.layer = layer_croc

	def draw_omegas(self, msp, orient):
		for o in self.omegas:
			if (orient==0):
				line = msp.add_line((o[0],o[1]), (o[0],o[2]))
			else:
				line = msp.add_line((o[1],o[0]), (o[2],o[0]))
			line.dxf.layer = layer_omega
		

	def draw_room(self, msp):

		subindex = 0
		for box in self.boxes:
			box.draw_box(msp, self.orient)
			box.draw_text(msp, self.index, subindex, self.orient)
			subindex = subindex + 1
			
		self.draw_crocs(msp, self.orient)
		self.draw_omegas(msp, self.orient)


Room.index = 0


class App:

	def __init__(self):
		self.root = Tk()
		root = self.root
		self.button = Button(root, text="Open", command=self.search, pady=5)
		self.button.grid(row=0, column=0)

		self.text = StringVar()
		self.text.set("Select DXF File")
		self.flabel = Label(root, textvariable=self.text, width=50)
		self.flabel.grid(row=0, column=1)

		self.text1 = StringVar()
		self.flabel = Label(root, textvariable=self.text1, width=50)
		self.flabel.grid(row=1, column=1)

		self.var = StringVar()
		self.opt = OptionMenu(root,self.var,[])

		self.button1 = Button(root, text="Build Model", command=self.build_model, pady=5)
		self.button1.grid(row=5, column=0)
		self.button1["state"] = "disabled"

		self.root.mainloop()
	

	def search(self,event=None):
		self.filename = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
		self.loadfile()

	def loadfile(self):
		try:
			self.doc = ezdxf.readfile(self.filename)
		except IOError:
			self.text.set('Not a DXF file or a generic I/O error.')
			return
		except ezdxf.DXFStructureError:
			self.text.set('Invalid or corrupted DXF file.')
			return

		self.text.set(self.filename)
		self.outname = self.filename[:-4]+"_mod.dxf"
		self.text1.set(self.outname)

		self.msp = self.doc.modelspace()
		

		layers = [layer.dxf.name for layer in self.doc.layers]
		self.opt.destroy()
		self.var.set(layers[0])
		self.opt = OptionMenu(self.root,self.var,*layers)
		self.opt.grid(row=2, column=1)
		self.button1["state"] = "normal" 

	def create_layers(self):
		self.doc.layers.new(name=layer_text, dxfattribs={'linetype': 'CONTINUOUS', 'color': 7})
		self.doc.layers.new(name=layer_box, dxfattribs={'linetype': 'CONTINUOUS', 'color': 8})
		self.doc.layers.new(name=layer_croc, dxfattribs={'linetype': 'CONTINUOUS', 'color': 9})
		self.doc.layers.new(name=layer_omega, dxfattribs={'linetype': 'CONTINUOUS', 'color': 10})


	def build_model(self):
		self.create_layers()
		print("num poly:", len(self.msp.query('LWPOLYLINE')))
		pc = 0
		po = 0
		for poly in  self.msp.query('LWPOLYLINE'):
			# print(poly.is_closed)
			if (poly.is_closed):
				pc = pc + 1
			else:
				po = po + 1
			room = Room(poly)
			room.draw_room(self.msp)
		print("open poly", po)
		print("closed poly", pc)
		self.doc.saveas(self.outname)


########################### GUI #####################

	
App()



