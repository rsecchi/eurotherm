import re
import os


class Dataset:
    def __init__(self):
        self.data: list[dict] = []


    def add_file(self, filename: str):
        if os.path.isfile(filename):
            self.data.append({"filename": filename})


    def add_folder(self, folder_path: str, regex: str=r".*"):
        pattern = re.compile(regex)

        for item in os.listdir(folder_path):
            full_path = os.path.join(folder_path, item)
            if (os.path.isfile(full_path)
                    and pattern.match(item)):
                self.data.append({"filename": full_path})


    def grep_files(self, regex: str, field: int, label: str):

        pattern = re.compile(regex)
        for data in self.data:
            filename = data["filename"]
            with open(filename, 'r', encoding='utf-8') as file:
                doc = file.read()
                vals = pattern.findall(doc)
                elems = []
                for val in vals:
                    fields = val.split()
                    elem = fields[field] if field<len(fields) else None
                    if elem is not None:
                        elems.append(elem)
                data[label] = elems


