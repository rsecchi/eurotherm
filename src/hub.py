from numpy import argmin
from geometry import point_t, poly_t 

class Hub:

	def __init__(self):
		self.sources: list[point_t] = []
		self.target: point_t =(0.0, 0.0)
		self.paths: list[poly_t] = []


	def set_sources(self, sources: list[point_t]): 
		self.sources = sources


	def set_target(self, target: point_t):
		self.target = target


	def route(self, source:point_t) -> poly_t:

		x0, y0 = source
		x1, y1 = self.target

		path = []
		path.append(source)

		dx = abs(x1-x0)
		dy = abs(y1-y0)

		if dy > dx:
			margin = (dy - dx)
			if y0 < y1:
				path.append((x0, y0 + margin))
				path.append((x1, y1))
			else:
				path.append((x0, y0 - margin))
				path.append((x1, y1))
		else:
			margin = dx - dy	
			if x0 < x1:
				path.append((x0 + margin, y0))
			else:
				path.append((x0 - margin, y0))

			path.append((x1, y1))

		path.append((x1, y1))

		return path


	def build_paths(self):

		global picture
		delta = 5.0
		overhead = 20.0
		paths = self.paths = []

		up = [src for src in self.sources if src[1] > self.target[1]]
		down = [src for src in self.sources if src[1] <= self.target[1]]

		up.sort(key=lambda p: p[1])
		down.sort(key=lambda p: p[1], reverse=True)

		width = len(up)
		if width is []:
			return []

		halfw = width//2
		start = self.target[0] - delta * halfw

		targets = []
		levels = [self.target[1]] * width

		for i in range(width):
			idx = i
			pos = self.target[0] + delta*(i-halfw), self.target[1]
			targets.append((idx, pos))

		for src in up:
			j = argmin([abs(src[0] - t[1][0]) for t in targets])
			endpoint = targets[j]
			idx, pos = endpoint
			var = (src[0] - start)/delta
			loc = min(max(int(var), 0), width-1)
			range_min = min(loc, idx)
			range_max = max(loc, idx) + 1

			level = levels[idx]
			for k in range(range_min, range_max):
				level = max(levels[k] - delta*abs(k-idx), level)
				
				 
			path = self.route(src)
			path.append(pos)
			paths.append(path)
			dx = abs(src[0] - pos[0])
			dy = abs(src[1] - pos[1])
			levels[idx] = max(src[1] - min(dx, dy), level) + overhead
			targets.remove(endpoint)
		

