import os, sys
import json
import atexit
import conf

from model import Model
from components import Components
from drawing import DxfDrawing
from excel import XlsDocument
from report import Report

class App:

	def read_configuration(self, filename):
		self.json_file = open(filename, "r")
		self.data = json.loads(self.json_file.read())
		self.lock_name = self.data['lock_name']
		self.outfile = conf.spool + self.data['outfile'][:-4]+".log"
		self.text = str()


	def remove_lock(self):
		os.remove(self.lock_name)
		f = open(self.outfile, "w")
		print(self.text, file = f)


	def acquire_lock(self):
		if os.path.exists(self.lock_name):
			print("ABORT: Resource busy")
		open(self.lock_name, "w")
		atexit.register(self.remove_lock)


	def __init__(self):
		self.read_configuration(sys.argv[1])
		self.acquire_lock()

		self.model = Model(self.data)
		self.components = Components(self.model)
		self.dxf = DxfDrawing(self.model)
		self.xls = XlsDocument(self.components)
		self.report = Report(self.components)

		self.dxf.import_floorplan(self.model.input_file)
		self.dxf.import_blocks(self.data["ptype"])

		# Create output file for elaborate
		if not self.model.build_model():
			self.dxf.output_error()
			return

		self.report.set_text(self.model.text)

		self.components.get_components()

		if not self.model.refit:
			self.dxf.draw_model()

		self.dxf.save()

		self.components.count_components(self.dxf.doc)
		self.xls.save_in_xls()

		self.report.make_report()
		self.report.save_report()

App()

