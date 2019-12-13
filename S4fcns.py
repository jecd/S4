import numpy as np
import pandas as pd 
import psycopg2 
import random
import matplotlib as mpl
import matplotlib.pyplot as plt

PGHOST="datafest201912.library.ucdavis.edu"
PGDATABASE="postgres"
PGPORT="49152"
PGUSER="anon"
PGPASSWORD="anon"
conn_string = ("host={} port={} dbname={} user={} password={}") \
        .format(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
conn=psycopg2.connect(conn_string)

sql_command = "SELECT page_ark FROM {} group by page_ark;".format("rtesseract_words")
pageIDs = pd.read_sql(sql_command, conn)

def colorDoc(document = 'd7pp4q-027', colorLabels = [], my_dpi = 220.53, colorBy = 'confidence'):
    df = getDoc(document)
    # Format dataframe from sql output
    df['text'] = df['text'].str.lower()
    def roundup(x):
        return x if x % 100 == 0 else x + 100 - x % 100
    im_height = roundup(max(df.bottom))
    im_width = roundup(max(df.right))
    df.top = im_height-df.top
    df.bottom = im_height-df.bottom
    # Deterimine coloring scheme
    # If appropriate sized color labels are supplied, then use those. Otherwise go with default (i.e. confidence).
    if len(colorLabels) > 0:
        if len(df) == len(colorLabels):
            colorBy = 'userDefined'
        else: 
            pass
    else:
        pass
    if colorBy == 'userDefined':
        k = len(np.unique(np.array(colorLabels)));
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(topics)))
        colorLabels = [random.randint(0,max(topics)) for i in range(len(df))]
    elif colorBy == 'random':
        topics = list(range(10))
        k = len(topics)
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(topics)))
        colorLabels = [random.randint(0,max(topics)) for i in range(len(df))]
    elif colorBy == 'confidence':
        confidences = list(range(101))
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(confidences)))
        colorLabels = df['confidence'].astype(int)
    elif colorBy == 'text_confidence':
        confidences = list(range(101))
        df['confidence'][df['confidence']<60] = 0
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(confidences)))
        colorLabels = df['confidence'].astype(int)
        colorLabels = df['confidence'].astype(int)
    # Plot:
    fig, ax = plt.subplots(figsize=(im_width/my_dpi, im_height/my_dpi), dpi=my_dpi)
    for idx,word,c in zip(range(len(df)),df.text,colorLabels):
        start = (df.left[idx],df.bottom[idx])
        height = df.top[idx]-df.bottom[idx]
        width = df.right[idx]-df.left[idx]
        ax.add_patch(mpl.patches.Rectangle(start, width = width, height = height, color = cmap[c,:], label = colorBy + '=' + str(c) ))
        ax.annotate(word,start, color='k', weight='bold', 
                    fontsize=height/4, ha='left', va='bottom')
        ax.set_xlim((0,im_width))
        ax.set_ylim((0,im_height))
    plt.title(str(docIdx) + ' : ' + documentName,fontdict = {'fontsize':22})
    plt.show()
    return df

def getDoc(document): 
    # Parse args
    if type(document) == int:
        documentName = pageIDs.page_ark[document]
        docIdx = document
    else:
        documentName = document
        docIdx = pageIDs[pageIDs['page_ark']==documentName].index[0]
    sql_command = "SELECT * FROM {} WHERE page_ark = '{}';".format("rtesseract_words",documentName)
    df = pd.read_sql(sql_command, conn)
    return df