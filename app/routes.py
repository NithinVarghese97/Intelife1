from app import app
from flask import render_template, request, redirect, send_file, jsonify
from app.forms import PDFUploadForm
from app.converter import convert
from generate_images import generate_images_from_prompts
from pdf_generation import compile_info_for_pdf, update_text, caller

import os
import time
import threading

UPLOAD_PROGRESS = {"progress": 0}

def process_pdf(pdf_file_path):
    global UPLOAD_PROGRESS, results, generated_images

    # Simulate progress updates
    UPLOAD_PROGRESS['progress'] = 10
    time.sleep(1)  # Simulate processing time

    # Process the PDF and get results
    results = convert(pdf_file_path)

    UPLOAD_PROGRESS['progress'] = 50
    time.sleep(1)  # Simulate processing time

    # Generate images using the results as prompts
    generated_images = generate_images_from_prompts(results)

    UPLOAD_PROGRESS['progress'] = 90
    time.sleep(1)  # Simulate processing time

    # Remove the uploaded PDF file after processing
    os.remove(pdf_file_path)

    UPLOAD_PROGRESS['progress'] = 100

@app.route('/', methods=['GET', 'POST'])
def upload():
    form = PDFUploadForm()

    if request.method == 'POST' and form.validate_on_submit():
        UPLOAD_PROGRESS['progress'] = 0  # Reset progress

        # Get the uploaded PDF file
        pdf_file = request.files['pdf_file']

        # Ensure the /files directory exists
        files_dir = os.path.join(os.path.dirname(__file__), 'files')
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)

        # Save the uploaded PDF file to the /files directory
        pdf_file_path = os.path.join(files_dir, pdf_file.filename)
        pdf_file.save(pdf_file_path)

        # Start the background thread for processing
        thread = threading.Thread(target=process_pdf, args=(pdf_file_path,))
        thread.start()

        return render_template('processing.html')  # Render a template that shows the progress bar

    return render_template('upload.html', form=form)

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(UPLOAD_PROGRESS)

@app.route('/choose-template', methods=['GET', 'POST'])
def choose_template():
    if request.method == 'POST':
        # Get the selected option from the form
        selected_option = request.form.get('option', '3')  # Default to 3 if no selection
        return redirect(f'/display?template={selected_option}')

    return render_template('templates.html')


TOTAL_PAGES = None
page_text_boxes = None
template = None

@app.route('/display')
def display():
    global TOTAL_PAGES, page_text_boxes, all_groups, mapping, template

    # Get the selected template variable from the query parameters
    temp = int(request.args.get('template', 999)) 
    if template is None or (temp != template and temp != 999):
        template = temp
    
    # Check if TOTAL_PAGES and page_text_boxes are already set
    if TOTAL_PAGES is None or page_text_boxes is None:
        TOTAL_PAGES, page_text_boxes, all_groups, mapping = compile_info_for_pdf(results, generated_images, template)
    else:
        TOTAL_PAGES, page_text_boxes = caller(all_groups, template)

    # Get the current page from the query parameters (default to 1)
    page = int(request.args.get('page', 1))
    if page < 1 or page > TOTAL_PAGES:
        page = 1

    # Render the requested page and its text boxes
    return render_template(
        'display.html',
        total_pages=TOTAL_PAGES,
        text_boxes=page_text_boxes.get(page, {}),
        current_page=page,
        selected_template=int(template)
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
            update_text(all_groups, page_text_boxes, mapping, page, key, value)

    # Debugging: Print the updated page content to the console
    print(f"Updated Text Boxes for Page {page}:", page_text_boxes[page])
    print("All Text Boxes:", page_text_boxes)

    # Redirect back to the same page
    return redirect(f"/display?page={page}")

@app.route('/download-pdf')
def download_pdf():
    pdf_path = "static/pdf/output.pdf"  # Update this to match your PDF file's location
    return send_file(pdf_path, as_attachment=True, download_name="output.pdf")
