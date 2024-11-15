import fitz

'''
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
'''
# Image and font size for footer and header
LOGO_SIZE = (50,25) 
FONT_NAME = "helv"
HEADER_FONT_SIZE = 10

# Image and font size for Body(14 for Easy Read)
IMAGE_SIZE = (75,75)
BODY_FONT_SIZE = 14

# Margin for header/footer and margins of the sides of document
MARGIN_TOP = 25
MARGIN_BOTTOM = 25
MARGIN_SIDES = 40

# Default margin, temporary use for static spacing.
DEFAULT_VERTICAL_MARGIN = 30
MIN_VERTICAL_MARGIN = 15

def measure_text_width(text):
    font = fitz.Font(FONT_NAME)
    text_width = font.text_length(text, BODY_FONT_SIZE)
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
    footer_text_x = footer_image_rect.x0 - 10 - measure_text_width(footer_text)
    page.insert_text((footer_text_x, page_height - 10), 
                     footer_text, fontname=FONT_NAME, fontsize=HEADER_FONT_SIZE)
    page.draw_line(
        p1=(MARGIN_SIDES, page_height - MARGIN_BOTTOM),
        p2=(page.rect.width - MARGIN_SIDES, page_height - MARGIN_BOTTOM)
    )


# Function to calculate the height of each paragraph/group of text and image.
# This is the function requiring work.
def calculate_group_height(page, img, group_text, max_text_height):
    # Load image to get its height, opens with path for now, but can change to DALLE output later.
    img = fitz.open(img)
    image_height = img[0].rect.height
    image_width = img[0].rect.width
    max_text_width = page.rect.width - image_width - 2 * MARGIN_SIDES

    # Calculate the height of the text box
    # Create a test rectangle for the text to measure height dynamically
    text_rect = fitz.Rect(0, 0, max_text_width, max_text_height)  # Large height to allow for wrapping
    line_count = page.insert_textbox(
        text_rect, group_text, fontname=FONT_NAME, fontsize=BODY_FONT_SIZE, render_mode=3
    )
    
    line_height = BODY_FONT_SIZE * 1.2  # 1.2 factor for line spacing
    text_height = line_count * line_height

    # Height for this group
    group_height = max(image_height,text_height)
    return group_height


# Function to add groups with dynamic spacing
# CURRENTLY ONLY ADDS GROUPS WITH FIXED SPACING
def add_groups(page, groups, num_groups, max_height):
    group_height = (max_height - (num_groups + 1) * DEFAULT_VERTICAL_MARGIN) / num_groups
    vertical_margin = DEFAULT_VERTICAL_MARGIN if group_height >= MIN_VERTICAL_MARGIN else MIN_VERTICAL_MARGIN
    if group_height < MIN_VERTICAL_MARGIN:
        num_groups -= 1  # Reduce groups if spacing is too small

    y_position = MARGIN_TOP + LOGO_SIZE[1] + vertical_margin

    for i in range(num_groups):
        if i >= len(groups):
            break  # No more groups to add
        group_image, group_text = groups[i]

        # Insert group image and text
        page.insert_image(fitz.Rect(MARGIN_SIDES, y_position, MARGIN_SIDES + IMAGE_SIZE[0], y_position + + IMAGE_SIZE[1]), 
                          filename=group_image)  # Adjust width/height as needed
        page.insert_text((MARGIN_SIDES + 110, y_position), group_text, fontname=FONT_NAME, fontsize=BODY_FONT_SIZE)

        y_position += group_height + vertical_margin


# Generate PDF based on specified group count per page
# CURRENTLY NOT DYNAMIC
def generate_pdf(output_path, header_image, header_text, footer_image, footer_text, all_groups, groups_per_page, image_width=100, text_width=400):
    doc = fitz.open()
    i = 0
    
    while i < len(all_groups):
        # Determine number of groups that can fit based on specified `groups_per_page`
        num_groups = groups_per_page
        page = doc.new_page()

        # Add header and footer
        add_header_footer(page, header_image, header_text, footer_image, footer_text)

        # Check if specified `groups_per_page` can fit, adjust if needed
        max_height = page.rect.height - MARGIN_TOP - MARGIN_BOTTOM - 2*LOGO_SIZE[1]
        #group_height = (max_height - (num_groups + 1) * DEFAULT_VERTICAL_MARGIN) / num_groups
        
        # TODO: Add groups to the page with calculated spacing 
        # Currently just uses a fixed margin
        add_groups(page, all_groups[i:i + num_groups], groups_per_page, max_height)

        # Advance the group index by the number of groups placed on this page
        i += num_groups

    # Save the document
    doc.save(output_path)
    doc.close()



## ALL CODE BELOW IS JUST A TEST WITH EXAMPLE.
output_path = "output.pdf"

# Define header and footer information
header_image = "test_images/logo.png"  # Replace with actual image path
header_text = "Header: Sample PDF Document"
footer_image = "test_images/logo.png"  # Replace with actual image path
footer_text = "Footer: Page Information"

# Define the groups with images and text for each "Standard"
all_groups = [
    ("test_images/Standard1.png", "Standard 1: Intelife promotes your legal and human rights. Your rights are upheld and protected. Your Rights and Intelife's Responsibilities. "),
    ("test_images/Standard2.png", "Standard 2\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities\n\n\n\n\n\n\n\n\n\n\n\n test \n"),
    ("test_images/Standard3.png", "Standard 3\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities\n\n\n\n\n\n\n\n\n testttt"),
    ("test_images/Standard4.png", "Standard 4\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities"),
    ("test_images/Standard5.png", "Standard 5\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities"),
]

# Specify the number of groups per page
groups_per_page = 4  # Try 4 per page to see the dynamic adjustment

# Generate the PDF with the sample data
generate_pdf(output_path, header_image, header_text, footer_image, footer_text, all_groups, groups_per_page)



measure_text_width("Standard 1\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities\n\n\n\n\n\n\n\n 5")