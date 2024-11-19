from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def add_bordered_content(document, image_path, text, font_size=14):
    """
    Add a centered rectangle with an image on the left and text on the right
    
    Args:
        document: Document object
        image_path: Path to the image file
        text: Text to display on the right
        font_size: Size of the text in points
    """
    # Add a table with one row and two cells
    table = document.add_table(rows=1, cols=2)
    table.columns[0].width = Inches(1.5)
    table.columns[1].width = Inches(4.5)

    # Center the table
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add border to the table
    border_xml = parse_xml(f'''
        <w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:top w:val="single" w:sz="10" w:space="0" w:color="000000"/>
            <w:left w:val="single" w:sz="10" w:space="0" w:color="000000"/>
            <w:bottom w:val="single" w:sz="10" w:space="0" w:color="000000"/>
            <w:right w:val="single" w:sz="10" w:space="0" w:color="000000"/>
        </w:tblBorders>
    ''')
    table._element.tblPr.append(border_xml)

    # Add image to left cell
    left_cell = table.cell(0, 0)
    left_cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = left_cell.paragraphs[0]
    run = paragraph.add_run()
    run.add_picture(image_path, width=Inches(2))
    
    # Add text to right cell
    right_cell = table.cell(0, 1)
    right_cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = right_cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.font.size = Pt(font_size)
    
    # Add spacing after the table
    document.add_paragraph()

def create_document(output_path, content_list):
    """
    Create a document with multiple bordered rectangles containing images and text
    
    Args:
        output_path: Path where the document will be saved
        content_list: List of dictionaries containing:
            - image_path: Path to image file
            - text: Text to display
            - font_size: (optional) Font size in points
    """
    doc = Document()
    # Add header
    header = doc.sections[0].header
    header_paragraph = header.paragraphs[0]
    header_paragraph.text = "This is the header text"
    header_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Add footer
    footer = doc.sections[0].footer
    footer_paragraph = footer.paragraphs[0]
    footer_paragraph.text = "This is the footer text"
    footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add each content block
    for content in content_list:
        add_bordered_content(
            doc,
            content['image_path'],
            content['text']
        )
    
    # Save the document
    doc.save(output_path)

content_list = [
    {
        'image_path': 'test_images/Standard1.png',
        'text': 'First item description',
        'font_size': 18
    },
    {
        'image_path': 'test_images/Standard2.png',
        'text': 'Second item description that is extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely extremely long',
        'font_size': 18
    },
    {
        'image_path': 'test_images/Standard3.png',
        'text': 'Third item description',
        'font_size': 18
    }
]

create_document('output.docx', content_list)