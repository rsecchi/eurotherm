import os, sys
import json
import atexit

from model import Model
from components import ComponentManager
from drawing import DxfDrawing
from excel import XlsDocument

class App:

	def read_configuration(self, filename):
		self.json_file = open(filename, "r")
		self.data = json.loads(self.json_file.read())
		self.lock_name = self.data['lock_name']


	def remove_lock(self):
		os.remove(self.lock_name)
		out = self.data['outfile'][:-4]+".txt"
		f = open(out, "w")
		print("Exit with error", file = f)


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
		self.xls = XlsDocument(self.data)

		self.dxf.import_floorplan(self.model.input_file)
		self.dxf.import_blocks(self.data["ptype"])


		# Create output file for elaborate
		self.outfile = self.data['cfg_dir']+"/"+self.data['outfile'] 
		if not self.model.refit:
			if not self.model.build_model():
				self.dxf.output_error(self.model.processed)
				return

			self.manager.get_components(self.model)

			if not self.model.refit:
				self.dxf.draw_model(self.model)

			self.dxf.save(self.outfile)


		if not self.model.refit:
			self.manager.count_components(self.model, self.dxf.doc)
			self.xls.save_in_xls(self.model)


App()

