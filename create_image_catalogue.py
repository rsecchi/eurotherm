import os
import sys
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from code_tests.pylint.tests.functional.i.import_outside_toplevel import i

# Function to validate the folder
def validate_folder(folder):
    if not os.path.exists(folder):
        print(f"Error: The folder '{folder}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory.")
        sys.exit(1)

# Get input folder from command-line arguments
if len(sys.argv) != 2:
    print("Usage: python create_image_catalogue.py <input_folder>")
    sys.exit(1)

input_folder = sys.argv[1]
validate_folder(input_folder)

# Define output PDF file
output_pdf = "output.pdf"

# PDF page size (A4)
page_width, page_height = A4

# Create a canvas for the PDF
pdf = canvas.Canvas(output_pdf, pagesize=A4)

# Process each PNG file with the required naming pattern
pattern_prefix = "LEO_"
files_processed = 0

for file_name in sorted(os.listdir(input_folder)):
    if file_name.startswith(pattern_prefix) and file_name.endswith(".png"):
        # Open the image
        image_path = os.path.join(input_folder, file_name)
        image = Image.open(image_path)
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

        # Create a new page for the next image
        pdf.showPage()
        files_processed += 1

# Save the PDF if any files were processed
if files_processed > 0:
    pdf.save()
    print(f"PDF created successfully "
          + f"with {files_processed} images: {output_pdf}")
else:
    print(f"No files matching the pattern '{pattern_prefix}*.png'"
          + f" were found in '{input_folder}'.")

