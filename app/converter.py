
from context_clustering import group_similar_paragraphs_lda_dynamic, group_similar_paragraphs_dbscan
from context_generation import extract_text_from_pdf, write_string_to_file
from translation import Wrapper
from pdf_generation import replace_pdf_text
import threading
  
def convert(pdf_path):
    txt_path = 'app/text/output.txt'
    text, locations = extract_text_from_pdf(pdf_path, ignore_small_font=False)
    write_string_to_file(" ".join(text), txt_path)

    grouped_para = group_similar_paragraphs_dbscan(list(text), eps=0.2, min_samples=3, use_transformer=True) # Need experimenting
    print("GROUP NUM: ", len(grouped_para))
    
    results = []
    for group in grouped_para:
        results.append(Wrapper(" ".join(group), "", 'ft:gpt-3.5-turbo-0125:intelife-group::A3EN89gL'))
    
    print("RESULTS SIZE: ", len(results))
    
    return results