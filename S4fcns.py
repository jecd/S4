import numpy as np
import pandas as pd 
import psycopg2 
import random
import matplotlib as mpl
import matplotlib.pyplot as plt
import string

PGHOST="datafest201912.library.ucdavis.edu"
PGDATABASE="postgres"
PGPORT="49152"
PGUSER="anon"
PGPASSWORD="anon"
conn_string = ("host={} port={} dbname={} user={} password={}") \
        .format(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
conn=psycopg2.connect(conn_string)

# sql_command = "SELECT page_ark FROM {} group by page_ark;".format("rtesseract_words")
# pageIDs = pd.read_sql(sql_command, conn)

sql_command ='select p.page_ark, page_id from page p'
pageIDs = pd.read_sql(sql_command, conn)
pageIDs = pageIDs.sort_values('page_ark',ascending = True).reset_index()

def colorDoc(document = 'd7pp4q-027', colorIdxs = [], colorBy = 'confidence', model = [], targetWord = 'wine', my_dpi = 220.53):
    df, docIdx, documentName = getDoc(document)
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
    if len(colorIdxs) > 0:
        if len(df) == len(colorIdxs):
            colorBy = 'userDefined'
        else: 
            pass
    else:
        pass
    if colorBy == 'userDefined':
        # k = len(np.unique(np.array(colorIdxs)));
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, 101))
        cmap[0,:] = np.array([1,1,1,1])
        df['colorVals'] = colorIdxs
        # colorIdxs = [random.randint(0,max(topics)) for i in range(len(df))]
    elif colorBy == 'random':
        topics = list(range(10))
        k = len(topics)
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(topics)))
        colorIdxs = [random.randint(0,max(topics)) for i in range(len(df))]
    elif colorBy == 'confidence':
        confidences = list(range(101))
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(confidences)))
        colorIdxs = df['confidence'].astype(int)
    elif colorBy == 'text_confidence':
        confidences = list(range(101))
        confidenceThresh = 80;
        df.loc[df['confidence']<80, 'confidence'] = 0
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, len(confidences)))
        colorIdxs = df['confidence'].astype(int)
    elif colorBy == 'wordSimilarity':
        colorIdxs = colorScoreText(documentName, targetWord, model)
        cmap = plt.get_cmap('RdYlGn')(np.linspace(0.15, 0.85, 101))
        cmap[0,:] = np.array([1,1,1,1])
        df['colorVals'] = colorIdxs


    # Plot:
    fig, ax = plt.subplots(figsize=(im_width/my_dpi, im_height/my_dpi), dpi=my_dpi)
    for idx,word,c in zip(list(range(len(df.text))),df.text,colorIdxs):
        start = (df.left[idx],df.bottom[idx])
        height = df.top[idx]-df.bottom[idx]
        width = df.right[idx]-df.left[idx]
        ax.add_patch(mpl.patches.Rectangle(start, width = width, height = height, color = cmap[c,:], label = colorBy + '=' + str(c) ))
        ax.annotate(word,start, color='k', weight='bold', 
                    fontsize=height/4, ha='left', va='bottom')
        ax.set_xlim((0,im_width))
        ax.set_ylim((0,im_height))
    plt.title(str(docIdx) + ' : ' + documentName,fontdict = {'fontsize':22})
    plt.savefig(str(docIdx) + ' : ' + documentName + colorBy + '.png')
    plt.show()
    return

def getDoc(document = 'd7pp4q-027'): 
    # Parse args
    if type(document) == int:
        documentName == pageIDs.page_ark[document]
        docIdx = document
    else:
        documentName = document
        docIdx = pageIDs[pageIDs['page_ark']==documentName].index[0]
    sql_command = "SELECT * FROM {} WHERE page_ark = '{}';".format("rtesseract_words",documentName)
    df = pd.read_sql(sql_command, conn)
    df = df.sort_values('num')
    df = df.reset_index()
    return df, docIdx, documentName

def getDocLink(document):
    if type(document) == int:
        docIdx = document
    else:    
        docIdx = pageIDs[pageIDs['page_ark'] == document].index[0]
    link = 'https://digital.ucdavis.edu'  + pageIDs['page_id'][docIdx]
    return link

def preprocessText(document):
    df,_,_ = getDoc(document)
    texts = list(df.text)
    preprocessed_texts = []
    for t in texts:
        t = ''.join([c for c in t if c in string.ascii_letters or c in string.whitespace])
        t = t.lower()
        t = t.split()
        if len(t) > 0:
            preprocessed_texts.append(t[0])
        else:
            preprocessed_texts.append('')   
    return preprocessed_texts

def orderScores(preprocessed_texts, scores):
    ''' Input all the prepreocessed texts in the document 
    and the cosine similary scores lookup table (should have a range from 0 to 2)

    Output scores associated with each word in the document in order.
    '''
    orderedScores = []
    for idx, word in zip(range(len(preprocessed_texts)), preprocessed_texts):
        if preprocessed_texts[idx]== '':
            orderedScores.append(0)
        else:
            wordScore = scores[scores.columns[1]][scores['source_word'] == preprocessed_texts[idx]]
            if wordScore.empty:
                orderedScores.append(0)
            else:
                orderedScores.append(wordScore.values[0]) 
    return orderedScores

def getColorIdx(orderedScores):
    ''' Given cosine similary scores for each word 
    output the color index from 0 to 100'''
    colorIdxs = list(np.round(100*np.array(orderedScores)/2).astype(int))
    return colorIdxs

def getOrderedColorIdx(preprocessed_texts, scores): 
    orderedScores = orderScores(preprocessed_texts, scores)
    colorIdxs = getColorIdx(orderedScores)
    return colorIdxs 

def scoreText(documentName, targetWord, model):
    ''' Score document according to similarity to target word. 
    Rescale scores on an integer scale from 0 to 100 (for coloring document).
    '''
    from scipy import spatial
    preprocessed_texts = preprocessText(documentName)
    orderedScores= []
    for currWord in preprocessed_texts:
        try: 
            wordScore = spatial.distance.cosine(model.wv[currWord], model.wv[targetWord])
            orderedScores.append(wordScore)
        except KeyError: 
            orderedScores.append(0)    
    return orderedScores 

def colorScoreText(documentName, targetWord, model):
    ''' Score document according to similarity to target word. 
    Rescale scores on an integer scale from 0 to 100 (for coloring document).
    '''
    orderedScores = scoreText(documentName, targetWord, model)    
    colorIdxs = getColorIdx(orderedScores)
    return colorIdxs 
