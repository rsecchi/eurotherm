from connector import Anchor, Connector
from geometry import point_t, poly_t


class Hub:
	slot_width = 0.
	fit_clearance = 0.
	link_width = 0.
	stub_length = 0.
	fit_extension = 0.

	def __init__(self):
		self.anchors: list[Anchor] = []
		self.target: point_t =(0., 0.)
		self.connectors: list[Connector] = []


	def add_anchor(self, anchor: Anchor):
		self.anchors.append(anchor)


	def set_target(self, target: point_t):
		self.target = target

	def route(self, src:point_t, dst:point_t) -> poly_t:

		x0, y0 = src
		x1, y1 = dst

		path = []
		path.append(src)

		dx = abs(x1-x0)
		dy = abs(y1-y0)

		if dy > dx:
			margin = (dy - dx)
			if y0 < y1:
				path.append((x0, y0 + margin))
			else:
				path.append((x0, y0 - margin))
		else:
			margin = dx - dy	
			if x0 < x1:
				path.append((x0 + margin, y0))
			else:
				path.append((x0 - margin, y0))


		path.append((x1, y1))

		return path


	def build_paths(self):

		for anchor in self.anchors:
			anchor.face_target(self.target)

		up: list[Anchor] = []
		down: list[Anchor] = []

		for anchor in self.anchors:
			if anchor.pos[1] > self.target[1]:
				up.append(anchor)
			else:
				down.append(anchor)
			
		up.sort(key=lambda anchor: anchor.pos[1])
		down.sort(key=lambda anchor: anchor.pos[1], reverse=True)

		self.build_side(up, True)
		self.build_side(down, False)


	def build_side(self, anchors: list[Anchor], upside: bool):

		width = len(anchors)
		if width == 0:
			return []

		targets = []
		slot_width = self.slot_width
		overpass = self.fit_clearance

		target_x, hub_centre = self.target
		if upside:
			target_y = hub_centre + self.stub_length
		else:
			target_y = hub_centre - self.stub_length
		left_margin = target_x - slot_width * (width//2)
		levels = [target_y] * width

		# prepare target slots
		for i in range(width):
			slot_x = left_margin + i * slot_width
			targets.append( {"index": i, "x_val": slot_x} )


		for anchor in anchors:

			# choose the closest available slot for the anchor
			anchor_x, anchor_y = anchor.pos
			offset_x = float("inf")
			selected_target = targets[0] 
			for target in targets:
				delta_x = abs(anchor_x - target["x_val"])
				if delta_x < offset_x:
					offset_x = delta_x
					selected_target = target
			target_idx = selected_target["index"]
			target_x = selected_target["x_val"]

			# calculate the initial hub slot for the anchor
			slot = (anchor_x - left_margin)/slot_width
			slot = min(max(int(slot), 0), width - 1)

			# calculate the path to align the anchor with the target
			level = levels[target_idx]
			range_min = min(slot, target_idx)
			range_max = max(slot, target_idx) + 1
			for k in range(range_min, range_max):
				slope = slot_width * abs(k - target_idx)
				if upside:
					level = max(levels[k] - slope, level)
				else:
					level = min(levels[k] + slope, level) 
			path = self.route(anchor.pos, (target_x, level))
			path.append((target_x, hub_centre))

			# create connector
			connector = Connector() 
			connector.attach_anchor(anchor)
			connector.link_width = self.link_width
			connector.build_from_path(path)
			self.connectors.append(connector)

			# update the level for the target slot
			dx = abs(anchor_x - target_x)
			dy = abs(anchor_y - target_y)
			margin = min(dx, dy)
			if upside:
				levels[target_idx] = max(anchor_y - margin, level) + overpass
			else:
				levels[target_idx] = min(anchor_y + margin, level) - overpass
			targets.remove(selected_target)

		
