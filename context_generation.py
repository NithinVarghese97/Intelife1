import pymupdf4llm
import pathlib
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Resources:
# https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
# https://ayselaydin.medium.com/1-text-preprocessing-techniques-for-nlp-37544483c007

def extract_text(pdf_path):
    text = pymupdf4llm.to_markdown(pdf_path)
    return text

def clean_text(text, language="english"):
    # 1. lowercase all text
    text = text.lower()

    # 2. remove headings
    text = re.sub(r'#+\s.*', '', text)

    # 3. remove urls
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 4. remove outline numbers, special characters, digits and extra whitespace
    text = re.sub(r"[^\r\na-z0-9\s,.!?]", "", text)
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r'^\s*\d+\.(\d+\.)*\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\b\d+%?\b', '', text)  # Remove percentages and standalone numbers
    text = re.sub(r'\b\d+\.\d+\b', '', text)  # Remove decimal numbers
    text = re.sub(r"[0-9]", "", text)

    # 5. remove new page lines
    text = re.sub(r'^\s*-+\s*$', '', text, flags=re.MULTILINE)
    
    # 6. remove html tags 
    text = re.sub(r'<.*?>', '', text) 

    return text

def preprocess_text(text, language="english"):
    paragraphs = text.split("\n\n")
    cleaned_paragraphs = [clean_text(paragraph, language) for paragraph in paragraphs]
    unique_paragraphs = list(set(cleaned_paragraphs))
    return unique_paragraphs