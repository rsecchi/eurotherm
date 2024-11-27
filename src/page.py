

class Section:

	def __init__(self, lang="default"):
		self.text = "<div class='section'>\n"
		self.lang = lang


	def indent(self):
		self.text += "\t"


	def header(self, text):

		self.indent()
		if type(text) == dict:
			self.text += "<h2>%s</h2>\n" % text[self.lang]
		else:
			self.text += "<h2>%s</h2>\n" % text


	def paragraph(self, text):

		self.indent()
		if type(text) == dict:
			self.text += "<p>%s</p>\n" % text[self.lang]
		else:
			self.text += "<p>%s</p>\n" % text


	def close(self):
		self.text += "</div>\n"

