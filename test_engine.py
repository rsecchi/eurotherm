from ctypes import *


class POINT(Structure):
	_fields_ = [("x",c_double), ("y",c_double)]


class POLYGON(Structure):
	_fields_ = [("poly", POINTER(POINT)),
				("size", c_int) ]

class ROOM(Structure):
	_fields_ = [("walls", POLYGON),
				("obstacles", POINTER(POLYGON)),
				("obs_num", c_int)]


engine = CDLL("./engine.so")

def c_polygon(poly):
	l = len(poly)
	POLY = POINT*l
	tt = POLY(*poly)
	return POLYGON(tt, l)

def c_room(poly, obs):
	_room = c_polygon(poly)
	_obs_num = len(obs)

	OBS = POLYGON*_obs_num
	_obs_poly = list()
	for ob in obs:
		_obs_poly.append(c_polygon(ob))

	_obs = OBS(*_obs_poly)
	return ROOM(_room, _obs, _obs_num)


t = [(1,2),(2,1),(0,-1)]

o1 = [(0,0),(1,1)]
o2 = [(1,0),(0,1)]

r = c_room(t, [])

print(t)
engine.grid(r)


