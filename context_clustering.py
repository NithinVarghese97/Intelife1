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

def cluster_sentences(sentences):
    topics, topic_model = create_BERTopic_model(sentences)
    
    groups = {p: [] for p in topics}
    for sentence in sentences:
        prediction = topic_model.transform(sentence)
        groups[prediction[0][0]] = groups[prediction[0][0]] + [sentence]
    
    # Remove outliers (topic = -1 is "outliers" topic, see BERTopic documentation)
    groups = {k: v for k, v in groups.items() if k != -1}
    groups = list(groups.values())

    return groups

def create_BERTopic_model(sentences, min_topic_size=8):

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

    topics, probs = topic_model.fit_transform(sentences, embeddings)

    print(topic_model.get_topic_info())
    
    
    return topics, topic_model