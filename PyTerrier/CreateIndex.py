import pyterrier as pt
import os
import pandas as pd

def create_index(collection_path):
    # Initialize PyTerrier
    if not pt.java.started():
        pt.java.init()

    # Define index method
    stopwords_path = "./datasets/stop_words.txt"
    index_config = {
        "nostop_nostem": {"stopwords": None, "stemmer": None},
        "nostop_porter": {"stopwords": None, "stemmer": "porter"},
        "stop_porter": {"stopwords": stopwords_path, "stemmer": "porter"}
    }

    # Get AP files
    files = []
    for file_name in os.listdir(collection_path):
        if file_name.startswith('AP'):
            file_path = os.path.join(collection_path, file_name)
            if os.path.isfile(file_path):
                files.append(file_path)
    
    print(f"Found {len(files)} AP files")

    # Create indexes based on configurations
    for config_name, settings in index_config.items():
        print(f"Creating: {config_name} index...")

        # Create index directory with absolute path
        index_dir = os.path.abspath("./var/indices")
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        index_path = os.path.join(index_dir, f"index_{config_name}")

        # Initialize indexer
        indexer = pt.TRECCollectionIndexer(
            index_path,
            stopwords = settings["stopwords"],
            stemmer = settings["stemmer"],
            verbose=True
        )

        indexer.setProperty("trec.encoding", "UTF-8")

        indexref = indexer.index(files)
        index = pt.IndexFactory.of(indexref)
        print(f"{config_name} index statistics:")
        print(index.getCollectionStatistics().toString())
        print("-" * 50)


def run_searches(query_file):
    # Initialize PyTerrier
    if not pt.java.started():
        pt.java.init()

    pt.ApplicationSetup.setProperty("trec.encoding", "UTF-8")

    # Load query file
    if not os.path.exists(query_file):
        raise FileNotFoundError(f"Query file not found: {query_file}")
    queries = pt.io.read_topics(query_file, "trec")
    queries["qid"] = (queries.index + 1).astype(str)

    # Load indexing methods
    index_path = os.path.abspath("./var/indices")
    index_nostop_nostem = pt.IndexFactory.of(os.path.join(index_path, "index_nostop_nostem"))
    index_nostop_porter = pt.IndexFactory.of(os.path.join(index_path, "index_nostop_porter"))
    index_stop_porter = pt.IndexFactory.of(os.path.join(index_path, "index_stop_porter"))

    # BM25 retrieval models
    bm25_nostop_nostem = pt.terrier.Retriever(index_nostop_nostem, wmodel="BM25")
    bm25_nostop_porter = pt.terrier.Retriever(index_nostop_porter, wmodel="BM25")
    bm25_stop_porter = pt.terrier.Retriever(index_stop_porter, wmodel="BM25")

    # TFIDF retrieval model
    tfidf_stop_porter = pt.terrier.Retriever(index_stop_porter, wmodel="TF_IDF")

    # Dirichlet retrieval model
    dirichlet_stop_porter_500 = pt.terrier.Retriever(index_stop_porter, wmodel="DirichletLM", controls={"mu":500})
    dirichlet_stop_porter_1500 = pt.terrier.Retriever(index_stop_porter, wmodel="DirichletLM", controls={"mu":1500})
    dirichlet_stop_porter_3000 = pt.terrier.Retriever(index_stop_porter, wmodel="DirichletLM", controls={"mu":3000})

    # Execute searches and save results
    result_dir = "./search_results"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    models = {
        "BM25_nostop_nostem": bm25_nostop_nostem,
        "BM25_nostop_porter": bm25_nostop_porter,  
        "BM25_stop_porter": bm25_stop_porter,
        "TFIDF_stop_porter": tfidf_stop_porter,
        "Dirichlet_stop_porter_500": dirichlet_stop_porter_500,
        "Dirichlet_stop_porter_1500": dirichlet_stop_porter_1500,
        "Dirichlet_stop_porter_3000": dirichlet_stop_porter_3000
    }

    for name, model in models.items():
        print(f"Running {name}...")
        results = model.transform(queries)
        output_path = os.path.join(result_dir, f"{name}_results.txt")
        pt.io.write_results(results, output_path, format='trec', run_name=name)
        print(f"Results saved to {output_path}")


def evaluate_results():
    # Initialize PyTerrier
    if not pt.java.started():
        pt.java.init()

    pt.ApplicationSetup.setProperty("trec.encoding", "UTF-8")

    # Load qrels
    qrels_file = "./datasets/qrels.1-50.AP8890"
    qrels = pd.read_csv(
        qrels_file, 
        sep=r"\s+", header=None,
        names=["qid", "Q0", "docno", "label"],
        dtype={"qid": str, "docno": str, "label": int}
    )[["qid", "docno", "label"]]

    # 统一类型与清洗空白
    qrels["qid"] = qrels["qid"].astype(str).str.strip()
    qrels["docno"] = qrels["docno"].astype(str).str.strip()
    assert isinstance(qrels, pd.DataFrame), f"type(qrels)={type(qrels)}"

    # 读取 topics，构建“标题->数字qid”映射
    topics = pt.io.read_topics("./datasets/topics.1-50.txt", "trec")
    topics["qid"] = topics["qid"].astype(str).str.strip()
    topics["query"] = topics["query"].astype(str).str.strip()
    title2qid = dict(zip(topics["query"], topics["qid"]))

    # Directory setup
    search_result_dir = "./search_results"
    eval_result_dir = "./eval_results"
    if not os.path.exists(eval_result_dir):
        os.makedirs(eval_result_dir)

    # Evaluation
    metrics = ["map", "Rprec", "P_10", "P_20", "P_100", "recall_1000", "bpref", "recip_rank"]

    for file in os.listdir(search_result_dir):
        if file.endswith("_results.txt"):
            model_name = file.replace("_results.txt", "")
            result_path = os.path.join(search_result_dir, file)

            run = pt.io.read_results(result_path)
            assert {"qid","docno"}.issubset(run.columns), f"{result_path} 缺少必要列"
            run["qid"] = run["qid"].astype(str).str.strip()
            run["docno"] = run["docno"].astype(str).str.strip()

            # 若 qid 不是纯数字，则用“标题->qid”映射修正
            non_numeric = ~run["qid"].str.fullmatch(r"\d+")
            if non_numeric.any():
                run.loc[non_numeric, "qid"] = run.loc[non_numeric, "qid"].map(title2qid)
                # 丢弃仍无 qid 的行
                before = len(run)
                run = run.dropna(subset=["qid"])
                if len(run) < before:
                    print(f"[{model_name}] 丢弃未能映射到 qid 的 {before-len(run)} 条结果")
                run["qid"] = run["qid"].astype(str)

            # 去除重复 (qid, docno)
            run = run.drop_duplicates(subset=["qid","docno"], keep="first")

            # 快速交叉检查
            common_qids = set(run["qid"].unique()) & set(qrels["qid"].unique())
            common_docs = set(run["docno"].unique()) & set(qrels["docno"].unique())
            print(f"[{model_name}] 共有主题数: {len(common_qids)}, 共有文档数: {len(common_docs)}")

            if len(common_qids) == 0 or len(common_docs) == 0:
                print(f"[{model_name}] 无法与 qrels 对齐，指标可能全为 0。请检查 topics 与 qrels 是否匹配。")

            eval_results = pt.Evaluate(res=run, qrels=qrels, metrics=metrics)

            output_file = os.path.join(eval_result_dir, f"{model_name}_eval.txt")
            with open(output_file, "w") as f:
                f.write(f"Evaluation Results for {model_name}\n")
                f.write("=" * 50 + "\n\n")
                for metric, value in eval_results.items():
                    f.write(f"{metric:<15}: {value:.4f}\n")
            
            print(f"Evaluation results for {model_name} saved to {output_file}")
            
    print("\nEvaluation completed!")


if __name__ == "__main__":
    collection_path = "./datasets/AP"
    query_file = "./datasets/topics.1-50.txt"
    # create_index(collection_path)
    run_searches(query_file)
    # evaluate_results()