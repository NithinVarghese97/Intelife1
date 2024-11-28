from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired
from nltk import word_tokenize          
from nltk.stem import WordNetLemmatizer 

# https://github.com/MaartenGr/BERTopic/issues/286
class LemmaTokenizer:
    def __init__(self):
        self.wnl = WordNetLemmatizer()
    def __call__(self, doc):
        return [self.wnl.lemmatize(t) for t in word_tokenize(doc)]

# Resources:
# Topic modelling in general: https://medium.com/@m.nath/topic-modeling-algorithms-b7f97cec6005
# BERTopic author's words: https://towardsdatascience.com/topic-modeling-with-bert-779f7db187e6
# Documentation: https://maartengr.github.io/BERTopic/index.html
# We have also considered LDA and normal DBSCAN. See older commits for that. Feel free to replace the current model with those!

def cluster_sentences(sentences, min_topic_size=8):

    sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

    embeddings = normalize(sentence_model.encode(sentences))

    hdbscan_model = HDBSCAN(
        min_cluster_size=min_topic_size,
        cluster_selection_method="leaf", # https://hdbscan.readthedocs.io/en/latest/parameter_selection.html#leaf-clustering
        prediction_data=True,
    )

    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        tokenizer=LemmaTokenizer(),
    )

    representation_model = KeyBERTInspired()

    topic_model = BERTopic(
        embedding_model=sentence_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
        nr_topics=20, # Easy Read generally has 4-5 pages. With 4 topics per page, we can have max 20 topics.
    )

    """
    topics variable looks like this: [-1, 1, 2, 3, 2, 1, ...]. 
    Each number represents the topic number of the 
    corresponding sentence at the same index in the sentences list. 
    0 means the first topic, 1 means the second topic, and so on. 
    -1 means outlier.
    """

    topics, probs = topic_model.fit_transform(sentences, embeddings)

    print(topic_model.get_topic_info())

    # Group sentences by topic
    # e.g. {0: [sent1, sent2], 1: [sent3, sent4], ...}

    groups = {t: [] for t in range(max(topics)+1)}
    for i, sentence in enumerate(sentences):
        if topics[i] == -1: continue # Skip outliers
        groups[topics[i]] = groups[topics[i]] + [sentence]
    
    # [[sent1, sent2], [sent3, sent4], ...]
    return list(groups.values())