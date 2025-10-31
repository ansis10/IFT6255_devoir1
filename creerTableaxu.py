import os
import re
import csv
from collections import defaultdict

def extract_metrics(filepath):
    metrics = {}
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3 and parts[1] == 'all':
                metric_name = parts[0]
                try:
                    value = float(parts[2])
                    metrics[metric_name] = value
                except ValueError:
                    continue
    return metrics

def get_model_info(filename):
    match = re.match(r'eval_run_(\w+)_(\w+)_(\w+)\.txt', filename)
    if match:
        model, stemmer, stop = match.groups()
        return f"{model.upper()}_{stemmer}_{stop}"
    return filename

# chemin du fichier eval
eval_dir = "eval"

# metrics
main_metrics = [
    "map",
    "gm_map",
    "P_5", 
    "P_10",
    "P_100",
    "P_1000",
    "Rprec",
    "bpref",
    "recip_rank",
    "num_rel_ret",
]

# collect tous metric
results = {}
for filename in os.listdir(eval_dir):
    if filename.startswith("eval_run_") and filename.endswith(".txt"):
        filepath = os.path.join(eval_dir, filename)
        model_name = get_model_info(filename)
        results[model_name] = extract_metrics(filepath)

# generer csv
output_file = "eval_comparison.csv"
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    
    # haeder
    header = ["Model"] + main_metrics
    writer.writerow(header)
    
    # ecrire diff modele resultas
    for model_name, metrics in sorted(results.items()):
        row = [model_name]
        for metric in main_metrics:
            value = metrics.get(metric, 0.0)
            row.append(value)
        writer.writerow(row)

print(f"save to{output_file}")