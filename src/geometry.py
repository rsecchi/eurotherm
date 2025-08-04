from PIL import Image, ImageDraw
from math import cos, sin, sqrt

import numpy as np
from PIL.ImageFont import truetype

from reference_frame import adv, mul, versor



MAX_DIST = 1e20

point_t = tuple[float, float]
poly_t = list[point_t]


def xprod(a: point_t, b: point_t):
	return a[0]*b[0]+a[1]*b[1]


def midpoint(a: point_t, b: point_t) -> point_t:
	return ((a[0]+b[0])/2, (a[1]+b[1])/2)


def ortho(a: point_t, b: point_t):
	return a[0]*b[1]-a[1]*b[0]
	

def parallel_proj(vector: point_t, vers: point_t):
	proj = vector[0]*vers[0] + vector[1]*vers[1]
	return (proj*vers[0], proj*vers[1])


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


	
def backtrack(p1: point_t, p2:point_t, val: float) -> point_t:
	return adv(p2, mul(-val, versor(p1, p2)))


def shift(point: point_t, vector: point_t, distance: float = 1.) -> point_t:
	u = norm(vector)
	return (point[0] + distance*u[0], point[1] + distance*u[1])


def perpendicular_coord(point: point_t, line: poly_t) -> float:

	a = line[0]
	b = line[1]

	if a == b:
		return dist(point, a)

	ux, uy = norm((b[0]-a[0], b[1]-a[1]))
	dx, dy = point[0]-a[0], point[1] - a[1]

	return ux*dy - uy*dx


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


def vertical_distance(poly: poly_t, point: point_t) -> float:

	if len(poly)<1:
		return MAX_DIST

	d = MAX_DIST
	
	for i in range(len(poly)-1):
		ax, ay = poly[i]
		bx, by = poly[i+1]
		x0, y0 = point

		if (ax > x0 and bx > x0) or (ax < x0 and bx < x0):
			continue

		if ax == bx == x0:
			d = min(min(abs(ay - y0), abs(by - y0)), d)
			continue

		yp = ((ay-by)*x0 + ax*by - bx*ay)/(ax-bx)

		d = min(abs(yp - y0), d)

	return d



def horizontal_distance(poly: poly_t, point: point_t) -> float:

	if len(poly)<1:
		return MAX_DIST

	d = MAX_DIST
	
	for i in range(len(poly)-1):
		ax, ay = poly[i]
		bx, by = poly[i+1]
		x0, y0 = point

		if (ay > y0 and by > y0) or (ay < y0 and by < y0):
			continue

		if ay == by == y0:
			d = min(min(abs(ax - x0), abs(ay - x0)), d)
			continue

		xp = ((ax-bx)*y0 + ay*bx - by*ax)/(ay-by)

		d = min(abs(xp - x0), d)

	return d


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


# def offset(poly, off: float) -> poly_t:

# 	if len(poly)<2:
# 		return []

# 	opoly = list()

# 	up = u = ou = (0, 0)
# 	for i in range(len(poly)-1):
# 		ux = poly[i+1][0] - poly[i][0]
# 		uy = poly[i+1][1] - poly[i][1]
# 		du = ux*ux + uy*uy
# 		if du == 0:
# 			continue
# 		du = sqrt(du)

# 		u = -uy/du, ux/du
# 		k = 1 + u[0]*up[0] + u[1]*up[1]
# 		if  k != 0:
# 			ou = (u[0]+up[0])/k, (u[1]+up[1])/k

# 		p = poly[i][0]+off*ou[0], poly[i][1]+off*ou[1]
# 		opoly.append(p)

# 		up = u

# 	opoly.append((poly[-1][0]+off*u[0], poly[-1][1]+off*u[1]))

# 	return opoly


def offset(poly: poly_t, off: float | list[float]) -> poly_t:

	if isinstance(off, float):
		off = [off] * (len(poly) - 1)

	if not isinstance(off, list):
		return poly

	segs = []
	u = []
	v = []

	for i in range(len(poly)-1):

		sega = poly[i]
		segb = poly[i+1]

		tang = versor(sega, segb)
		norm = (-tang[1], tang[0])
		p1 = (sega[0] + off[i]*norm[0], sega[1] + off[i]*norm[1])
		p2 = (segb[0] + off[i]*norm[0], segb[1] + off[i]*norm[1])
		segs.append([p1,p2])
		u.append(tang)
		v.append(norm)
	
	opoly = []
	opoly.append(segs[0][0])

	for i in range(len(segs)-1):
		xa1, ya1, xa2, ya2 = *segs[i][0],   *segs[i][1]
		xb1, yb1, xb2, yb2 = *segs[i+1][0], *segs[i+1][1]

		dxa = xa2 - xa1
		dya = ya2 - ya1
		dxb = xb2 - xb1
		dyb = yb2 - yb1
		dxx = xb1 - xa1
		dyy = yb1 - ya1
		
		det = dya * dxb - dxa * dyb
		adt = dxa * dyy - dya * dxx
		ads = dxb * dyy - dyb * dxx

		s = ads / det if det != 0 else ads * float('inf')
		t = adt / det if det != 0 else adt * float('inf')

		if (s<0 and t<0) or (s>1 and t>1):
			lateral_shift = abs(off[i] - off[i+1])
			join1 = adv(segs[i][1], mul(-lateral_shift, u[i]))
			join2 = adv(segs[i+1][0], mul(lateral_shift, u[i+1]))
			opoly.append(join1)
			opoly.append(join2)
			continue

		if adt == 0 and ads == 0:
			continue

		m1 = ads / det
		miter = xa1 + m1 * dxa, ya1 + m1 * dya
		opoly.append(miter)

	opoly.append(segs[-1][1])
		
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



class CoordSystem:
	def __init__(self, origin: point_t, angle: float, scale: float):
		self.origin = origin
		self.angle = angle
		self.scale = scale
		self.ux = cos(angle)/scale
		self.uy = sin(angle)/scale

	
	def local_to_real(self, point: point_t) -> point_t:
		xl, yl = point	
		ox, oy = self.origin
		xr = self.ux*xl - self.uy*yl + ox
		yr = self.uy*xl + self.ux*yl + oy
		return (xr, yr)


	def real_to_local(self, point: point_t) -> point_t:
		xr, yr = point
		ox, oy = self.origin
		xl =  self.ux*(xr - ox) + self.uy*(yr - oy)
		yl = -self.uy*(xr - ox) + self.ux*(yr - oy)
		return (xl, yl)


class Picture:

	width_px = 600
	height_px = 400
	margin = 10.
	radius = 5.

	id = 0

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

	def draw(self, filename: str = ""):

		if filename == "":
			self.set_frame()
			Picture.id += 1
			filename = f"picture_{Picture.id}.png"

		for shade in self.shades:
			color = shade["color"]
			poly = self.scale(shade["poly"])
			self.drawing.polygon(poly, fill=color)

		for i, poly in enumerate(self.polylines):
			color = self.colors[i]
			dpoly = self.scale(poly)
			if len(dpoly)==1:
				r = self.radius
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
	w = dist(end1, end2)/4

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


# def offset_poly(poly: poly_t, offset: float) -> list[poly_t]:

# 	scale = 1e6
# 	scaled_poly = [(int(x * scale), int(y * scale)) for x, y in poly]

# 	pc = PyclipperOffset()
# 	pc.AddPath(scaled_poly, JT_MITER, ET_CLOSEDPOLYGON)
# 	paths = pc.Execute(offset * scale)

# 	polygons = []
# 	for path in paths:
# 		off_path = [(x/scale, y/scale) for x, y in path]
# 		polygons.append(off_path+[off_path[0]])

# 	return polygons



def offset_segment(p1, p2, distance):
    # Compute direction and normal
    dx, dy = np.array(p2) - np.array(p1)
    length = np.hypot(dx, dy)
    nx, ny = -dy / length, dx / length  # normal vector (left-hand)
    offset_p1 = (p1[0] + nx * distance, p1[1] + ny * distance)
    offset_p2 = (p2[0] + nx * distance, p2[1] + ny * distance)
    return offset_p1, offset_p2


def line_intersection(p1, p2, q1, q2):
    """Return intersection point of line segments (p1,p2) and (q1,q2)"""
    a1, b1 = np.array(p1), np.array(p2)
    a2, b2 = np.array(q1), np.array(q2)
    da, db = b1 - a1, b2 - a2
    dp = a1 - a2
    dap = np.array([-da[1], da[0]])
    denom = np.dot(dap, db)
    if np.abs(denom) < 1e-10:
        return None  # parallel
    num = np.dot(dap, dp)
    return tuple(a2 + (num / denom) * db)


def non_uniform_offset(polyline, offsets):
    assert len(polyline) >= 2 and len(offsets) == len(polyline) - 1
    segments = []
    for (p1, p2), d in zip(zip(polyline[:-1], polyline[1:]), offsets):
        segments.append(offset_segment(p1, p2, d))

    offset_points = [segments[0][0]]  # first point of first segment
    for (p1, p2), (q1, q2) in zip(segments[:-1], segments[1:]):
        ipt = line_intersection(p1, p2, q1, q2)
        offset_points.append(ipt if ipt else p2)  # fallback to end of segment
    offset_points.append(segments[-1][1])  # last point of last segment
    return offset_points
