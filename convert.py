import re
''' 
Ce script convertit un fichier de topics au format TREC (<top>...</top>)
en un fichier TSV simple id<TAB> requête adapté pour Pyserini.
'''

input_path = "data/topics.1-50.txt"
output_path = "data/topics.1-50.tsv"


with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Trouver chaque bloc <top>...</top>
topics = re.findall(r"<top>(.*?)</top>", content, re.DOTALL)

with open(output_path, 'w', encoding='utf-8') as out:
    for topic in topics:
        # extraie id
        num_match = re.search(r"<num>\s*Number:\s*(\d+)", topic)
        # extraire titlte
        title_match = re.search(r"<title>\s*(.+)", topic)

        if num_match and title_match:
            qid = num_match.group(1).strip()
            query = title_match.group(1).strip()
            out.write(f"{qid}\t{query}\n")

print(f"Converted to TSV format: {output_path}")
