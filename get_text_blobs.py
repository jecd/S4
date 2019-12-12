import nltk
from nltk.cluster import KMeansClusterer
import gensim
import string
import psycopg2
import pandas as pd

# 1. CONNECT TO THE DB ----------------------------------------------------------
PGHOST="datafest201912.library.ucdavis.edu"
PGDATABASE="postgres"
PGPORT="49152"
PGUSER="anon"
PGPASSWORD="anon"

conn_string = ("host={} port={} dbname={} user={} password={}") \
        .format(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)

conn=psycopg2.connect(conn_string)


# 2. GET THE DATA --------------------------------------------------------------
sql_command = "select page_ark, string_agg(text, '  ') from rtesseract_words group by page_ark;"
frame = pd.read_sql(sql_command, conn)
texts = list(frame['string_agg'])


# 3. PREPROCESS THE DATA ------------------------------------------------------
    # preprocess:
    # remove non alphabet or whitespace characters
    # to lowercase
    # normalize whitespace
preprocessed_texts = []
for t in texts:
    t = ''.join([c for c in t if c in string.ascii_letters or c in string.whitespace])
    t = t.lower()
    t = t.split()
    preprocessed_texts.append(t)


# 4. TRAIN THE MODEL ----------------------------------------------------------
model = gensim.models.Word2Vec(
            preprocessed_texts,
            size=200,
            window=15,
            min_count=5,
            workers=4)


# 5. CLUSTER THE MODEL --------------------------------------------------------
# not yet run
# K = 20 
# kclusterer = KMeansClusterer(K, distance=nltk.cluster.util.cosine_distance, repeats=25)
# assigned_clusters = kclusterer.cluster(model[model.vocab], assign_clusters=True)
