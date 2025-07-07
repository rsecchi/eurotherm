from typing import List, Optional
from geometry import backtrack, midpoint, norm, offset, point_t, xprod
from reference_frame import adv, diff, mul, versor
from settings import Config

COS45 = 0.7071067811865476  # sqrt(2) / 2, used for angle thresholding

class Anchor:

	def __init__(self, red: point_t, blue: point_t, dir: point_t):
		self.red = red
		self.blue = blue
		self.dir = norm(dir)
		self.mid = midpoint(red, blue)

		delta_red = diff(self.mid, red)
		proj = xprod(self.dir, delta_red)

		ortho = (-self.dir[1], self.dir[0])
		self.width = abs(xprod(ortho, diff(red, blue)))/2
		self.sign = 1 if xprod(ortho, delta_red) > 0 else -1


		pipe = Config.stub_length_cm/2 + abs(proj)

		self.stub_mid = adv(self.mid, mul(pipe, dir))

			

class Connector:
	def __init__(self):
		self.anchors: List[Anchor] = []
		self.target: Optional[point_t] = None
		self.path: List[point_t] = []
		self.ofs_red: List[float] = []
		self.red_path: List[point_t] = []
		self.blue_path: List[point_t] = []
	

	def attach(self, red: point_t, blue: point_t, dir: point_t):
		endpoint = Anchor(red=red, blue=blue, dir=dir)
		self.anchors.append(endpoint)


	def face_target(self, node: point_t, dir: point_t, target: point_t):

		path = []
		step = Config.stub_length_cm

		v = versor(node, target) 
		while dir[0]*v[0] + dir[1]*v[1] < COS45:
			if -dir[1]*v[0] + dir[0]*v[1] > 0:
				dir = COS45*(dir[0]-dir[1]), COS45*(dir[0]+dir[1])
			else:
				dir = COS45*(dir[0]+dir[1]), COS45*(dir[1]-dir[0])

			node = node[0] + dir[0]*step, node[1] + dir[1]*step
			path.append(node)

		return path


	def point_to_point(self):

		if len(self.anchors) != 2:
			return

		link_width = Config.link_width_cm

		self.path = []
		self.ofs: list[float] = []

		node0 = self.anchors[0].stub_mid
		dir0 = self.anchors[0].dir
		sign0 = self.anchors[0].sign
		node1 = self.anchors[1].stub_mid
		dir1 = self.anchors[1].dir
		sign1 = -self.anchors[1].sign

		self.path.append(self.anchors[0].mid)
		self.path.append(node0)
		self.ofs.append(sign0*self.anchors[0].width)

		path = self.face_target(node0, dir0, node1) 
		for node in path:
			self.path.append(node)
			self.ofs.append(sign0*link_width)
		self.ofs.append(sign0*link_width)
		m = len(self.path) - 1

		path = self.face_target(node1, dir1, node0)
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


	def paths(self):
		
		if self.target is None and len(self.anchors) < 2:
			return

		offs = self.anchors[0].sign * Config.link_width_cm / 2

		if self.target:
			self.path.append(self.anchors[0].mid)
			self.path.append(self.anchors[0].stub_mid)
			self.path.append(self.target)
			self.red_path = offset(self.path, offs)
			self.blue_path = offset(self.path, -offs)
			self.red_path[0] = self.anchors[0].red
			self.blue_path[0] = self.anchors[0].blue
			return


		for i in range(1, len(self.anchors)):
			link_path = []
			link_path.append(self.anchors[i-1].mid)
			link_path.append(self.anchors[i-1].stub_mid)
			link_path.append(self.anchors[i].back_stub_mid)
			link_path.append(self.anchors[i].mid)

			red_path = offset(link_path, offs)
			blue_path = offset(link_path, -offs)

			red_path[0] = self.anchors[i-1].red
			blue_path[0] = self.anchors[i-1].blue
			red_path[-1] = self.anchors[i].red
			blue_path[-1] = self.anchors[i].blue

			self.red_path.extend(red_path)
			self.blue_path.extend(blue_path)
			self.path.extend(link_path)
		

# picture = Picture()

# for angle in [0, 90, 180, 270]:
# 	connector = Connector()
# 	red = (0.,0.)
# 	blue = (5.,4.)
# 	dir = (cos(angle * 3.14 / 180), sin(angle * 3.14 / 180))

# 	connector.attach(red, blue, dir)
# 	# red = (200., 100.)
# 	# blue = (202., 104.)
# 	# dir = (0., -1.)
# 	# connector.attach(red, blue, dir)
# 	connector.target = (200.*dir[0], 100.*dir[1])
# 	connector.paths()

# 	# picture.add(connector.endpoints[0].red, color='red')
# 	# picture.add(connector.endpoints[0].blue, color='blue')
# 	# picture.add(connector.endpoints[0].stub_red, color='red')
# 	# picture.add(connector.endpoints[0].stub_blue, color='blue')
# 	# picture.add(connector.endpoints[0].stub_mid, color='green')
# 	# picture.add(connector.path, color='black')

# 	picture.add(connector.red_path, color='red')
# 	picture.add(connector.blue_path, color='blue')

# picture.draw()






