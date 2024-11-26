from context_generation import extract, preprocess
from context_clustering import cluster_sentences
from translation import Wrapper
from pdf_generation import replace_pdf_text
import os

def summarise(pdf_path):
    extracted_text = extract(pdf_path)
    print("EXTRACTED TEXT: ", extracted_text)

    preprocessed_text = preprocess(extracted_text)
    print("PREPROCESSED TEXT: ", preprocessed_text)

    # Save preprocessed text to app/text/output.txt
    output_dir = 'app/text'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(os.path.join(output_dir, 'output.txt'), 'w') as f:
        for line in preprocessed_text:
            f.write(line + '\n')

    groups = cluster_sentences(preprocessed_text)
    print("GROUPED TEXT: ", groups)

    ai_summary = [Wrapper(" ".join(group), "", 'ft:gpt-3.5-turbo-0125:intelife-group::A3EN89gL') for group in groups]
    print("SUMMARIZED TEXT: ", ai_summary)

    return ai_summary

pdf_path = 'dir/ER_2_0.pdf'
summarised_text = summarise(pdf_path)