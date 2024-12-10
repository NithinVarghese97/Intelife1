from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired, Regexp
from flask_wtf.file import FileAllowed, FileRequired

class PDFUploadForm(FlaskForm):
    pdf_file = FileField('Upload File', validators=[
        FileRequired(message="Please select a file."),
        FileAllowed(['pdf', 'docx'], 'Only PDF or DOCX files are allowed.'),
    ])
    submit = SubmitField('Submit')
