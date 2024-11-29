from math import sqrt
import os
import sys
from typing import Optional

from PIL import Image
from reportlab.pdfgen import canvas
from utils.dataset import Dataset
from utils.reportPDF import ReportPDF
from utils.reportPDF import PagePDF

import matplotlib.pyplot as plt


if len(sys.argv) != 2:
    print("Usage: python create_image_catalogue.py <input_folder>")
    sys.exit(1)


class TxtData(Dataset):

    def __init__(self, folder: str):
        self.folder = folder
        self.tags = []
        self.data: list[dict] = []
        self.failed = []
        self.stats = []


    def validate_folder(self):

        if not os.path.exists(self.folder):
            print(f"Error: The folder '{self.folder}' does not exist.")
            sys.exit(1)

        if not os.path.isdir(self.folder):
            print(f"Error: '{self.folder}' is not a directory.")
            sys.exit(1)


    def add_tag(self, tag: str, sindex: int, eindex: int):
        self.tags.append({"tag": tag, "sindex": sindex, "eindex": eindex})


    def points(self, tag1: str, tag2: str):
        vals = []
        for item in self.data:
            vals.append((item[tag1], item[tag2]))
        return vals


    def ratio(self, tag1: str, tag2: str):
        vals = []
        for item in self.data:
            ratio = (item[tag1], item[tag2] / item[tag1])
            vals.append(ratio)
        return vals

    def extract_tag(self, doc: str, tag: str, sindex: int, eindex: int):
        for line in doc.split("\n"):
            if line.startswith(tag):
                return float(line[sindex:eindex])
        return None


    def calc_stats(self):

        for tag in self.tags:
            entry = {"tag": tag["tag"]}
            items = [item[tag["tag"]] for item in self.data]
            entry["mean"] = sum(items) / len(items)
            entry["median"] = items[len(items) // 2]
            entry["min"] = min(items)
            entry["max"] = max(items)
            diffs = [(x - entry["mean"])**2 for x in items]
            entry["stdev"] = sqrt(sum(diffs) / len(items))
            self.stats.append(entry)


    def sort_data(self, tag: str):
        self.data = sorted(self.data, key=lambda x: x[tag]) 


    def extract_data(self):

        data = self.data
        if not os.path.exists(data_folder):
            print(f"Error: The folder '{data_folder}' does not exist.")
            return data

        # Iterate over all text files in the directory
        for file_name in os.listdir(data_folder):
            if file_name.startswith("LEO_") and file_name.endswith(".txt"):
                file_path = os.path.join(data_folder, file_name)

                with open(file_path, 'r', encoding='utf-8') as file:
                    doc = file.read()
                    element = {}
                    element["file"] = file_path
                    for tag in self.tags:
                        tag_name = tag["tag"]
                        si = tag["sindex"]
                        ei = tag["eindex"]

                        val = self.extract_tag(doc, tag_name, si, ei)
                        if val is not None:
                            element[tag_name] = val

                data.append(element)

        self.failed = [item for item in self.data if len(item.keys()) < 2]
        self.data = [item for item in self.data if len(item.keys()) >= 2]


class TextPagePDF(PagePDF):
    def __init__(self):
        super().__init__()

    def render(self, pdf: canvas.Canvas):
        self.page_title(pdf)
        self.print_text(pdf)
        return super().render(pdf)


class GraphPagePDF(PagePDF):

    def __init__(self):
        super().__init__()
        self.graphs = []


    def add_plot(self, data, graphname: str, xlabel="X", ylabel="Y"):
        graph = {
            "data": data,
            "graphname": graphname,
            "xlabel": xlabel,
            "ylabel": ylabel
        }
        self.graphs.append(graph)


    def make_plot(self, graph: dict):
        graphname = graph["graphname"]
        xlabel = graph["xlabel"]
        ylabel = graph["ylabel"]
        data = graph["data"]

        x, y = zip(*data)
        plt.scatter(x, y,
                color='blue',
                s=50, alpha=0.7,
                edgecolors='black',
                label='Data points')

        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel(ylabel, fontsize=14)
        plt.grid(True)
        plt.savefig(graphname, format='png', dpi=300)


    def render(self, pdf: canvas.Canvas):

        yc = self.height - 120
        for graph in self.graphs:
            self.make_plot(graph)
            image = Image.open(graph["graphname"])
            size = image.size
            width = self.width - 200
            height = width * size[1] / size[0]
            xc = (self.width - width) / 2
            yc -= height + 50
            pdf.drawImage(graph["graphname"], xc, yc,
                          width=width, height=height, mask="auto")
        pdf.showPage()


    def distribution(self, data, xlabel: str):

        plt.hist(data, bins=25, edgecolor='black',
                 alpha=0.7, color='skyblue', label="Histogram")

        # Set plot labels and title
        title = f"mean: {sum(data)/len(data):0.2f}," + \
                f"median: {data[len(data)//2]:0.2f}, " + \
                f"min: {min(data):0.2f}, max: {max(data):0.2f}"
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel('Frequency / Density')
        plt.legend()

        # Save the plot as a PNG file
        plt.savefig(xlabel+".png", format='png')

        # Close the plot to free memory
        plt.close()

        return xlabel+".png"




class DrawingPagePDF(PagePDF):

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path


    def render(self, pdf: canvas.Canvas):

        image = Image.open(self.image_path)
        page_width, page_height = self.width, self.height
        # image = image.convert("RGBA")

        # background = Image.new("RGBA", image.size, (255,255,255,255))
        # image = Image.alpha_composite(background, image)

        # Resize image to fit within the PDF page
        max_width, max_height = page_width - 100, page_height - 150 
        image.thumbnail((max_width, max_height))

        # Calculate image position (centre it on the page)
        x = (page_width - image.width) / 2
        y = page_height - image.height - 30

        # Draw the image on the PDF
        pdf.drawImage(self.image_path, x, y,
                width=image.width, height=image.height, mask="auto")

        # Add the file name below the image
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(page_width / 2, page_height - 30, 
                              self.image_path)

        # Add the content of the corresponding .txt file (if it exists)
        txt_file_path = os.path.splitext(self.image_path)[0] + ".txt"

        if os.path.exists(txt_file_path):
            with open(txt_file_path, "r", encoding="utf-8") as txt_file:
                txt_content = txt_file.read()
                line_no = 0
                xpos = 50
                for line in txt_content.split("\n"):
                    line_no += 1
                    if line[:12] == "Rooms report":
                        line_no = 1
                        xpos = 300
                    pdf.setFont("Courier", 6)
                    pdf.drawString(xpos,
                        page_height - image.height - 50 - line_no * 10, line)

        pdf.showPage()



# Create a PDF report
report = ReportPDF()

data_folder = sys.argv[1]
data = TxtData(data_folder)

data.add_tag("Total area ", 39, 44)
data.add_tag("Total active area ", 39, 44)
data.add_tag("Total passive area ", 39, 44)
data.add_tag("Normal area ", 39, 44)
data.add_tag("Normal active area ", 39, 44)
data.extract_data()
data.sort_data("Total area ")
data.calc_stats()


# Add a page with the main statistics
calcpage = TextPagePDF()
calcpage.add_title("Main Statistics")
for item in data.stats:
    txt  = f"{item['tag']:20}"
    txt += f" {item['mean']:8.2f}"
    txt += f" {item['stdev']:8.2f}"
    calcpage.add_text(txt)
report.add_page(calcpage)


# Add a page with the coordinate plot
graph = GraphPagePDF()
points = data.ratio("Total area ", "Total active area ")
graph.add_plot(points, "area_plot.png", "Tot. area[m2] ", "Active area [m2]")
report.add_page(graph)


files_processed = 0
for item in data.data:
    file_name = os.path.basename(item["file"])
    image_path = os.path.join(data_folder, 
            os.path.splitext(file_name)[0] + ".png")
    if os.path.exists(image_path):
        drawing_page = DrawingPagePDF(image_path)
        report.add_page(drawing_page)
        files_processed += 1


# Iterate over all files in the directory

report.generate()


