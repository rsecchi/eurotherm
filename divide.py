#!/usr/local/bin/python3

print("This program opens a DXF")

import ezdxf

#   (ax,ay)    (bx,ay)  p2
#
#
#   (ax,by)    (bx,by)  p1 

class Zone():

	width_doga   = 20
	croc_first  = 15
	croc_second = 60
	croc_maxd    = 120

	text_layer  = 'Eurotherm_text'
	text_font   = 'LiberationSerif'
	box_layer   = 'Eurotherm_box'
	croc_layer = 'Eurotherm_crocodile'
	doga_layer  = 'Eurotherm_doga'

	def __init__(self,ax,ay,bx,by):
		self.ax = ax; self.bx = bx
		self.ay = ay; self.by = by
		self.pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]

	def extend_right(self, bx):
		ax = self.ax
		self.bx = bx
		ay = self.ay
		by = self.by
		self.pline = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]

	def draw_box(self):
		pl = msp.add_lwpolyline(box.pline)
		pl.dxf.layer = Zone.box_layer

	def draw_text(self, text):
		pos = ((self.ax + self.bx)/2, (self.ay+self.by)/2)
		ttype={'style': Zone.text_font, 'height': 50, 'layer': Zone.text_layer}
		msp.add_text(text, ttype).set_pos(pos, align='MIDDLE')

	def draw_doga(self):
		ax = self.ax; ay = self.ay
		bx = self.bx; by = self.by
		L = Zone.width_doga
		n = int((self.bx - self.ax) / L)
		for i in range(0, n):
			box = Zone(self.ax + i*L, self.ay, self.ax + (i+1)*L, self.by)
			pl = msp.add_lwpolyline(box.pline)
			pl.dxf.layer = Zone.doga_layer

	def draw_croc(self):
		ax = self.ax; ay = self.ay
		bx = self.bx; by = self.by

		fst = Zone.croc_first
		snd = Zone.croc_second

		# draw first croc
		line = msp.add_line((ax,by-fst),(bx,by-fst))
		line.dxf.layer = Zone.croc_layer
		line = msp.add_line((ax,ay+fst),(bx,ay+fst))
		line.dxf.layer = Zone.croc_layer

		# draw second croc
		line = msp.add_line((ax,by-snd),(bx,by-snd))
		line.dxf.layer = Zone.croc_layer
		line = msp.add_line((ax,ay+snd),(bx,ay+snd))
		line.dxf.layer = Zone.croc_layer

		# draw remaing crocs
		h1 = ay + Zone.croc_second
		h2 = by - Zone.croc_second
		print(ay, h1, h2, by)
		n = int((h2 - h1) / Zone.croc_maxd)
		H = (h2-h1)/n
		for i in range(0,n):
			hy = h1 + i*H
			line = msp.add_line((ax,hy),(bx,hy))
			line.dxf.layer = Zone.croc_layer

# This function divides a polyline into boxes
# and returns the list of boxes
def get_boxes(polyline):
	boxes = list()
	points = list(poly.vertices())
	xs = sorted(set([p[0] for p in poly.vertices()]))

	for i in range(0,len(xs)-1):
		ax = xs[i]
		bx = xs[i+1]
		midx = (ax + bx)/2
		ys = list()
		for j in range(0, len(points)-1):
			if (points[j][1]==points[j+1][1]):
				# vertical line
				m0 = min(points[j][0], points[j+1][0])
				m1 = max(points[j][0], points[j+1][0])
				if (m0<midx and m1>midx):
					ys.append(points[j][1])
		ys.sort()
		for j in range(0,len(ys),2):
			ay = ys[j]
			by = ys[j+1]
			m = -1
			for k in range(0,len(boxes)):
				p1 = boxes[k].pline[2]
				p2 = boxes[k].pline[3]
				if (p2==(ax,ay) and p1==(ax,by)):
					m = k

			if (m==-1):
				box = Zone(ax,ay,bx,by)
				boxes.append(box)
			else:
				boxes[m].extend_right(bx)

	return boxes



# Open file and get model space
doc = ezdxf.readfile("test1.dxf")
msp = doc.modelspace()


# Creating layers
doc.layers.new(name=Zone.text_layer, dxfattribs={'linetype': 'CONTINUOUS', 'color': 7})
doc.layers.new(name=Zone.box_layer, dxfattribs={'linetype': 'CONTINUOUS', 'color': 8})
doc.layers.new(name=Zone.croc_layer, dxfattribs={'linetype': 'CONTINUOUS', 'color': 9})
doc.layers.new(name=Zone.doga_layer, dxfattribs={'linetype': 'CONTINUOUS', 'color': 10})


# Get all the polylines from the layer=XXX
index = 0
for poly in  msp.query('LWPOLYLINE'):
	index = index + 1
	boxes = get_boxes(poly)
	subzone = 64
	for box in boxes:
		subzone = subzone + 1
		box.draw_box()
		box.draw_text("Zone"+str(index)+chr(subzone))
		box.draw_doga()
		box.draw_croc()


doc.saveas("test1_mod.dxf")

