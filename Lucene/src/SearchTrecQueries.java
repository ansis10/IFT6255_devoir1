import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.*;
import org.apache.lucene.search.similarities.*;
import org.apache.lucene.store.FSDirectory;

import java.io.*;
import java.nio.file.Paths;
import java.util.regex.*;

public class SearchTrecQueries {

    public static void main(String[] args) throws Exception {
        if (args.length < 4) {
            System.out.println("Usage: java SearchTrecQueries <index_folder> <topics_file> <model:tfidf|bm25> <output_run_file>");
            return;
        }

        String indexDir = args[0];
        String topicsFile = args[1];
        String modelType = args[2].toLowerCase();
        String outputFile = args[3];

        // === open index ===
        FSDirectory dir = FSDirectory.open(Paths.get(indexDir));
        DirectoryReader reader = DirectoryReader.open(dir);
        IndexSearcher searcher = new IndexSearcher(reader);

        // === choose modele (Similarity) ===
        if (modelType.equals("bm25")) {
            searcher.setSimilarity(new BM25Similarity());
        } else if (modelType.equals("tfidf")) {
            searcher.setSimilarity(new ClassicSimilarity()); // TF-IDF
        } else if (modelType.equals("dirichlet")) {
            // if dirichlet, we can set mu parameter from args[4], default 2000
            float mu = (args.length >= 5) ? Float.parseFloat(args[4]) : 2000f;
            searcher.setSimilarity(new LMDirichletSimilarity(mu));
        } else {
            throw new IllegalArgumentException("Unsupported model: " + modelType);
}


        // === ready Query Parser ===
        StandardAnalyzer analyzer = new StandardAnalyzer();
        QueryParser parser = new QueryParser("text", analyzer);

        // === lire TREC file (only take <num> and <title>) ===
        Pattern numPattern = Pattern.compile("<num>\\s*Number:\\s*(\\d+)");
        Pattern titlePattern = Pattern.compile("<title>\\s*(.*)");

        BufferedReader br = new BufferedReader(new FileReader(topicsFile));
        BufferedWriter bw = new BufferedWriter(new FileWriter(outputFile));

        String line, num = null, title = null;
        while ((line = br.readLine()) != null) {
            Matcher mNum = numPattern.matcher(line);
            Matcher mTitle = titlePattern.matcher(line);
            if (mNum.find()) {
                // num = mNum.group(1).trim();
                num = mNum.group(1).trim().replaceFirst("^0+", "");  // enlver les 00 devant
            } else if (mTitle.find()) {
                title = mTitle.group(1).trim();
                if (num != null && title != null) {
                    runQuery(num, title, searcher, parser, bw);
                    num = null;
                    title = null;
                }
            }
        }

        br.close();
        bw.close();
        reader.close();
        System.out.println("Retrieval completed. Results saved to: " + outputFile);
    }

    private static void runQuery(String qid, String queryString, IndexSearcher searcher, QueryParser parser, BufferedWriter bw) throws Exception {
        Query query = parser.parse(QueryParser.escape(queryString));
        TopDocs topDocs = searcher.search(query, 1000); // top 1000 documents
        int rank = 1;
        for (ScoreDoc sd : topDocs.scoreDocs) {
            Document doc = searcher.doc(sd.doc);
            String docno = doc.get("docid");
            float score = sd.score;
            // TREC input format：qid Q0 docno rank score runid
            bw.write(qid + " Q0 " + docno + " " + rank + " " + score + " lucene_run\n");
            rank++;
        }
    }
}

