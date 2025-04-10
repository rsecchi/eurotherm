import os
import sys
import json
import atexit
import conf

from model import Model
from components import Components
from bill import Bill
from drawing import DxfDrawing, Preview
from excel import XlsDocument
from report import Report
from settings import Config


class App:

	def read_configuration(self, filename):
		self.json_file = open(filename, "r")
		self.data = json.loads(self.json_file.read())
		self.lock_name = self.data['lock_name']
		self.outfile = conf.spool + self.data['outfile'][:-4] + ".log"
		self.text = str()

	def remove_lock(self):
		os.remove(self.lock_name)
		f = open(self.outfile, "w")
		print(self.text, file=f)

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
		self.bill = Bill(self.report)
		self.preview = Preview(self.model)

		self.dxf.import_layer(self.model.input_file, Config.input_layer)

		# Create output file for elaborate
		if not self.model.build_model():
			self.report.text += self.model.text
			self.report.save_report()
			self.dxf.output_error()
			self.preview.draw_model()
			self.preview.save()
			return

		if not self.model.refit:
			self.dxf.import_blocks(self.data["ptype"])
			self.components.get_components()
			self.dxf.draw_model()
			self.dxf.save()
			self.preview.draw_model()
			self.preview.save()
		else:
			layers = [
				Config.layer_text,
				Config.layer_box,      
				Config.layer_panel,    
				Config.layer_panelp,   
				Config.layer_link,     
				Config.layer_error,    
				Config.layer_lux,      
				Config.layer_probes,   
				Config.layer_struct,   
				Config.layer_collector,
				Config.layer_fittings] 
			for layer in layers:
				self.dxf.import_layer(self.model.input_file, layer)

		# count components and save
		self.components.count_components(self.dxf.doc)
		self.dxf.save()

		self.xls.save_in_xls()

		self.components.air_handling()
		self.report.set_text(self.model.text)
		self.report.insert_allocation_report()
		self.report.append_text(self.components.text)
		self.report.save_report()

		self.bill.make_bill()
		self.bill.save()


App()
