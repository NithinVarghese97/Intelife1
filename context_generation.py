import pymupdf4llm
import re
import nltk

nltk.download('punkt')

# Resources:
# https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
# https://ayselaydin.medium.com/1-text-preprocessing-techniques-for-nlp-37544483c007

def extract(pdf_path):
    text = pymupdf4llm.to_markdown(pdf_path)
    return text

def preprocess(text):
    sentences = nltk.sent_tokenize(text)
    cleaned_sentences = [clean(sent) for sent in sentences]
    filtered_sentences = [sent for sent in cleaned_sentences if sent.strip() != ""]

    # remove duplicates
    visited = set()
    unique_sentences = []
    for sent in filtered_sentences:
        if sent not in visited:
            unique_sentences.append(sent)
            visited.add(sent)
    
    return unique_sentences

def clean(text):
    text = text.lower()
    # remove hashtags, urls, html tags, and lines with only dashes
    text = re.sub(r'#+\s.*|https?://\S+|www\.\S+|<.*?>|^\s*-+\s*$', '', text, flags=re.MULTILINE)

    # remove non-alphabetic characters, except for newlines, commas, periods, exclamation/question marks, apostrophes (for contractions), and hyphens (for compound words)
    text = re.sub(r"[^\r\na-z0-9\s,.!?'-]", ' ', text)

    # remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()