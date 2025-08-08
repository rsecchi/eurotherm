from typing import List, Optional
from geometry import backtrack, midpoint, norm, offset, point_t
from geometry import poly_t, shift, xprod
from reference_frame import adv, diff, mul, versor

COS45 = 0.7071067811865476  # sqrt(2) / 2, used for angle thresholding

class Anchor:

	def __init__(self, red: point_t, blue: point_t, dir: point_t):
		self.red = red
		self.blue = blue
		self.dir = norm(dir)
		self.mid = midpoint(red, blue)
		self.stub_length = 0.0
		self.path: list[point_t] = [self.mid]

		delta_red = diff(self.mid, red)
		ortho = (-self.dir[1], self.dir[0])

		self.width = abs(xprod(ortho, diff(red, blue)))/2
		self.sign = 1 if xprod(ortho, delta_red) > 0 else -1
		self.pos = self.mid


	def set_stub(self, stub_length: float):
		self.stub_length = stub_length
		delta_red = diff(self.mid, self.red)
		proj = xprod(self.dir, delta_red)
		pipe = stub_length + abs(proj)
		self.stub_mid = adv(self.mid, mul(pipe, self.dir))
		self.path.append(self.stub_mid)
		self.pos = self.stub_mid


	def extend_anchor(self, length: float):
		if len(self.path) < 2:
			return
		u = versor(self.path[-2], self.path[-1])
		shifted = shift(self.path[-1], u, length)
		self.path.append(shifted)
		self.pos = shifted


	def face_target(self, target: point_t) -> List[point_t]:

		path = []
		step = self.stub_length
		node = self.pos
		dir = self.dir

		v = versor(node, target)
		while dir[0]*v[0] + dir[1]*v[1] < COS45:
			if -dir[1]*v[0] + dir[0]*v[1] > 0:
				dir = COS45*(dir[0]-dir[1]), COS45*(dir[0]+dir[1])
			else:
				dir = COS45*(dir[0]+dir[1]), COS45*(dir[1]-dir[0])

			node = node[0] + dir[0]*step, node[1] + dir[1]*step
			path.append(node)
			self.pos = node
			self.path.append(node)


		return path


class Connector:

	link_width = 0.0
	link_width = 0.0
	stub_length = 0.0
	leeway = 0.0

	def __init__(self):
		self.anchors: List[Anchor] = []
		self.target: Optional[point_t] = None
		self.path: List[point_t] = []
		self.ofs_red: List[float] = []
		self.red_path: List[point_t] = []
		self.blue_path: List[point_t] = []


	def attach(self, red: point_t, blue: point_t, dir: point_t):
		endpoint = Anchor(red=red, blue=blue, dir=dir)
		endpoint.set_stub(self.stub_length/2)
		self.anchors.append(endpoint)


	def attach_anchor(self, anchor: Anchor):
		self.anchors.append(anchor)


	def misalignment(self) -> float:
		if len(self.anchors) != 2:
			return 0.0

		if len(self.anchors[0].path) < 2 or len(self.anchors[1].path) < 2:
			return 0.0

		v1 = versor(self.anchors[0].path[-1], self.anchors[0].path[-2])
		v2 = versor(self.anchors[1].path[-1], self.anchors[1].path[-2])

		return xprod(v1, v2)



	def point_to_point(self):

		if len(self.anchors) != 2:
			return

		link_width = self.link_width

		self.path = []
		self.ofs: list[float] = []

		node0 = self.anchors[0].stub_mid
		sign0 = self.anchors[0].sign
		node1 = self.anchors[1].stub_mid
		sign1 = -self.anchors[1].sign

		self.path.append(self.anchors[0].mid)
		self.path.append(node0)
		self.ofs.append(sign0*self.anchors[0].width)

		path = self.anchors[0].face_target(self.anchors[1].stub_mid)
		for node in path:
			self.path.append(node)
			self.ofs.append(sign0*link_width)
		self.ofs.append(sign0*link_width)
		m = len(self.path) - 1

		path = self.anchors[1].face_target(self.anchors[0].stub_mid)
		for node in reversed(path):
			self.path.append(node)
			self.ofs.append(sign0*link_width)

		self.path.append(node1)
		self.ofs.append(sign0*self.anchors[1].width)
		self.path.append(self.anchors[1].mid)

		neg_ofs = [-ofs for ofs in self.ofs]

		self.red_path = offset(self.path, self.ofs)
		self.blue_path = offset(self.path, neg_ofs)
		self.red_path[0] = self.anchors[0].red
		self.blue_path[0] = self.anchors[0].blue

		if sign0 != sign1:
			mid_red = midpoint(self.red_path[m], self.red_path[m+1])
			mid_blue = midpoint(self.blue_path[m], self.blue_path[m+1])
			mid0_red = backtrack(self.red_path[m], mid_red, link_width)
			mid1_red = backtrack(self.red_path[m+1], mid_red, link_width)
			mid0_blue = backtrack(self.blue_path[m], mid_blue, link_width)
			mid1_blue = backtrack(self.red_path[m+1], mid_blue, link_width)
			br0_red = self.red_path[:m+1] + [mid0_red]
			br0_blue = self.blue_path[:m+1] + [mid0_blue]
			br1_red = [mid1_red] + self.red_path[m+1:]
			br1_blue = [mid1_blue] + self.blue_path[m+1:]
			self.red_path = br0_red + br1_blue
			self.blue_path = br0_blue + br1_red

		self.red_path[-1] = self.anchors[-1].red
		self.blue_path[-1] = self.anchors[-1].blue


	def point_to_target(self):

		if not self.target:
			return

		if len(self.anchors) != 1:
			return

		self.path = []
		self.ofs: list[float] = []

		node0 = self.anchors[0].stub_mid
		sign0 = self.anchors[0].sign

		self.path.append(self.anchors[0].mid)
		self.path.append(node0)
		self.ofs.append(sign0*self.anchors[0].width)

		path = self.anchors[0].face_target(self.target)
		for node in path:
			self.path.append(node)
			self.ofs.append(sign0*self.link_width)

		point = backtrack(self.path[-1], self.target, self.leeway)
		self.path.append(point)
		self.ofs.append(sign0*self.link_width)

		self.red_path = offset(self.path, self.ofs)
		self.blue_path = offset(self.path, [-ofs for ofs in self.ofs])
		self.red_path[0] = self.anchors[0].red
		self.blue_path[0] = self.anchors[0].blue


	def build_from_path(self, path: poly_t):

		if len(self.anchors) != 1:
			raise ValueError("Connector must have exactly one"
					"anchor for building from path.")

		anchor = self.anchors[0]
		self.path = anchor.path.copy()
		self.path.extend(path[1:])

		sign0 = anchor.sign
		for _ in self.path:
			self.ofs_red.append(sign0*self.link_width)
		self.ofs_red[0] = sign0*anchor.width
			
		self.red_path = offset(self.path, self.ofs_red)
		self.red_path[0] = anchor.red
		self.blue_path = offset(self.path, [-ofs for ofs in self.ofs_red])
		self.blue_path[0] = anchor.blue


