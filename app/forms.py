from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired, Regexp
from flask_wtf.file import FileAllowed, FileRequired

class PDFUploadForm(FlaskForm):
    pdf_file = FileField('Upload PDF', validators=[
        FileRequired(message="Please select a file."),
        FileAllowed(['pdf'], 'Only PDF files are allowed.'),
    ])
    api_key = StringField('API Key', validators=[
        DataRequired(message="Please enter an API key."),
    ])
    submit = SubmitField('Submit')
