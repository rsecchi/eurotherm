#!/usr/local/bin/python3

print("This program opens a DXF")

import ezdxf

#   (ax,ay)    (bx,ay)  p2
#
#
#   (ax,by)    (bx,by)  p1 


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
				p1 = boxes[k][2]
				p2 = boxes[k][3]
				if (p2==(ax,ay) and p1==(ax,by)):
					m = k

			if (m==-1):
				box = [(ax,ay),(ax,by),(bx,by),(bx,ay),(ax,ay)]
			else:
				print("Extending box",m, boxes[m])
				box = [boxes[m][0],boxes[m][1],(bx,by),(bx,ay),boxes[m][4]]
				del boxes[m]
			boxes.append(box)
	return boxes


doc = ezdxf.readfile("test.dxf")
msp = doc.modelspace()

for poly in  msp.query('LWPOLYLINE'):
	boxes = get_boxes(poly)
	for box in boxes:
		msp.add_lwpolyline(box)


doc.saveas("test_mod.dxf")

