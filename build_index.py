import subprocess
import os

stemOption = "porter" # porter, krovetz, none
stopwordOption = "nostop" # stop/nostop

index_dir = f"indexes/index_{stemOption}_{stopwordOption}"
os.makedirs(index_dir, exist_ok=True)
stopword_path = "data/stop_words.txt"
args = [
    "python", "-m", "pyserini.index.lucene",
    "--collection", "TrecCollection",
    "--input", "data/AP",
    "--index", index_dir,
    "--generator", "DefaultLuceneDocumentGenerator",
    "--threads", "4",
    "--storePositions", "--storeDocvectors", "--storeRaw",
    "--stemmer", stemOption
]

if stopwordOption == "stop":
    args += ["--stopwords", stopword_path]

subprocess.run(args, check=True)
