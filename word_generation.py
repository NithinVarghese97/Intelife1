from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.table import _Cell


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

def add_spacing(document):
    """
    Add vertical spacing using an empty paragraph with specific spacing.
    Currently using default spacing, can be adjusted.

    Args:
        document: Document object.
    """
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = Pt(0)

def make_cell_cant_split(cell : _Cell) -> None:
    """
    Makes a table cell not break across pages.

    Args:
        cell: Table Cell object.
    """
    trPr = cell._tc.get_or_add_tcPr()
    trPr.append(OxmlElement('w:cantSplit'))
    

def add_bordered_content(document, box_per_page, image_path, text, font_size=14):
    """
    Add a centered rectangle with an image on the left and text on the right.
    
    Args:
        document: Document object
        image_path: Path to the image file
        text: Text to display on the right
        font_size: Size of the text in points (14 by default for Easy Read Documents)
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
    


    # Add image to left cell
    left_cell = table.cell(0, 0)
    left_cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = left_cell.paragraphs[0]
    run = paragraph.add_run()
    run.add_picture(image_path, width=Inches(image_width))
    
    # Add text to right cell
    right_cell = table.cell(0, 1)
    right_cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = right_cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.font.size = Pt(font_size)
    run.font.name = 'Calibri'
    
    make_cell_cant_split(left_cell)
    make_cell_cant_split(right_cell)
    # Add spacing after the table
    document.add_paragraph()


def estimate_row_height(text, font_size, column_width_in):
    """
    Estimate the height of a row based on text length and font size.
    Currently not used as estimation is not accurate due to different width of characters.
    Example: 'M' is much wider than 'i'. Accurate width unobtainable unless we have font file/use PyMuPDF Font
    
    Args:
        text (str): Text content in the row.
        font_size (int): Font size in points.
        column_width_in (float): Width of the column in inches.
    
    Returns:
        float: Estimated row height in inches.
    """
    # Estimate number of lines based on column width (approx 10 characters per inch)
    chars_per_line = int(column_width_in * 10)
    lines = len(text) // chars_per_line + 1  # Number of lines needed for text

    # Convert font size (points) to height in inches
    line_height_in = (font_size + 15) / 72 # Points to inches, 1.15(15pt) is default line spacing in Word.

    # Return the height for this text based on number of lines.
    return lines * line_height_in


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
    doc = Document()
    # Predefined templates can be used by importing docx file.
    # doc = Document('intelife-template.docx')

    # Add header (Use table for two cells, left for image, right for text.)
    header = doc.sections[0].header
    header_table = header.add_table(rows=1, cols=2, width=Inches(6))
    set_column_widths(header_table, [0.5,5.5])
    header_table.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Adjust column widths for header
    header_table.cell(0, 0).vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    header_table.cell(0, 1).vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # Add image
    header_logo_cell = header_table.cell(0, 0)
    header_logo_paragraph = header_logo_cell.paragraphs[0]
    header_logo_run = header_logo_paragraph.add_run()
    header_logo_run.add_picture(header_image, width=Inches(0.5))

    # Add text
    header_text_cell = header_table.cell(0, 1)
    header_text_paragraph = header_text_cell.paragraphs[0]
    header_text_paragraph.text = header_text

    # Add footer
    footer = doc.sections[0].footer
    footer_table = footer.add_table(rows=1, cols=2, width=Inches(6))
    set_column_widths(footer_table, [5.5,0.5])
    footer_table.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Sets vertical alignment for footer text.
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
    footer_logo_run.add_picture(footer_image, width = Inches(0.5))
    

    # Potential calculation of margin instead of default.
    #content_height_inch = page_height_inch - (2 * margin_inch)
    #spacing_between_boxes_inch = content_height_inch / (2*(boxes_per_page + 1))

    # Add each content block
    for content in content_list:
        # Default spacing for now, could require work on calculation of margin.
        add_spacing(doc)
        add_bordered_content(
            doc,
            boxes_per_page,
            content['image_path'],
            content['text']
        )
    
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
        'text': 'Third item descriptionSecond item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item description. Second item descript. item desc'
    },
    {
        'image_path': 'test_images/Standard3.png',
        'text': 'Fourth item description'
    },
    {
        'image_path': 'test_images/Standard3.png',
        'text': 'Fifth item description'
    }
]

create_document('output.docx', content_list, 4)