from app import app
from flask import render_template, request, jsonify
from app.forms import PDFUploadForm
import os

@app.route('/', methods=['GET', 'POST'])
def upload():
    form = PDFUploadForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Get the uploaded PDF file
        pdf_file = request.files['pdf_file']

        print("PDF FILE: ", pdf_file)
        # Ensure the /files directory exists
        files_dir = os.path.join(os.path.dirname(__file__), 'files')
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)

        # Save the uploaded PDF file to the /files directory
        pdf_file_path = os.path.join(files_dir, pdf_file.filename)
        pdf_file.save(pdf_file_path)

        return jsonify({'success': True})

    return render_template('upload.html', form=form)