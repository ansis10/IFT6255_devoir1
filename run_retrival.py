import subprocess
import os


# modele option：'tfidf', 'bm25','dirichlet'
modelOption = "bm25" \
""     

# index path
stemOption = "porter"     # porter, krovetz, none
stopwordOption = "nostop"   # stop / nostop
index_dir = f"indexes/index_{stemOption}_{stopwordOption}"


topics_path = "data/topics.1-50.tsv"
output_dir = "runs"
os.makedirs(output_dir, exist_ok=True)
output_path = f"{output_dir}/run_{modelOption}_{stemOption}_{stopwordOption}.txt"

# construire les agrs
args = [
    "python", "-m", "pyserini.search.lucene",
    "--index", index_dir,
    "--topics", topics_path,
    "--output", output_path,
    "--hits", "1000"
]


if modelOption == "tfidf":
    args += ["--impact"]

elif modelOption == "bm25":
    args += ["--bm25", "--k1", "0.9", "--b", "0.4"]

elif modelOption == "dirichlet":
    args += ["--qld"]

else:
    raise ValueError("modelOption 必须是 'tfidf', 'bm25', 或 'dirichlet'")


print(f"Running retrieval model: {modelOption}")
print(" ".join(args))
subprocess.run(args, check=True)
print(f"Retrieval finished! Results saved to {output_path}")
