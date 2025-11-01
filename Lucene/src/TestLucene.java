
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.store.ByteBuffersDirectory;

public class TestLucene {
    public static void main(String[] args) throws Exception {
        // 1️⃣ 创建内存索引目录
        ByteBuffersDirectory dir = new ByteBuffersDirectory();
        StandardAnalyzer analyzer = new StandardAnalyzer();
        IndexWriterConfig config = new IndexWriterConfig(analyzer);
        IndexWriter writer = new IndexWriter(dir, config);

        // 2️⃣ 添加文档
        Document doc1 = new Document();
        doc1.add(new TextField("content", "Lucene is a powerful search library", Field.Store.YES));
        writer.addDocument(doc1);

        Document doc2 = new Document();
        doc2.add(new TextField("content", "Lucene supports full-text indexing", Field.Store.YES));
        writer.addDocument(doc2);

        writer.close();
        System.out.println("Documents indexed successfully!");

        // 3️⃣ 打开索引并搜索
        DirectoryReader reader = DirectoryReader.open(dir);
        IndexSearcher searcher = new IndexSearcher(reader);

        // 搜索“Lucene”这个词
        QueryParser parser = new QueryParser("content", analyzer);
        Query query = parser.parse("Lucene");

        TopDocs results = searcher.search(query, 10);
        System.out.println("Found " + results.totalHits + " result(s):");

        for (ScoreDoc sd : results.scoreDocs) {
            Document d = searcher.doc(sd.doc);
            System.out.println(" - " + d.get("content"));
        }

        reader.close();
        dir.close();
        System.out.println("Search completed.");
    }
}
