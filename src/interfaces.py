from typing import Any
from ezdxf.entities.insert import Insert


class Accessor:

	def __init__(self, obj: Any, attrib: str):
		self._obj = obj
		self._attrib = attrib

	def get(self):
		return getattr(self._obj, self._attrib, None) 

	def set(self, value: Any):
		setattr(self._obj, self._attrib, value)


class InsertRef:

	def __init__(self, obj: Any, attrib: str):
		self._obj = obj
		self._attrib = attrib

	def get(self):
		return getattr(self._obj, self._attrib, None) 

	def set(self, value: Insert):
		setattr(self._obj, self._attrib, value)

