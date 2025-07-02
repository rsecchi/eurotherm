from typing import List, Optional
from geometry import midpoint, norm, offset, point_t, xprod
from reference_frame import adv, diff, mul
from settings import Config


class Anchor:

	def __init__(self, red: point_t, blue: point_t, dir: point_t):
		self.red = red
		self.blue = blue
		self.dir = norm(dir)
		self.mid = midpoint(red, blue)

		delta_red = diff(self.mid, red)
		delta_blue = diff(self.mid, blue)
		proj_red = xprod(self.dir, delta_red)
		proj_blue = xprod(self.dir, delta_blue)

		ortho = (-self.dir[1], self.dir[0])
		self.sign = 1 if xprod(ortho, delta_red) > 0 else -1


		len_red = Config.stub_length_cm + proj_red
		len_blue = Config.stub_length_cm + proj_blue 
		stub_red = mul(len_red, self.dir)
		stub_blue = mul(len_blue, self.dir)
		back_red = mul(-len_red, self.dir)
		back_blue = mul(-len_blue, self.dir)

		self.stub_red = adv(stub_red, red)
		self.stub_blue = adv(stub_blue, blue)
		self.back_stub_red = adv(back_red, red)
		self.back_stub_blue = adv(back_blue, blue)
		self.stub_mid = midpoint(self.stub_red, self.stub_blue)
		self.back_stub_mid = midpoint(self.back_stub_red, self.back_stub_blue)

			

class Connector:
	def __init__(self):
		self.anchors: List[Anchor] = []
		self.target: Optional[point_t] = None
		self.path: List[point_t] = []
		self.red_path: List[point_t] = []
		self.blue_path: List[point_t] = []
	
	def attach(self, red: point_t, blue: point_t, dir: point_t):
		endpoint = Anchor(red=red, blue=blue, dir=dir)
		self.anchors.append(endpoint)
		

	def paths(self):
		print("Ma che ohh", self.target, len(self.anchors))
		
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






