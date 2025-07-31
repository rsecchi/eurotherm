from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime

class PagePDF:

    top_margin = 200
    bottom_margin = 50
    left_margin = 50
    right_margin = 50
    font = "Helvetica"
    font_size = 12
    title_font = "Helvetica-Bold"
    title_font_size = 24

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


    def page_title(self, pdf: canvas.Canvas):
        pdf.setFont(self.title_font, self.title_font_size)
        pdf.drawString(200, 700, self.title)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(2)
        pdf.line(50, 680, 550, 680)


    def print_text(self, pdf: canvas.Canvas):
        pdf.setFont(self.font, self.font_size)
        for line in self.textlines:
            pdf.drawString(line["pos"][0], line["pos"][1], line["text"])


    def render(self, pdf: canvas.Canvas):
        self.textlines = []
        self.add_text("PagePDF render method not implemented.")
        self.print_text(pdf)
        pdf.showPage()



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
    output_file = "leonardo_report.pdf"


    def __init__(self, pagesize=A4):
        self.pdf = canvas.Canvas(self.output_file, pagesize=pagesize)
        self.width, self.height = pagesize
        self.pages: list[PagePDF] = []


    def report_title(self, title: str):
        pdf = self.pdf
        pdf.setFont(self.title_font, self.title_font_size)
        pdf.drawString(200, 700, title)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(2)
        pdf.line(50, 680, 550, 680)


    def create_cover_page(self):
        # Create a canvas for the PDF
        pdf = self.pdf

        self.report_title(self.title)

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


    def add_page(self, page: PagePDF):
        self.pages.append(page)


    def generate(self):
        self.create_cover_page()
        for page in self.pages:
            page.render(self.pdf)

        self.pdf.save()

