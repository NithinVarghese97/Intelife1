from app import app
from flask import render_template, request, redirect
from app.forms import PDFUploadForm
from app.converter import convert
from generate_images import generate_images_from_prompts
from pdf_generation import compile_info_for_pdf
import os

@app.route('/', methods=['GET', 'POST'])
def upload():
    form = PDFUploadForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Get the uploaded PDF file
        pdf_file = request.files['pdf_file']

        # Ensure the /files directory exists
        files_dir = os.path.join(os.path.dirname(__file__), 'files')
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)

        # Save the uploaded PDF file to the /files directory
        pdf_file_path = os.path.join(files_dir, pdf_file.filename)
        pdf_file.save(pdf_file_path)

        # Process the PDF and get results
        global results
        results = convert(pdf_file_path)

        # Remove the uploaded PDF file after processing
        os.remove(pdf_file_path)
        
        # Generate images using the results as prompts
        global generated_images
        generated_images = generate_images_from_prompts(results)
        
        # Pass both results and generated image paths to the template
        return redirect('/index')

    return render_template('upload.html', form=form)

TOTAL_PAGES = None
page_text_boxes = None

@app.route('/index')
def index():
    global TOTAL_PAGES, page_text_boxes

    # Check if TOTAL_PAGES and page_text_boxes are already set
    if TOTAL_PAGES is None or page_text_boxes is None:
        TOTAL_PAGES, page_text_boxes = compile_info_for_pdf(results, generated_images)

    # Get the current page from the query parameters (default to 1)
    page = int(request.args.get('page', 1))
    if page < 1 or page > TOTAL_PAGES:
        page = 1

    # Render the requested page and its text boxes
    return render_template(
        'index.html',
        total_pages=TOTAL_PAGES,
        text_boxes=page_text_boxes.get(page, {}),
        current_page=page
    )

@app.route('/submit', methods=['POST'])
def submit():
    # Get the current page from the form (ensure it's valid)
    page = int(request.form.get('page', 1))
    if page < 1 or page > TOTAL_PAGES:
        page = 1

    # Ensure the page exists in the dictionary
    if page not in page_text_boxes:
        page_text_boxes[page] = {}

    # Update the text box content for the current page
    for key, value in request.form.items():
        if key.startswith('box'):  # Only update keys that start with 'box'
            page_text_boxes[page][key] = value

    # Debugging: Print the updated page content to the console
    print(f"Updated Text Boxes for Page {page}:", page_text_boxes[page])
    print("All Text Boxes:", page_text_boxes)

    # Redirect back to the same page
    return redirect(f"/index?page={page}")