import os, sys
import json
import atexit

from model import Model
from components import ComponentManager
from drawing import DxfDrawing


class App:

	def read_configuration(self, filename):
		self.json_file = open(filename, "r")
		self.data = json.loads(self.json_file.read())
		self.lock_name = self.data['lock_name']


	def remove_lock(self):
		out = self.data['outfile'][:-4]+".txt"
		f = open(out, "w")
		print("Early exit", file = f)
		os.remove(self.lock_name)


	def acquire_lock(self):
		if os.path.exists(self.lock_name):
			print("ABORT: Resource busy")
		open(self.lock_name, "w")	
		atexit.register(self.remove_lock)


	def __init__(self):
		self.read_configuration(sys.argv[1])
		self.acquire_lock()

		self.data['cfg_dir'] = os.path.dirname(sys.argv[1])

		self.model = Model(self.data)
		self.manager = ComponentManager()
		self.dxf = DxfDrawing()

		self.dxf.import_floorplan(self.model.input_file)

		if not self.model.refit:
			# build and elaborate model
			if not self.model.build_model():
				self.dxf.output_error(self.model.processed)
				return

			self.manager.get_components(self.model)

			if not self.model.refit:
				self.dxf.draw_model(self.model)

		self.outfile = self.data['cfg_dir']+"/"+self.data['outfile'] 
		self.dxf.save(self.outfile)



App()

