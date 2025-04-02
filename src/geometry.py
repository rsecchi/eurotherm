from PIL import Image, ImageDraw
from math import sqrt

from PIL.ImageFont import truetype
from pyclipper import PyclipperOffset, JT_MITER, ET_CLOSEDPOLYGON


MAX_DIST = 1e20

point_t = tuple[float, float]
poly_t = list[point_t]


def xprod(a: point_t, b: point_t):
	return a[0]*b[0]+a[1]*b[1]


def norm(vector) -> point_t:

	if isinstance(vector, list):
		vector = (vector[1][0]-vector[0][0],vector[1][1]-vector[0][1])

	n = sqrt(vector[0]*vector[0] + vector[1]*vector[1])
	if n>0:
		return (vector[0]/n, vector[1]/n)
	return (0., 0.)


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


def find_intersect(line0, vect):

	a0x = line0[0][0]
	a0y = line0[0][1]
	a1x = line0[1][0]
	a1y = line0[1][1]
	b0x = vect[0][0]
	b0y = vect[0][1]
	b1x = vect[1][0]
	b1y = vect[1][1]

	delta  = -(a1x-a0x)*(b1y-b0y)+(b1x-b0x)*(a1y-a0y)
	if delta==0:
		return None

	deltat = -(b0x-a0x)*(b1y-b0y)+(b1x-b0x)*(b0y-a0y)
	t = deltat/delta

	if not (0<=t and t<=1):
		return None

	return (a0x + t*(a1x-a0x), a0y + t*(a1y-a0y))


def meeting_point(line0, line1):

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

	# deltat = -(b0x-a0x)*(b1y-b0y)+(b1x-b0x)*(b0y-a0y)
	deltas =  (a1x-a0x)*(b0y-a0y)-(a1y-a0y)*(b0x-a0x)
	# t = deltat/delta
	s = deltas/delta

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


def offset(poly, off: float) -> poly_t:

	if len(poly)<2:
		return []

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
		r = find_intersect(line, seg)
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


def trim(polyline: poly_t, line: poly_t, from_tail:bool=False) -> poly_t:
	""" Given a polyline and a line defined by two points, trim all the
		points that are on the opposite side of the first point w.r.t the line
		scanning the line up to first line crossing. 

		If from_tail is True, the polyline is reversed
		and the last point is considered for trimming
	""" 

	orig = line[0]
	ux, uy = (line[1][0]-orig[0], line[1][1]-orig[1])
	mod = sqrt(ux*ux+uy*uy)
	ux, uy = (ux/mod, uy/mod)
	vx, vy = (-uy, ux)

	opoly: poly_t = []
	if from_tail:
		poly = reversed(polyline)
		start_point = polyline[-1]
	else:
		poly = iter(polyline)
		start_point = polyline[0]

	refx = start_point[0] - orig[0]
	refy = start_point[1] - orig[1]

	xp = ux*refx + uy*refy
	yp = vx*refx + vy*refy

	if yp < 0:
		vx, vy = -vx, -vy

	for point in poly:
		xc = ux*(point[0]-orig[0]) + uy*(point[1]-orig[1])
		yc = vx*(point[0]-orig[0]) + vy*(point[1]-orig[1])
		if yc<=0:
			if yc==yp:
				opoly.append(point)
				break
			
			t = (xc*yp-xp*yc)/(yp-yc)
			opoly.append((t*ux+orig[0], t*uy+orig[1]))
			break

		opoly.append(point)
		xp, yp = xc, yc

	return opoly


class Picture:

	width_px = 600
	height_px = 400
	margin = 10
	radius = 5

	def __init__(self):
		self.polylines = []
		self.messages = []
		self.colors = []
		self.shades = []
		w = Picture.width_px
		h = Picture.height_px
		self.image = Image.new("RGBA", (w, h), 255)
		self.font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
		self.font = truetype(self.font_path, 12)
		self.drawing = ImageDraw.Draw(self.image)
		self.xscale = 1.0
		self.yscale = 1.0
		self.xorig = 0
		self.yorig = 0


	def add(self, poly, color="black"):
		if not poly:
			return
		
		if isinstance(poly, tuple):
			poly = [poly]

		self.polylines.append(poly)
		self.colors.append(color)
		

	def add_shaded_area(self, poly, color="grey"):
		if not poly:
			return

		if isinstance(poly, tuple):
			poly = [poly]

		self.shades.append({"poly": poly, "color": color})


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
		self.yorig = (Picture.height_px-self.xscale*(ymin+ymax))/2


	def text(self, point, text, color="black"):
		self.messages.append({"point": point, 
						   "text": text,
					       "color": color})

	def draw(self, filename: str):

		for shade in self.shades:
			color = shade["color"]
			poly = self.scale(shade["poly"])
			self.drawing.polygon(poly, fill=color)

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

		for msg in self.messages:
			point = self.scale([msg['point']])[0]
			color = msg["color"]
			text = msg["text"]
			width, height = self.drawing.textsize(text)
			point = (point[0]-width/2, point[1]-height/2)
			self.drawing.text(point, text, fill=color)

		self.image.save(filename)


def extend_pipes(pipe1: poly_t, pipe2: poly_t, target: point_t, leeway:float):

	end1 = pipe1[-1]
	end2 = pipe2[-1]

	side = (pipe1[-2][0]-end1[0], pipe1[-2][1]-end1[1])
	w = dist(end1, end2)/2

	vx, vy = norm((end2[0]-end1[0], end2[1]-end1[1]))
	ux, uy = vy, -vx

	if side[0]*ux + side[1]*uy > 0:
		ux, uy = -ux, -uy

	mid = (w*(vx+ux) + end1[0], w*(vy+uy) + end1[1])
	sx, sy = norm((target[0] - mid[0], target[1] - mid[1]))
	qx, qy = -sy, sx

	if vx*qx + vy*qy<0:
		qx, qy = -qx, -qy

	trg = (target[0] - leeway*sx, target[1] - leeway*sy)
	ext1 = [(mid[0]-w*qx, mid[1]-w*qy), (trg[0]-w*qx, trg[1]-w*qy)]
	ext2 = [(mid[0]+w*qx, mid[1]+w*qy), (trg[0]+w*qx, trg[1]+w*qy)]
	dir1 = [end1, (end1[0]+ux, end1[1]+uy)]
	dir2 = [end2, (end2[0]+ux, end2[1]+uy)]
	
	point1 = meeting_point(ext1, dir1)
	point2 = meeting_point(ext2, dir2)

	if point1:
		pipe1.append(point1)
		pipe1.append(ext1[1])

	if point2:
		pipe2.append(point2)
		pipe2.append(ext2[1])


def offset_poly(poly: poly_t, offset: float) -> list[poly_t]:

	scale = 1e6
	scaled_poly = [(int(x * scale), int(y * scale)) for x, y in poly]

	pc = PyclipperOffset()
	pc.AddPath(scaled_poly, JT_MITER, ET_CLOSEDPOLYGON)
	paths = pc.Execute(offset * scale)

	polygons = []
	for path in paths:
		off_path = [(x/scale, y/scale) for x, y in path]
		polygons.append(off_path+[off_path[0]])

	return polygons


