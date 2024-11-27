import os
import sys
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime

from code_tests.pylint.tests.functional.i.import_outside_toplevel import i

if len(sys.argv) != 2:
    print("Usage: python create_image_catalogue.py <input_folder>")
    sys.exit(1)


# Function to validate the folder
def validate_folder(folder):
    if not os.path.exists(folder):
        print(f"Error: The folder '{folder}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory.")
        sys.exit(1)

input_folder = sys.argv[1]
validate_folder(input_folder)


# Function to extract lines starting with a given text
def extract_data(input_folder, start_text, sindex, eindex):

    data = []

    if not os.path.exists(input_folder):
        print(f"Error: The folder '{input_folder}' does not exist.")
        return data 

    # Iterate over all text files in the directory
    for file_name in os.listdir(input_folder):
        if file_name.startswith("LEO_") and file_name.endswith(".txt"):
            file_path = os.path.join(input_folder, file_name)

            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.startswith(start_text):
                        data.append(float(line[sindex:eindex]))
    return data



class TextPagePDF:
   
    top_margin = 200
    bottom_margin = 50
    left_margin = 50
    right_margin = 50

    def __init__(self, row_width=12, pagesize=A4):
        self.textlines = []
        self.row_width = row_width
        self.width, self.height = pagesize
        self.pagesize = pagesize
        self.cursor = (self.left_margin, self.height - self.top_margin)
        self.title = ""

    def add_text(self, text):
        pos = self.cursor
        self.cursor = (pos[0], pos[1] - self.row_width)
        self.textlines.append({"pos": pos, "text": text})

    def add_title(self, title):
        self.title = title
        pos = self.cursor
        self.cursor = (pos[0], pos[1] - self.row_width)



class ReportPDF:

    title = "Leonardo Planner CS Report"
    title_font = "Helvetica-Bold"
    title_font_size = 24

    text_font = "Helvetica"
    text_font_size = 12

    addition_font = "Helvetica-Oblique"
    addition_font_size = 10
    addition_text = "Statistics on the Selected Floor Plans."

    author_text = "Prepared by: Eurotherm Inc."
    author_font = "Helvetica"
    author_font_size = 10

    def __init__(self, output_file, pagesize=A4):
        self.output_file = output_file
        self.pdf = canvas.Canvas(output_file, pagesize=pagesize)
        self.width, self.height = pagesize
        self.files_processed = 0


    def write_title(self, title: str):
        pdf = self.pdf
        pdf.setFont(self.title_font, self.title_font_size)
        pdf.drawString(200, 700, title)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(2)
        pdf.line(50, 680, 550, 680)


    def create_cover_page(self):
        # Create a canvas for the PDF
        pdf = self.pdf
        
        self.write_title(self.title)
        
        pdf.setFont(self.text_font, self.text_font_size)
        current_date = datetime.now().strftime("%B %d, %Y")
        pdf.drawString(250, 650, f"Date: {current_date}")
       
        # Add a note at the top
        pdf.setFont(self.addition_font, self.addition_font_size)
        pdf.drawString(150, 600, self.addition_text)
        
        # Draw the company or author name at the bottom
        pdf.setFont(self.author_font, self.author_font_size)
        pdf.drawString(230, 100, self.author_text)
        
        pdf.showPage()



    def distribution(self, data, xlabel: str):
        # Step 1: Sort the data

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


    def add_drawing(self, image_path):

        image = Image.open(image_path)
        pdf = self.pdf
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
        pdf.drawImage(image_path, x, y,
                width=image.width, height=image.height, mask="auto")

        # Add the file name below the image
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(page_width / 2, page_height - 30, file_name)


        # Add the content of the corresponding .txt file (if it exists)
        txt_file_path = os.path.join(input_folder, 
                           os.path.splitext(file_name)[0] + ".txt")
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

        self.files_processed += 1
        pdf.showPage()


    def add_page(self, page: TextPagePDF):
        pdf = self.pdf

        self.write_title(page.title)

        pdf.setFont(self.text_font, self.text_font_size)
        for line in page.textlines:
            pos = line["pos"]
            text = line["text"]
            pdf.drawString(pos[0], pos[1], text)

        pdf.showPage()


    def save(self):
        self.pdf.save()




def make_stats_page(report: ReportPDF, folder: str):

    tot_area = extract_data(folder, "Total area ", 39, 44)
    active_area = extract_data(folder, "Total active area ", 39, 44)
    passive_area = extract_data(folder, "Total passive area ", 39, 44)
    norm_area = extract_data(folder, "Normal area ", 39, 44)
    norm_act_area = extract_data(folder, "Normal active area ", 39, 44)
    # norm_psv_area = extract_data(folder, "Normal passive area ", 39, 44)

    perc_active = 100 * sum(active_area) / sum(tot_area) 
    perc_passive = 100 * sum(passive_area) / sum(tot_area) 
    perc_normal = 100 * sum(norm_area) / sum(tot_area)
    perc_normal_act = 100 * sum(norm_act_area) / sum(tot_area)
    # perc_normal_psv = 100 * sum(norm_psv_area) / sum(tot_area)


    page = TextPagePDF()
    page.add_title("Main Statistics")
    page.add_text(f"Total Area: {sum(tot_area):0.2f}")
    page.add_text(f"Active Area: {sum(active_area):0.2f}")
    page.add_text(f"Passive Area: {sum(passive_area):0.2f}")
    page.add_text(f"Normal Area: {sum(norm_area):0.2f}")
    page.add_text(f"Normal Active Area: {sum(norm_act_area):0.2f}")
    page.add_text("")

    page.add_text(f"Percentage Active: {perc_active:0.2f}%")
    page.add_text(f"Percentage Passive: {perc_passive:0.2f}%")
    page.add_text(f"Percentage Normal: {perc_normal:0.2f}%")
    page.add_text(f"Percentage Normal Active: {perc_normal_act:0.2f}%")
    # page.add_text(f"Percentage Normal Passive: {perc_normal_psv:0.2f}%")
    page.add_text("")

    report.add_page(page)



# Create a PDF file to store the images
output_pdf = "leonardo_report.pdf"
report = ReportPDF(output_pdf)
report.create_cover_page()

# Add a page with statistic's Data
make_stats_page(report, input_folder)



# Process each PNG file with the required naming pattern
pattern_prefix = "LEO_"
files_processed = 0

# Iterate over all files in the directory
for file_name in sorted(os.listdir(input_folder)):
    if file_name.startswith(pattern_prefix) and file_name.endswith(".png"):
        image_path = os.path.join(input_folder, file_name)
        report.add_drawing(image_path)

# Save the PDF if any files were processed
if report.files_processed > 0:
    report.save()
    print(f"PDF created successfully "
          + f"with {files_processed} images: {output_pdf}")
else:
    print(f"No files matching the pattern '{pattern_prefix}*.png'"
          + f" were found in '{input_folder}'.")

