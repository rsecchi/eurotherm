from PIL import Image, ImageDraw
from math import sqrt

MAX_DIST = 1e20


def dist(point1, point2):
	dx = point1[0] - point2[0]
	dy = point1[1] - point2[1]
	return sqrt(dx*dx+dy*dy)


def central_symm(centre, point):
	x = 2*centre[0] - point[0]
	y = 2*centre[1] - point[1]
	return (x,y)

def line_cross(line0, line1):

	a0x = line0[0][0]
	a0y = line0[0][1]
	a1x = line0[1][0]
	a1y = line0[1][1]
	b0x = line1[0][0]
	b0y = line1[0][1]
	b1x = line1[1][0]
	b1y = line1[1][1]

	delta  = -(a1x-a0x)*(b1y-b0y)+(b1x-b0x)*(a1y-a0y)
	if delta==0:
		return None

	deltat = -(b0x-a0x)*(b1y-b0y)+(b1x-b0x)*(b0y-a0y)
	deltas =  (a1x-a0x)*(b0y-a0y)-(a1y-a0y)*(b0x-a0x)
	t = deltat/delta
	s = deltas/delta

	if not (0<=s and s<=1 and 0<=t and t<=1):
		return None

	return (b0x + s*(b1x-b0x), b0y + s*(b1y-b0y))



def project_hor(poly, point) -> tuple[float,float]:

	if len(poly)<1:
		return point

	y = point[1]

	xmin = xmax = poly[0][0]
	ymin = ymax = poly[0][1]

	for i in range(len(poly)-1):
		pa = poly[i]
		pb = poly[i+1]
		if pa[1] == pb[1]:
			if pa[1] == y:
				return pa
		else:
			if pa[1] < pb[1]:
				if pa[1]<=y and y<=pb[1]:
					u = pb[0]*(y-pa[1]) + pa[0]*(pb[1]-y)
					d = pb[1] - pa[1]
					return (u/d, y)	
			else:
				if pb[1]<=y and y<=pa[1]:
					u = pa[0]*(y-pb[1]) + pb[0]*(pa[1]-y)
					d = pa[1] - pb[1]
					return (u/d, y)

		if ymin > pb[1]:
			xmin = pb[0]
			ymin = pb[1]
		
		if ymax < pb[1]:
			xmin = pb[0]
			ymax = pb[1]

	if y<ymin:
		return (xmin, y)

	return (xmax, y)


def miter(poly, offs):

	if len(poly)<3:
		return 
	
	opoly = [poly[0]]
	
	for i in range(1, len(poly)-1):
		u1x = poly[i-1][0] - poly[i][0]
		u1y = poly[i-1][1] - poly[i][1]
		d1u = sqrt(u1x*u1x + u1y*u1y)
		u2x = poly[i+1][0] - poly[i][0]
		u2y = poly[i+1][1] - poly[i][1]
		d2u = sqrt(u2x*u2x + u2y*u2y)
		
		if (d1u==0 or d2u==0):
			opoly.append(poly[i])
			continue

		off = min(offs, d1u/3, d2u/3)
	
		u1 = off*u1x/d1u, off*u1y/d1u
		u2 = off*u2x/d2u, off*u2y/d2u
		
		o1 = poly[i][0] + u1[0], poly[i][1] + u1[1]
		o2 = poly[i][0] + u2[0], poly[i][1] + u2[1]
		opoly.append(o1)
		opoly.append(o2)

	opoly.append(poly[-1])
	return opoly


def offset(poly, off: float):

	if len(poly)<2:
		return

	opoly = list()

	up = u = ou = (0, 0)
	for i in range(len(poly)-1):
		ux = poly[i+1][0] - poly[i][0]
		uy = poly[i+1][1] - poly[i][1]
		du = ux*ux + uy*uy
		if du == 0:
			continue
		du = sqrt(du)

		u = -uy/du, ux/du
		k = 1 + u[0]*up[0] + u[1]*up[1]
		if  k != 0:
			ou = (u[0]+up[0])/k, (u[1]+up[1])/k

		p = poly[i][0]+off*ou[0], poly[i][1]+off*ou[1]
		opoly.append(p)

		up = u

	opoly.append((poly[-1][0]+off*u[0], poly[-1][1]+off*u[1]))

	return opoly


def extend_to_poly(poly, v):

	ux = v[1][0] - v[0][0]
	uy = v[1][1] - v[0][1]

	if ux==0 and uy==0:
		return None

	# find BBox
	minx = maxx = poly[0][0]
	miny = maxy = poly[0][1]
	for i in range(1, len(poly)-1):
		minx = min(minx, poly[i][0])
		maxx = max(maxx, poly[i][0])
		miny = min(miny, poly[i][1])
		maxy = max(maxy, poly[i][1])

	if ((maxx < v[0][0] and ux>0) or 
		(minx > v[0][0] and ux<0) or
		(maxy < v[0][1] and uy>0) or 
		(miny > v[0][1] and uy<0)):
		return None

	fx = fy = MAX_DIST
	if not ux==0:
		if ux>0:
			dx = maxx - v[0][0]
		else:
			dx = minx - v[0][0]
		fx = dx/ux

	if not uy==0:
		if uy>0:
			dy = maxy - v[0][1]
		else:
			dy = miny - v[0][1]
		fy = dy/uy

	f = 2*min(fx, fy)
	p = (v[0][0] + f*ux, v[0][1]+f*uy)

	crss = list()
	l1 = (v[0], p)
	for i in range(len(poly)-1):
		pa = poly[i]
		pb = poly[i+1]
		l0 = (pa, pb)
		r = line_cross(l0, l1)
		if not r:
			continue
		crss.append(r)

	if len(crss) == 0:
		return None

	norm = dist(v[1], v[0])
	e = None
	d = MAX_DIST
	for c in crss:
		d1 = dist(c, v[0])/norm
		if d1>=0.99 and d1<d:
			d = d1
			e = c

	return e


def trim_segment_by_poly(poly, seg):
	
	crss = list()
	for i in range(len(poly)-1):
		line = (poly[i], poly[i+1])
		r = line_cross(line, seg)
		if r:
			d = dist(seg[0], r)
			crss.append([d, r])

	l = len(crss)
	if not (l>0 and l%2==0):
		return []

	crss.sort(key=lambda x: x[0])

	cr = list()
	for i in range(0,l,2):
		cr.append([crss[i][1], crss[i+1][1]])

	return cr


def trim_poly_by_vector(poly, vector):

	center = extend_to_poly(poly, vector)
	if not center:
		return poly

	opposite = 2*center[0] - vector[0][0], 2*center[1] - vector[0][1]
	trimmer = [opposite, vector[0]]

	opoly = []
	for i in range(len(poly)-1):
		opoly.append(poly[i])
		line = (poly[i], poly[i+1])
		cross = line_cross(trimmer, line)
		if cross:
			opoly.append(cross)
			return opoly
	
	opoly.append(poly[-1])
	return opoly


class Picture:

	width_px = 600
	height_px = 400
	margin = 20
	radius = 5

	def __init__(self):
		self.polylines = []
		self.colors = []
		w = Picture.width_px
		h = Picture.height_px
		self.image = Image.new("RGBA", (w, h), (255, 255, 255, 255))
		self.drawing = ImageDraw.Draw(self.image)
		self.xscale = 1.0
		self.yscale = 1.0
		self.xorig = 0
		self.yorig = 0


	def add(self, poly, color="black"):
		
		self.polylines.append(poly)
		self.colors.append(color)
		

	def scale(self, poly):
		opoly = []
		for point in poly:
			x = point[0]*self.xscale + self.xorig
			y = Picture.height_px - (point[1]*self.yscale + self.yorig)
			opoly.append((x,y))
		return opoly


	def set_frame(self):

		if not self.polylines:
			return

		xmax, ymax = xmin, ymin = self.polylines[0][0]

		for polyline in self.polylines:
			x_min = min([x[0] for x in polyline])
			y_min = min([x[1] for x in polyline])
			x_max = max([x[0] for x in polyline])
			y_max = max([x[1] for x in polyline])
			
			xmin = min(x_min,xmin)
			ymin = min(y_min,ymin)
			xmax = max(x_max,xmax)
			ymax = max(y_max,ymax)

		deltax = xmax - xmin
		deltay = ymax - ymin

		if deltax > 0:
			self.xscale = (Picture.width_px - 2*Picture.margin) / deltax

		if deltay > 0:
			self.yscale = (Picture.height_px - 2*Picture.margin)/ deltay

		self.xscale = self.yscale = min(self.xscale, self.yscale)

		self.xorig = (Picture.width_px-self.xscale*(xmin+xmax))/2
		self.xorig -= Picture.margin/2
		self.yorig = (Picture.height_px-self.xscale*(xmin+xmax))/2
		self.yorig -= Picture.margin/2


	def draw(self, filename: str):
		for i, poly in enumerate(self.polylines):
			color = self.colors[i]
			dpoly = self.scale(poly)
			if len(dpoly)==1:
				r = Picture.radius
				p = dpoly[0]
				point = (p[0]-r,p[1]-r,p[0]+r,p[1]+r)
				self.drawing.ellipse(point, fill=color)
				continue
			self.drawing.line(dpoly, fill=color, width=1)
		self.image.save(filename)



picture = Picture()

poly = [(50., 300), (100, 100), (250, 350), (350, 50)]

vector = [(0,0), (60,20)]

mypoint = extend_to_poly(poly, vector)

tp = trim_poly_by_vector(poly, vector)

picture.add(poly, "green")
picture.add(tp, "orange")
picture.add(vector, "purple")


poly = offset(poly, 20)

picture.add(poly)


vector2 = [(100,140), (100,150)]
picture.add(vector2, "cyan")

trimmed = trim_poly_by_vector(poly, vector2)

picture.add(trimmed, "lightblue")

picture.set_frame()
picture.draw("polyline.png")

