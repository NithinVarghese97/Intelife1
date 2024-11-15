import fitz

# Constants for header and footer
LOGO_SIZE = (50, 25)  # (width, height) in points
FONT_NAME = "helv"
HEADER_FONT_SIZE = 10

# Constants for body content
IMAGE_SIZE = (75, 75)  # (width, height) in points
BODY_FONT_SIZE = 14

# Margins
MARGIN_TOP = 25
MARGIN_BOTTOM = 25
MARGIN_SIDES = 40

# Spacing
DEFAULT_VERTICAL_MARGIN = 30
MIN_VERTICAL_MARGIN = 15

def measure_text_width(text):
    """
    Measure the width of the given text using the specified font and size.
    """
    # Create a dummy page to measure text width
    doc = fitz.open()
    page = doc.new_page()
    font = fitz.Font(FONT_NAME)
    text_width = font.text_length(text, BODY_FONT_SIZE)
    doc.close()
    return text_width

def add_header_footer(page, header_image, header_text, footer_image, footer_text):
    """
    Add header and footer to the page.

    Parameters:
    - page: The current PDF page.
    - header_image: Path to the header image.
    - header_text: Text for the header.
    - footer_image: Path to the footer image.
    - footer_text: Text for the footer.
    """
    # Adding header image
    header_image_rect = fitz.Rect(
        MARGIN_SIDES,
        MARGIN_TOP - LOGO_SIZE[1],
        MARGIN_SIDES + LOGO_SIZE[0],
        MARGIN_TOP
    )
    try:
        page.insert_image(header_image_rect, filename=header_image)
    except Exception as e:
        print(f"Error inserting header image: {e}")

    # Adding header text
    page.insert_text(
        (MARGIN_SIDES + LOGO_SIZE[0] + 10, MARGIN_TOP - 8),
        header_text,
        fontname=FONT_NAME,
        fontsize=HEADER_FONT_SIZE
    )

    # Draw line below header
    page.draw_line(
        p1=(MARGIN_SIDES, MARGIN_TOP),
        p2=(page.rect.width - MARGIN_SIDES, MARGIN_TOP)
    )

    # Adding footer image
    page_height = page.rect.height
    footer_image_rect = fitz.Rect(
        page.rect.width - MARGIN_SIDES - LOGO_SIZE[0],
        page_height - MARGIN_BOTTOM - LOGO_SIZE[1],
        page.rect.width - MARGIN_SIDES,
        page_height - MARGIN_BOTTOM
    )
    try:
        page.insert_image(footer_image_rect, filename=footer_image)
    except Exception as e:
        print(f"Error inserting footer image: {e}")

    # Adding footer text
    footer_text_x = footer_image_rect.x0 - 10 - measure_text_width(footer_text)
    footer_text_y = page_height - MARGIN_BOTTOM - (LOGO_SIZE[1] / 2) - (HEADER_FONT_SIZE / 2)
    page.insert_text(
        (footer_text_x, footer_text_y),
        footer_text,
        fontname=FONT_NAME,
        fontsize=HEADER_FONT_SIZE
    )

    # Draw line above footer
    page.draw_line(
        p1=(MARGIN_SIDES, page_height - MARGIN_BOTTOM),
        p2=(page.rect.width - MARGIN_SIDES, page_height - MARGIN_BOTTOM)
    )

def calculate_group_height(page, group_image_path, group_text, max_text_width):
    """
    Calculate the height of a group based on the image and the text.

    Parameters:
    - page: The current PDF page.
    - group_image_path: Path to the group's image.
    - group_text: The text content of the group.
    - max_text_width: Maximum width available for the text.

    Returns:
    - Total height required for the group.
    """
    # Load the image to get its dimensions
    try:
        img = fitz.Pixmap(group_image_path)
        image_height = img.height
        image_width = img.width
    except Exception as e:
        print(f"Error loading image {group_image_path}: {e}")
        image_height = IMAGE_SIZE[1]
        image_width = IMAGE_SIZE[0]
    finally:
        img = None  # Free memory

    # Calculate text height
    # Approximate number of lines based on text length and max_text_width
    if group_text.startswith("Standard 2"):
        print("Debugging Text Wrapping for Standard 2:")
        print(f"Group Text: {group_text}")
        print(f"Max Text Width: {max_text_width}")
    
    words = group_text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        test_width = measure_text_width(test_line)
        if test_width <= max_text_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Print wrapped lines for debugging
    if group_text.startswith("Standard 2"):
        print("Wrapped Lines:")
        print("\n".join(lines))
    
    line_count = len(lines)
    line_height = BODY_FONT_SIZE * 1.2  # 1.2 factor for line spacing
    text_height = line_count * line_height

    # Total group height is the maximum of image height and text height
    group_height = max(image_height, text_height)

    return group_height

def insert_resized_image(page, image_path, rect, max_size):
    """
    Insert an image into the page, resizing it to fit within max_size if necessary.

    Parameters:
    - page: The current PDF page.
    - image_path: Path to the image.
    - rect: The rectangle area where the image should be placed.
    - max_size: Tuple (max_width, max_height).

    Returns:
    - None
    """
    try:
        img = fitz.Pixmap(image_path)
        # Calculate scaling factor
        width_ratio = max_size[0] / img.width
        height_ratio = max_size[1] / img.height
        scale = min(width_ratio, height_ratio, 1)  # Prevent upscaling

        scaled_width = img.width * scale
        scaled_height = img.height * scale

        # Center the image within the rect
        x0 = rect.x0 + (rect.width - scaled_width) / 2
        y0 = rect.y0 + (rect.height - scaled_height) / 2
        scaled_rect = fitz.Rect(x0, y0, x0 + scaled_width, y0 + scaled_height)

        page.insert_image(scaled_rect, pixmap=img, keep_proportion=True)
    except Exception as e:
        print(f"Error inserting resized image {image_path}: {e}")

def add_groups(page, groups, y_start, max_height, max_text_width):
    """
    Add groups to the page with dynamic spacing.

    Parameters:
    - page: The current PDF page.
    - groups: List of tuples containing (image_path, text).
    - y_start: Starting y-coordinate for adding groups.
    - max_height: Maximum height available on the page.
    - max_text_width: Maximum width available for the text.

    Returns:
    - y_position after adding the groups.
    """
    current_y = y_start
    total_groups = len(groups)

    # First, calculate total height required for all groups
    group_heights = []
    for group in groups:
        group_height = calculate_group_height(page, group[0], group[1], max_text_width)
        group_heights.append(group_height)

    total_content_height = sum(group_heights)
    available_spacing = max_height - total_content_height

    if total_groups > 1:
        spacing = available_spacing / (total_groups - 1)
    else:
        spacing = available_spacing / 2  # Center if only one group

    spacing = max(spacing, MIN_VERTICAL_MARGIN)  # Ensure minimum spacing

    for idx, (group_image, group_text) in enumerate(groups):
        group_height = group_heights[idx]

        # Insert image
        image_rect = fitz.Rect(
            MARGIN_SIDES,
            current_y,
            MARGIN_SIDES + IMAGE_SIZE[0],
            current_y + IMAGE_SIZE[1]
        )
        insert_resized_image(page, group_image, image_rect, IMAGE_SIZE)

        if group_text.startswith("Standard 2"):
            print("Debugging Text Box for Standard 2:")
            print(f"Text Box Dimensions: {fitz.Rect(text_x, text_y, page.rect.width - MARGIN_SIDES - 10, text_y + group_height)}")
            print(f"Group Height: {group_height}, Current Y: {current_y}")

        # Insert text next to image
        text_x = MARGIN_SIDES + IMAGE_SIZE[0] + 10  # 10 units padding
        text_y = current_y
        page.insert_textbox(
            fitz.Rect(
                text_x,
                text_y,
                page.rect.width - MARGIN_SIDES - 10,
                text_y + group_height
            ),
            group_text,
            fontname=FONT_NAME,
            fontsize=BODY_FONT_SIZE,
            align=fitz.TEXT_ALIGN_LEFT,
            color=(0, 0, 0),
            overlay=True
        )

        # Update y_position for next group
        current_y += group_height + spacing

    return current_y

def generate_pdf(
    output_path,
    header_image,
    header_text,
    footer_image,
    footer_text,
    all_groups,
    groups_per_page=4,
    page_size="A4",
    image_width=100,
    text_width=400
):
    """
    Generate a PDF with dynamic spacing for groups.

    Parameters:
    - output_path: Path to save the generated PDF.
    - header_image: Path to the header image.
    - header_text: Text for the header.
    - footer_image: Path to the footer image.
    - footer_text: Text for the footer.
    - all_groups: List of tuples containing (image_path, text).
    - groups_per_page: Number of groups per page.
    - page_size: Size of the page (default "A4").
    - image_width: Width of the group images.
    - text_width: Maximum width available for the text.
    """
    doc = fitz.open()
    page = None

    # Define paper sizes in points
    PAPER_SIZES = {
        "A4": (595, 842),
        "Letter": (612, 792),
        # Add more sizes if needed
    }

    if page_size not in PAPER_SIZES:
        raise ValueError(f"Unsupported page size: {page_size}")

    PAGE_WIDTH, PAGE_HEIGHT = PAPER_SIZES[page_size]

    # Calculate usable page height
    usable_height = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - LOGO_SIZE[1] * 2  # Header and footer

    current_index = 0
    total_groups = len(all_groups)

    while current_index < total_groups:
        # Create a new page with specified size
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

        # Add header and footer
        add_header_footer(page, header_image, header_text, footer_image, footer_text)

        # Determine remaining groups
        remaining_groups = all_groups[current_index:]

        # Find the maximum number of groups that can fit on the current page
        for n in range(len(remaining_groups), 0, -1):
            groups_to_add = remaining_groups[:n]
            group_heights = [
                calculate_group_height(page, g[0], g[1], text_width) for g in groups_to_add
            ]
            
            
            total_content_height = sum(group_heights)
            total_spacing = usable_height - total_content_height

            if n > 1:
                spacing = total_spacing / (n - 1)
            else:
                spacing = total_spacing / 2  # Center if only one group

            if spacing >= MIN_VERTICAL_MARGIN:
                # Enough space to fit n groups
                add_groups(
                    page,
                    groups_to_add,
                    MARGIN_TOP + LOGO_SIZE[1],
                    usable_height,
                    text_width,
                )
                current_index += n
                break
        else:
            # If no group fits with the minimum margin, force add at least one
            groups_to_add = [remaining_groups[0]]
            add_groups(
                page,
                groups_to_add,
                MARGIN_TOP + LOGO_SIZE[1],
                usable_height,
                text_width,
            )
            current_index += 1

    # Save the document
    try:
        doc.save(output_path)
        print(f"PDF generated successfully at {output_path}")
    except Exception as e:
        print(f"Error saving PDF: {e}")
    finally:
        doc.close()

# Test Code
if __name__ == "__main__":
    output_path = "output.pdf"

    # Define header and footer information
    header_image = "test_images/logo.png"  # Replace with actual image path
    header_text = "Header: Sample PDF Document"
    footer_image = "test_images/logo.png"  # Replace with actual image path
    footer_text = "Footer: Page Information"

    # Define the groups with images and text for each "Standard"
    all_groups = [
        (
            "test_images/Standard1.png",
            "Standard 1: Intelife promotes your legal and human rights. Your rights are upheld and protected. Your Rights and Intelife's Responsibilities. Your Rights and Intelife's Responsibilities. Your Rights and Intelife's Responsibilities. Your Rights and Intelife's Responsibilities. Your Rights and Intelife's Responsibilities. Your Rights and Intelife's Responsibilities."
        ),
        (
            "test_images/Standard2.png",
            "Standard 2\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities\nAdditional Information."
        ),
        (
            "test_images/Standard3.png",
            "Standard 3\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities."
        ),
        (
            "test_images/Standard4.png",
            "Standard 4\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities."
        ),
        (
            "test_images/Standard5.png",
            "Standard 5\nIntelife promotes your legal and human rights\nYour rights are upheld and protected\nYour Rights and Intelife's Responsibilities."
        ),
    ]

    # Specify the number of groups per page
    groups_per_page = 4  # Try 4 per page to see the dynamic adjustment

    # Generate the PDF with the sample data
    generate_pdf(
        output_path,
        header_image,
        header_text,
        footer_image,
        footer_text,
        all_groups,
        groups_per_page,
        page_size="A4"
    )
