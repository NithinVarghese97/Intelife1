from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.table import _Cell
from docx.oxml.ns import qn
from PIL import ImageFont

def set_column_widths(table, col_widths):
    """
    Set fixed widths for table columns.
    
    Args:
        table: The table object from `python-docx`.
        col_widths: A list of widths in inches for each column.
    """
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Inches(col_widths[idx])

def add_spacing(document, spacing=0):
    """
    Add vertical spacing using an empty paragraph with specific spacing.

    Args:
        document: Document object.
    """
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = Pt(spacing)

def make_cell_cant_split(cell : _Cell) -> None:
    """
    Makes a table cell not break across pages.

    Args:
        cell: Table Cell object.
    """
    trPr = cell._tc.get_or_add_tcPr()
    trPr.append(OxmlElement('w:cantSplit'))
    

def add_content(document, box_per_page, image_path, text, font_size=12, font_family = 'Calibri', line_spacing = 1.5):
    """
    Add a centered table with an image on the left cell and text on the right cell.
    
    Args:
        document: Document object
        image_path: Path to the image file
        text: Text to display on the right
        font_size: Size of the text in points (12 by default for Intelife Easy Read Documents)
        font_family: Font family of the text (Calibri by default for Intelife Easy Read Documents)
    """
    # Add a table with one row and two cells
    table = document.add_table(rows=1, cols=2)
    # Adjust image cell width according to number of boxes per page (template)
    match box_per_page:
        case 3:
            image_width = 2
        case 4:
            image_width = 1.5
    set_column_widths(table, [image_width, 6-image_width])

    # Center the table
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.allow_autofit = False
    paragraph_format = document.styles['Normal'].paragraph_format
    paragraph_format.line_spacing = 1.5
    paragraph_format.space_after = 0
    # Add image to left cell
    left_cell = table.cell(0, 0)
    left_cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = left_cell.paragraphs[0]
    run = paragraph.add_run()
    run.add_picture(image_path, width=Inches(image_width-0.16))
    
    # Add text to right cell
    right_cell = table.cell(0, 1)
    right_cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = right_cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.font.size = Pt(font_size)
    run.font.name = font_family
    
    make_cell_cant_split(left_cell)
    make_cell_cant_split(right_cell)

def measure_text_width(text, font_size, font_path = None):
    """
    Measures the width of specified text using Pillow.

    Args:
    text (str): Text content
    font_size (int): Font size in points.
    font_path (str): Path to the font file (optional).
    """
    font = ImageFont.truetype("test_fonts/calibri.ttf", font_size)
    # Measure the width of the entire text (in pixels)
    return font.getlength(text)

def estimate_row_height(text, image_size, font_size, column_width_in, line_spacing = 1.5, font_path=None):
    """
    Estimate the height of a row based on exact character widths using Pillow.
    
    Args:
        text (str): Text content in the row.
        font_size (int): Font size in points.
        column_width_in (float): Width of the column in inches.
        line_spacing (float): Line spacing of document (1.5 for Easy Read Documents)
        font_path (str): Path to the font file (optional).
    
    Returns:
        tuple: Estimated number of lines and estimated height of the row in inches.
    """
    # Convert column width to pixels
    column_width_pt = (column_width_in - 0.16) * 80 # 80 DPI (dots per inch), 0.08 inch is default side margin.

    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        test_width = measure_text_width(test_line,font_size, font_path)
        if test_width <= column_width_pt:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Calculate height of text based on font size and line spacing.
    num_lines = len(lines)
    height_pt = (num_lines*(font_size * (line_spacing))) * 1.24 # 1.24 is factor for line spacing

    # Convert the calculated height to inch
    height_inch = height_pt/72
    print(height_inch, num_lines)
    return max(height_inch, image_size)

def create_page(doc, content_list, boxes_per_page):
    i = 0
    match boxes_per_page:
        case 3:
            image_height = 2 - 0.16 # 0.16 cell side margin
            text_width = 4 # side margin is handled in estimate function
        case 4:
            image_height = 1.5 - 0.16 # 0.16 cell side margin
            text_width = 4.5 # side margin is handled in estimate function

    # Space for content
    space_height_inch = 11 - (2 * 1)
    
    total_table_heights = 0
    for content in content_list:
        tmp = estimate_row_height(content['text'], image_height, 12, text_width)
        if (total_table_heights + tmp > space_height_inch - 0.2 *(i+1)):
            break
        else:
            total_table_heights += tmp
            i += 1
    spacing_inch = (space_height_inch-total_table_heights) / (i+1)
    spacing_pt = spacing_inch * 72

    for content in content_list[0:i]:
        add_spacing(doc,spacing_pt)
        add_content(
            doc,
            boxes_per_page,
            content['image_path'],
            content['text']
        )
    return i

def create_document(output_path, content_list, boxes_per_page, header_text = "Header text", header_image = "test_images/logo.png", footer_text = "Footer Text", footer_image = "test_images/logo.png"):
    """
    Create a document with multiple bordered rectangles containing images and text, with specified header and footer.
    
    Args:
        output_path: Path where the document will be saved
        content_list: List of dictionaries containing:
            - image_path: Path to image file
            - text: Text to display
            - font_size: (optional) Font size in points
        boxes_per_page: Number of boxes per page desired
        header_text: Text of header
        header_image: Path of header image
        footer_text: Text of footer
        footer_image: Path of footer image
    """
    # Open an empty document to write to
    # Predefined template can also be used by importing docx file.
    doc = Document()
    #doc = Document('intelife-template.docx')

    
    # Add header (Use table for two cells, left for image, right for text.)
    doc.sections[0].header_distance = 0.2
    header = doc.sections[0].header
    header_table = header.add_table(rows=1, cols=2, width=Inches(6))

    # Adjust header column widths and alignments
    set_column_widths(header_table, [0.5,5.5])
    header_table.alignment = WD_ALIGN_PARAGRAPH.LEFT
    header_table.cell(0, 0).vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    header_table.cell(0, 1).vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # Add header image
    header_logo_cell = header_table.cell(0, 0)
    header_logo_paragraph = header_logo_cell.paragraphs[0]
    header_logo_run = header_logo_paragraph.add_run()
    header_logo_run.add_picture(header_image, width=Inches(0.5-0.16))

    # Add header text
    header_text_cell = header_table.cell(0, 1)
    header_text_paragraph = header_text_cell.paragraphs[0]
    header_text_paragraph.text = header_text

    # Add footer
    doc.sections[0].footer_distance = 0.2
    footer = doc.sections[0].footer
    footer_table = footer.add_table(rows=1, cols=2, width=Inches(6))
    set_column_widths(footer_table, [5.5,0.5])
    footer_table.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Adjust footer column widths and alignments
    footer_table.cell(0, 0).vertical_alignment = WD_ALIGN_VERTICAL.TOP
    footer_table.cell(0, 1).vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Add footer text 
    footer_text_cell = footer_table.cell(0,0)
    footer_text_paragraph = footer_text_cell.paragraphs[0]
    footer_text_paragraph.text = footer_text
    footer_text_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    # Add footer image
    footer_logo_cell = footer_table.cell(0,1)
    footer_logo_paragraph = footer_logo_cell.paragraphs[0]
    footer_logo_run = footer_logo_paragraph.add_run()
    footer_logo_run.add_picture(footer_image, width = Inches(0.5-0.16))
    
    i =  0
    while i < len(content_list):
        n = create_page(doc, content_list[i:i+boxes_per_page], boxes_per_page)
        # Advance the group index by the number of groups placed on this page
        i += n
        if (i < len(content_list)):
            doc.add_page_break()

    # Save the document
    doc.save(output_path)

content_list = [
    {
        'image_path': 'test_images/Standard1.png',
        'text': 'First item description'
    },
    {
        'image_path': 'test_images/Standard2.png',
        'text': 'Second item description. Second item description. Second item description. Second item description. Second item description.'
    },
    {
        'image_path': 'test_images/Standard3.png',
        'text': 'Third item descriptionSecond item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item descript. item descSecond item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item descript. item descripripripriprppppppppppppppppppppp ddddddddd'
    },
    {
        'image_path': 'test_images/Standard1.png',
        'text': 'Fourth item description'
    },
    {
        'image_path': 'test_images/Standard1.png',
        'text': 'Fifth item description'
    },
        {
        'image_path': 'test_images/Standard1.png',
        'text': 'Sixth item description'
    },
        {
        'image_path': 'test_images/Standard1.png',
        'text': 'Seventh item description'
    }
]

create_document('output1.docx', content_list, 4)