from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from hdbscan import HDBSCAN
from umap import UMAP
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired
from nltk import word_tokenize          
from nltk.stem import WordNetLemmatizer 
import gensim.corpora as corpora
from gensim.models.coherencemodel import CoherenceModel
import tqdm

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
    
    coherence = calculate_coherence_score(sentences, groups, topic_model)
    print(f"Coherence score: {coherence}")

    # [[sent1, sent2], [sent3, sent4], ...]
    return list(groups.values())

def calculate_coherence_score(sentences, groups, topic_model):
    """
    Coherence score tells you how well the words in a topic are related to each other. 
    0 means no relation (e.g. random words), 1 means perfect relation (e.g. synonyms).
    https://www.reddit.com/r/LanguageTechnology/comments/ap36l1/what_is_a_good_coherence_score_for_an_lda_model/
    https://stackoverflow.com/questions/54762690/evaluation-of-topic-modeling-how-to-understand-a-coherence-value-c-v-of-0-4
    """

    # Get top words for each topic
    top_words = []
    for group in groups:
        topic = topic_model.get_topic(group)
        words = [word for word, prob in topic]
        top_words.append(words)
    
    # https://stackoverflow.com/questions/70548316/gensim-coherencemodel-gives-valueerror-unable-to-interpret-topic-as-either-a-l
    vectorizer = topic_model.vectorizer_model
    analyzer = vectorizer.build_analyzer()

    texts = [analyzer(doc) for doc in sentences]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    coherence_model = CoherenceModel(
        topics=top_words,
        corpus=corpus,
        texts=texts,
        dictionary=dictionary,
        coherence="c_v",
    )

    return coherence_model.get_coherence()

def run_topic_model_experiments(sentences):
    embedding_models = [
        'all-MiniLM-L6-v2',
    ]
    min_cluster_sizes = [3, 5, 8, 10, 15, 20, 25]
    min_sample_sizes = [3, 5, 8, 10, 15, 20, 25]
    ngram_ranges = [(1, 1), (1, 2), (1, 3), (1, 4)]

    config_list = [
        {
            'embedding_model': embedding_model,
            'min_cluster_size': min_cluster_size,
            'ngram_range': ngram_range,
        }
        for embedding_model in embedding_models
        for min_cluster_size in min_cluster_sizes
        for ngram_range in ngram_ranges
    ]

    results = []
    
    for config in tqdm.tqdm(config_list, desc="Running topic model experiments"):
        try:
            # Create SentenceTransformer with specified model
            sentence_model = SentenceTransformer(
                config.get('embedding_model', 'all-MiniLM-L6-v2')
            )
            
            # Normalize embeddings
            embeddings = normalize(sentence_model.encode(sentences))

            umap_model = UMAP(random_state=42)
            
            # Configure HDBSCAN
            hdbscan_model = HDBSCAN(
                min_cluster_size=config.get('min_cluster_size', 8),
                cluster_selection_method=config.get('cluster_selection_method', "leaf"),
                prediction_data=True,
            )
            
            # Configure Vectorizer
            vectorizer_model = CountVectorizer(
                stop_words="english",
                ngram_range=config.get('ngram_range', (1, 2)),
                tokenizer=LemmaTokenizer(),
            )
            
            # Choose representation model
            representation_model = KeyBERTInspired()
            
            # Create BERTopic model
            topic_model = BERTopic(
                embedding_model=sentence_model,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                vectorizer_model=vectorizer_model,
                representation_model=representation_model,
                nr_topics=20,
            )
            
            # Fit and transform
            topics, probs = topic_model.fit_transform(sentences, embeddings)
            
            # Group sentences by topic
            groups = {t: [] for t in range(max(topics)+1)}
            for i, sentence in enumerate(sentences):
                if topics[i] == -1: continue
                groups[topics[i]] = groups[topics[i]] + [sentence]
            
            # Calculate coherence
            coherence = calculate_coherence_score(sentences, groups, topic_model)
            
            # Prepare result
            result = {
                'config': config,
                'topic_sizes': [len(group) for group in groups.values()],
                'coherence_score': coherence,
            }
            results.append(result)

            print(result)
            
        except Exception as e:
            print(f"Experiment failed with config {config}: {e}")
    
    return results
