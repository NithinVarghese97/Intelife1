import context_generation 
import context_clustering
from translation import Wrapper
from pdf_generation import replace_pdf_text
import os

pdf_path = 'dir/ER_2_0.pdf'
txt_path = 'text/output.txt'
os.makedirs(os.path.dirname(txt_path), exist_ok=True)

text = context_generation.extract_text(pdf_path)
text = context_generation.preprocess_text(text)

with open(txt_path, 'w') as txt_file:
    for line in text:
        txt_file.write(line + '\n')

groups = context_clustering.cluster_sentences(text)
print("GROUPED PARA: ", groups)

results = []
for group in groups:
    results.append(Wrapper(" ".join(group), "", 'ft:gpt-3.5-turbo-0125:intelife-group::A3EN89gL'))

print("RESULT: ", results)