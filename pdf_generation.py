import fitz
import os 
from pdf2image import convert_from_path

def replace_pdf_text(input_pdf_path, output_pdf_path, body_text_locations, new_texts):
    doc = fitz.open(input_pdf_path)
    
    text_index = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Remove existing body text
        for rect in body_text_locations:
            if isinstance(rect, tuple) and len(rect) == 4:
                rect = fitz.Rect(*rect)
            page.add_redact_annot(rect)
        page.apply_redactions()

        # Add new text
        for rect in body_text_locations:
            if text_index < len(new_texts):
                if isinstance(rect, tuple) and len(rect) == 4:
                    rect = fitz.Rect(*rect)
                page.insert_textbox(rect, new_texts[text_index], fontsize=11, fontname="helv",
                                    align=fitz.TEXT_ALIGN_LEFT)
                text_index += 1
            else:
                break  # No more new texts to add

        if text_index >= len(new_texts):
            break  # No more new texts to add
    
    # Save the modified PDF
    doc.save(output_pdf_path)
    doc.close()

# Image and font size for footer and header
LOGO_SIZE = (50,25) 
FONT_NAME = "helv"
HEADER_FONT_SIZE = 10

# Image and font size for Body(14 for Easy Read)
IMAGE_SIZE = (100,100)
BODY_FONT_SIZE = 14

# Margin for header/footer and margins of the sides of document
MARGIN_TOP = 25
MARGIN_BOTTOM = 25
MARGIN_SIDES = 40
MINIMUM_VERTICAL_MARGIN = 10

def measure_text_width(text, font_size):
    font = fitz.Font(FONT_NAME)
    text_width = font.text_length(text,font_size)
    return text_width


def add_header_footer(page, header_image, header_text, footer_image, footer_text):
    # Adding header image and text
    page.insert_image(fitz.Rect(MARGIN_SIDES, MARGIN_TOP - LOGO_SIZE[1], 
                                MARGIN_SIDES + LOGO_SIZE[0], MARGIN_TOP),
                      filename=header_image)
    page.insert_text((MARGIN_SIDES + LOGO_SIZE[0] + 10, MARGIN_TOP-8), 
                     header_text, fontname=FONT_NAME, fontsize=HEADER_FONT_SIZE)
    # Draw line below header
    page.draw_line(
        p1=(MARGIN_SIDES, MARGIN_TOP),
        p2=(page.rect.width - MARGIN_SIDES, MARGIN_TOP)
    )

    # Adding footer image on the right and text to the left of it
    page_height = page.rect.height
    footer_image_rect = fitz.Rect(page.rect.width - MARGIN_SIDES - LOGO_SIZE[0], 
                                  page_height - MARGIN_BOTTOM, 
                                  page.rect.width - MARGIN_SIDES, 
                                  page_height - MARGIN_BOTTOM + LOGO_SIZE[1])
    page.insert_image(footer_image_rect, filename=footer_image)
    
    # Position footer text to the left of the footer image
    footer_text_x = footer_image_rect.x0 - 10 - measure_text_width(footer_text, HEADER_FONT_SIZE)
    page.insert_text((footer_text_x, page_height - 10), 
                     footer_text, fontname=FONT_NAME, fontsize=HEADER_FONT_SIZE)
    page.draw_line(
        p1=(MARGIN_SIDES, page_height - MARGIN_BOTTOM),
        p2=(page.rect.width - MARGIN_SIDES, page_height - MARGIN_BOTTOM)
    )


def calculate_group_height(page, group_text):
    """
    Calculate the height of a group based on the image and the text.

    Parameters:
    - page: The current PDF page.
    - group_image_path: Path to the group's image.
    - group_text: The text content of the group.

    Returns:
    - Total height required for the group.
    """
    # Use default scaled image size
    image_height = IMAGE_SIZE[1]
    image_width = IMAGE_SIZE[0]

    # Approximate number of lines based on text length and max_text_width
    max_text_width = page.rect.width - 2*MARGIN_SIDES - image_width - 10

    parts = group_text.splitlines(keepends=True)
    lines = []
    current_line = ""
    for part in parts:
        # Check if the part ends with a newline
        if "\n" in part:
            # Split the part into words without the newline
            words = part.strip().split()
            # If there are no words, the line only consists of blank
            if not words:
                current_line = '\n'
            for word in words:
                test_line = f"{current_line} {word}".strip()
                test_width = measure_text_width(test_line, BODY_FONT_SIZE)
                if test_width <= max_text_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:  # Add the current line before the explicit line break
                lines.append(current_line)
                current_line = ""  # Reset for the next part
        else:
            # Treat parts without newlines as normal text
            words = part.strip().split()
            for word in words:
                test_line = f"{current_line} {word}".strip()
                test_width = measure_text_width(test_line, BODY_FONT_SIZE)
                if test_width <= max_text_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

    # Append any remaining text
    if current_line:
        lines.append(current_line)

    line_count = len(lines)
    line_height = BODY_FONT_SIZE * 1.5  # 1.5 factor for line spacing
    text_height = (line_count * line_height) # Height of all lines combined + padding

    # Group height is the maximum of image height and text height
    group_height = max(image_height, text_height)
    return group_height

# Function to add groups with dynamic spacing
def add_groups(page, groups, num_groups, max_height):
    total_group_height = 0
    n = 0
    for i in range(len(groups)):
        tmp_image, tmp_text = groups[i]
        tmp_height = calculate_group_height(page,tmp_text)
        if total_group_height + tmp_height > (max_height) :
            break
        else:
            total_group_height += tmp_height
            n += 1
    n = min(n, num_groups)
    vertical_margin = (max_height - total_group_height) / n

    y_position = MARGIN_TOP + LOGO_SIZE[1] + 10

    for i in range(n):
        if i >= len(groups):
            break  # No more groups to add
        group_image, group_text = groups[i]

        # Insert group image and text
        page.insert_image(fitz.Rect(MARGIN_SIDES, y_position, MARGIN_SIDES + IMAGE_SIZE[0], y_position + IMAGE_SIZE[1]), 
                          filename=group_image)  # Adjust width/height as needed
        text_x = MARGIN_SIDES + IMAGE_SIZE[0] + 10  # 10 units padding on left
        text_y = y_position
        group_height = calculate_group_height(page, group_text)
        page.insert_textbox(
            fitz.Rect(
                text_x,
                text_y,
                page.rect.width - MARGIN_SIDES,
                text_y + group_height + 5 # 5 units padding at bottom
            ),
            group_text,
            fontname=FONT_NAME,
            fontsize=BODY_FONT_SIZE,
            align=fitz.TEXT_ALIGN_LEFT,
            color=(0, 0, 0),
            overlay=True
        )
        page.draw_line(
        p1=(MARGIN_SIDES, MARGIN_TOP),
        p2=(page.rect.width - MARGIN_SIDES, MARGIN_TOP)
        )
        y_position += group_height + vertical_margin
    # Return number of groups added
    return n

# Generate PDF based on specified group count per page
def generate_pdf(output_path, header_image, header_text, footer_image, footer_text, all_groups, groups_per_page):
    doc = fitz.open()
    i = 0
    
    while i < len(all_groups):
        page = doc.new_page()
        # Add header and footer
        add_header_footer(page, header_image, header_text, footer_image, footer_text)

        # Adds the maximum possible number of groups (up to `groups_per_page`) that can fit in the available space. 
        max_height = page.rect.height - MARGIN_TOP - MARGIN_BOTTOM - 2*LOGO_SIZE[1] - MINIMUM_VERTICAL_MARGIN * (groups_per_page - 1)
        n = add_groups(page, all_groups[i:i + groups_per_page], groups_per_page, max_height)

        # Advance the group index by the number of groups placed on this page
        i += n

    # Save the document
    doc.save(output_path)
    doc.close()



## ALL CODE BELOW IS JUST A TEST WITH EXAMPLE.
output_path = "app/static/pdf/output.pdf"

# Define header and footer information
header_image = "app/static/test_images/logo.png"  # Replace with actual image path
header_text = "Header: Sample PDF Document"
footer_image = "app/static/test_images/logo.png"  # Replace with actual image path
footer_text = "Footer: Page Information"


# Specify the number of groups per page
# Different templates would be different groups_per_page.
groups_per_page = 4

# Constants for PDF processing
PDF_PATH = "app/static/pdf/output.pdf"
OUTPUT_DIR = "app/static/pdf2image"

def compile_info_for_pdf(text: list, image_paths: list[tuple[str, str]], template: int = 3):
    all_groups = []
    for i in range(len(text)):
        all_groups.append([image_paths[i][1], text[i]])
        
    # Generate the PDF with the sample data
    generate_pdf(output_path, header_image, header_text, footer_image, footer_text, all_groups, template)
    generate_all_images(output_path, OUTPUT_DIR)
    TOTAL_PAGES = get_page_count(output_path)
    page_text_boxes = populate_text_boxes(TOTAL_PAGES, text, template)
    
    # Create a mapping between `page_text_boxes` and `all_groups`
    mapping = {}

    # Initialize mapping in order
    list_index = 0
    for page, boxes in page_text_boxes.items():
        for box in boxes.keys():
            if list_index < len(all_groups):
                mapping[(page, box)] = list_index
                list_index += 1
    
    
    return TOTAL_PAGES, page_text_boxes, all_groups, mapping
        
def caller(text, template):
    generate_pdf(output_path, header_image, header_text, footer_image, footer_text, text, template)
    generate_all_images(output_path, OUTPUT_DIR)
    TOTAL_PAGES = get_page_count(output_path)
    
    temp = []
    for i in text:
        temp.append(i[1])
    page_text_boxes = populate_text_boxes(TOTAL_PAGES, temp, template)
    
    return TOTAL_PAGES, page_text_boxes
    
# Function to update text in both dictionary and list
def update_text(l, d, map, page, box, new_text):
    # Update the dictionary
    if page in d and box in d[page]:
        d[page][box] = new_text
        
        # Update the corresponding list
        list_index = map.get((page, box))
        if list_index is not None:
            l[list_index][1] = new_text

def get_page_count(pdf_file):
    """
    Returns the total number of pages in the PDF file.
    """
    doc = fitz.open(pdf_file)  # Open the PDF document
    page_count = len(doc)  # Get the number of pages
    doc.close()  # Close the document
    return page_count

def populate_text_boxes(total_pages, results, template):
    # Initialize the page_text_boxes dictionary with empty dictionaries
    page_text_boxes = {page: {} for page in range(1, total_pages + 1)}
    
    # Use an iterator to assign results to boxes
    result_iterator = iter(results)
    
    # Loop through each page
    for page in range(1, total_pages + 1):
        # Assign a maximum of 3 or 4 boxes per page depending on the template
        for box_num in range(1, template + 1):
            try:
                # Assign the next result to the current box
                text = next(result_iterator)
                page_text_boxes[page][f"box{box_num}"] = text
            except StopIteration:
                # If results are exhausted, return the dictionary
                return page_text_boxes
    print(page_text_boxes)
    return page_text_boxes

def generate_all_images(pdf_path, output_dir):
    """
    Converts all pages of the PDF into images and saves them in the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert all pages of the PDF into images
    images = convert_from_path(pdf_path, dpi=200)
    for i, image in enumerate(images, start=1):
        output_path = os.path.join(output_dir, f"pdf_page_{i}.jpg")
        image.save(output_path, "JPEG")
        print(f"Saved: {output_path}")