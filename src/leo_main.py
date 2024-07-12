import os, sys
import json
import atexit

local_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(local_dir)
sys.path.append('..')
from model import Model
from components import ComponentManager
from drawing import DxfDrawing

# read configuration file into local dict
json_file = open(sys.argv[1], "r")
data = json.loads(json_file.read())
lock_name = data['lock_name']


def remove_lock():
	out = data['outfile'][:-4]+".txt"
	f = open(out, "w")
	print("Early exit", file = f)
	os.remove(lock_name)


# Acquire lock 
if os.path.exists(lock_name):
	print("ABORT: Resource busy")
open(lock_name, "w")	
atexit.register(remove_lock)


data['cfg_dir'] = os.path.dirname(sys.argv[1])

model = Model(data)
manager = ComponentManager()

outfile = data['cfg_dir'] + "/" + data['outfile'] 
dxfdrawing = DxfDrawing(outfile, model.refit, model.scale)

if not model.build_model():
	print("NEED TO PRINT OUTPUT HERE")

manager.get_components(model)


dxfdrawing.save()



