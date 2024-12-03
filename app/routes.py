from app import app
from flask import render_template, request, redirect, send_file, jsonify
from app.forms import PDFUploadForm
from app.converter import convert
from generate_images import generate_images_from_prompts
from pdf_generation import compile_info_for_pdf, update_text, caller
from word2pdf import convert_to_pdf
from werkzeug.utils import secure_filename

import os
import time
import threading

UPLOAD_PROGRESS = {"progress": 0}

def process_pdf(pdf_file_path):
    global UPLOAD_PROGRESS, results, generated_images

    # Simulate progress updates
    UPLOAD_PROGRESS['progress'] = 10
    time.sleep(2.5)  # Simulate processing time

    UPLOAD_PROGRESS['progress'] = 20
    time.sleep(1)  # Simulate processing time
    
    # Process the PDF and get results
    results = convert(pdf_file_path)

    UPLOAD_PROGRESS['progress'] = 40
    time.sleep(1)  # Simulate processing time
    
    total_images = len(results)
    
    def progress_callback(current_image, total_images):
        # Update the progress based on the current image
        progress_start = 40
        progress_end = 80
        progress_range = progress_end - progress_start
        progress_increment = progress_range / total_images
        UPLOAD_PROGRESS['progress'] = int(round(progress_start + (current_image * progress_increment)))

    # Generate images using the results as prompts
    generated_images = generate_images_from_prompts(results, progress_callback)

    UPLOAD_PROGRESS['progress'] = 80
    time.sleep(1)  # Simulate processing time

    # Remove the uploaded PDF file after processing
    os.remove(pdf_file_path)

    UPLOAD_PROGRESS['progress'] = 100

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['pdf_file']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file and file_extension in {'.pdf', '.docx'}:
        files_dir = os.path.join(os.path.dirname(__file__), 'static/files')
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)

        # Remove uploaded files stored on server side.
        temp_filenames = ["upload.pdf", "upload.docx"]
        for filename in temp_filenames:
            file_path = os.path.join(files_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        # Define a static file name and save the uploaded file to that path
        static_file_name = 'upload.pdf' if file_extension == '.pdf' else 'upload.docx'
        file_path = os.path.join(files_dir, static_file_name)
        file.save(file_path)

        # Convert DOCX to PDF if it's a DOCX file
        if file_extension == '.docx':
            # Convert the DOCX to PDF
            convert_to_pdf(file_path)

        # Return the static file path (relative or absolute as needed)
        pdf_url = "static/files/upload.pdf"
        return jsonify({'file_url': pdf_url}), 200

    return jsonify({'error': f"Unsupported file type: {file_extension}"}), 400


@app.route('/', methods=['GET', 'POST'])
def process():
    form = PDFUploadForm()

    if request.method == 'POST' and form.validate_on_submit():
        UPLOAD_PROGRESS['progress'] = 0  # Reset progress

        file_path = "app/static/files/upload.pdf"

        # Start the background thread for processing
        thread = threading.Thread(target=process_pdf, args=(file_path,))
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