

class Element:
	def __init__(self, name, value):
		self.name = name
		self.value = value

	def __str__(self):
		return f'{self.name} = {self.value}'

	def __repr__(self):
		return f'{self.name} = {self.value}'


	def print_val(self):
		print(end='<input type="text" ') 

		if not type(self.value) == str:
			print(end='style="text-align:right;width:300px;" ')
		else:
			print(end='style="width:300px;" ')

		print(end='value="' + str(self.value) + '">')



class Section:

	valid_types = [int, float, str]

	def __init__(self, id):
		self.id = id
		self.content = []

	def add(self, name: str, value):
		if not type(value) in self.valid_types:
			return

		self.content.append(Element(name, value))

	def print(self):

		print("<div class='section' id=\"" + self.id + "\">")

		print("<table>")
		print("<th width='300'>Variable</th>")
		print("<th>Value</th>")
		for element in self.content:
			print("<tr>")
			print("<td>" + element.name + "</td>")
			print("<td>")
			element.print_val()
			print("</td>")
			print("</tr>")
		print("</table>")

		print("</div>")



class Page:
	def __init__(self, title, url, content):
		self.title = title
		self.url = url
		self.content = content

	def __str__(self):
		return f'{self.title} - {self.url}'

	def __repr__(self):
		return f'{self.title} - {self.url}'

