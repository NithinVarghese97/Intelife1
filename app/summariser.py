from context_generation import extract, preprocess
from context_clustering import cluster_sentences
from translation import translate
from pdf_generation import replace_pdf_text
import os

def summarise(pdf_path):
    extracted_text = extract(pdf_path)
    preprocessed_text = preprocess(extracted_text)
    grouped_paragraphs, coherence = cluster_sentences(preprocessed_text)
    ai_summary = [translate(" ".join(group)) for group in grouped_paragraphs]

    # Save preprocessed text to app/text/output.txt
    output_dir = 'app/text'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(os.path.join(output_dir, 'output.txt'), 'w') as f:
        for line in preprocessed_text:
            f.write(line + '\n')

    return ai_summary