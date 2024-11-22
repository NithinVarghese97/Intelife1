from app import app
from flask import render_template, request, jsonify
from app.forms import PDFUploadForm
from app.converter import convert
from generate_images import generate_images_from_prompts  # Import your function
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
        results = convert(pdf_file_path)

        # Remove the uploaded PDF file after processing
        os.remove(pdf_file_path)
        
        # Generate images using the results as prompts
        generated_images = generate_images_from_prompts(results)
        
        # Compile and generate the PDF
        compile_info_for_pdf(results, generated_images)
        
        # Pass both results and generated image paths to the template
        return render_template('results.html', results=results, images=generated_images)

    return render_template('upload.html', form=form)
