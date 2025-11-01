import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenFilter;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.core.StopFilter;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
// import org.apache.lucene.analysis.standard.StandardFilter;
import org.apache.lucene.analysis.standard.StandardTokenizer;
import org.apache.lucene.analysis.core.LowerCaseFilter;
import org.apache.lucene.analysis.en.PorterStemFilter;
import org.apache.lucene.analysis.en.KStemFilter;
import org.apache.lucene.analysis.CharArraySet;

import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;

import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;


public class IndexTrecCollection {

    private static final Pattern DOC_PATTERN  = Pattern.compile("<DOC>(.*?)</DOC>", Pattern.DOTALL);
    private static final Pattern DOCNO_PATTERN= Pattern.compile("<DOCNO>(.*?)</DOCNO>");
    private static final Pattern TEXT_PATTERN = Pattern.compile("<TEXT>(.*?)</TEXT>", Pattern.DOTALL);

    public static void main(String[] args) throws Exception {
        if (args.length < 5) {
            System.out.println("Usage: java IndexTrecCollection <input_folder> <index_folder> <useStoplist:true|false> <stemmer:none|porter|krovetz> <stopwords_file_if_any>");
            return;
        }

        String inputDir = args[0];
        String indexDir = args[1];
        boolean useStoplist = Boolean.parseBoolean(args[2]);
        String stemmerOption = args[3].toLowerCase();
        String stopwordsFile = args[4];

        CharArraySet stopSet = null;
        if (useStoplist) {
            List<String> lines = Files.readAllLines(Paths.get(stopwordsFile));
            stopSet = new CharArraySet(lines, true);
        }

        Analyzer analyzer = createAnalyzer(useStoplist, stopSet, stemmerOption);
        Directory dir = FSDirectory.open(Paths.get(indexDir));
        IndexWriterConfig config = new IndexWriterConfig(analyzer);
        IndexWriter writer = new IndexWriter(dir, config);

        // === Start Time ===
        long startTime = System.currentTimeMillis();

        int totalDocs = indexDocuments(writer, inputDir);

        writer.commit();
        writer.close();

        // === start time ===
        long endTime = System.currentTimeMillis();
        double durationSec = (endTime - startTime) / 1000.0;

        // === print ===
        System.out.println("\n=============================");
        System.out.println("Indexing finished successfully");
        System.out.println("Input folder: " + inputDir);
        System.out.println("Index folder: " + indexDir);
        System.out.println("Stoplist: " + useStoplist + ", Stemmer: " + stemmerOption);
        System.out.println("Total documents indexed: " + totalDocs);
        System.out.printf(" Total time: %.2f seconds%n", durationSec);
        System.out.println("=============================\n");
        System.out.println("You can now run the search application to query the indexed documents.");
    }

    private static Analyzer createAnalyzer(final boolean useStoplist, final CharArraySet stopSet, final String stemmerOption) {
        return new Analyzer() {
            @Override
            protected TokenStreamComponents createComponents(String fieldName) {
                final var source = new StandardTokenizer();
                TokenStream result = source;
                result = new LowerCaseFilter(result);

                if (useStoplist && stopSet != null) {
                    result = new StopFilter(result, stopSet);
                }

                if ("porter".equals(stemmerOption)) {
                    result = new PorterStemFilter(result);
                } else if ("krovetz".equals(stemmerOption) || "kstem".equals(stemmerOption)) {
                    result = new KStemFilter(result);
                }
                return new TokenStreamComponents(source, result);
            }
        };
    }

    private static int indexDocuments(IndexWriter writer, String inputDir) throws IOException {
        final int[] count = {0};

        Files.walk(Paths.get(inputDir))
             .filter(Files::isRegularFile)
             .forEach(path -> {
                try {
                    String content = Files.readString(path);
                    Matcher docMatcher = DOC_PATTERN.matcher(content);
                    while (docMatcher.find()) {
                        String docText = docMatcher.group(1);
                        String docno = extractTag(DOCNO_PATTERN, docText).trim();
                        String text = extractTag(TEXT_PATTERN, docText).trim();

                        if (!docno.isEmpty() && !text.isEmpty()) {
                            Document doc = new Document();
                            doc.add(new StringField("docid", docno, Field.Store.YES));
                            doc.add(new TextField("text", text, Field.Store.YES));
                            writer.addDocument(doc);
                            count[0]++;
                        }
                    }
                    System.out.println("Indexed file: " + path.getFileName());
                } catch (Exception e) {
                    System.err.println("Error reading " + path + ": " + e.getMessage());
                }
             });

        return count[0];
    }

    private static String extractTag(Pattern pattern, String text) {
        Matcher m = pattern.matcher(text);
        if (m.find()) {
            return m.group(1);
        }
        return "";
    }
}
