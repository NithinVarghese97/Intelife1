import numpy as np
from bertopic import BERTopic
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

# Resources:
# Topic modelling in general: https://medium.com/@m.nath/topic-modeling-algorithms-b7f97cec6005
# BERTopic author's words: https://towardsdatascience.com/topic-modeling-with-bert-779f7db187e6
# Documentation: https://maartengr.github.io/BERTopic/index.html

def cluster_sentences(sentences):
    topics, _, topic_model = create_BERTopic_model(sentences)
    
    groups = {p: [] for p in topics}
    for sentence in sentences:
        prediction = topic_model.transform(sentence)
        groups[prediction[0][0]] = groups[prediction[0][0]] + [sentence]
    
    # Remove outliers (topic = -1 is "outliers" topic, see BERTopic documentation)
    groups = {k: v for k, v in groups.items() if k != -1}
    groups = list(groups.values())

    return groups

def create_BERTopic_model(sentences, min_topic_size=5, n_neighbors=5):
    # Sentence embeddings using SentenceTransformer
    sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = sentence_model.encode(sentences, show_progress_bar=False)
    embeddings = normalize(embeddings)

    vectorizer_model = CountVectorizer(stop_words="english", min_df=2, ngram_range=(1, 2))
    
    # UMAP model
    umap_model = UMAP(
        n_neighbors=n_neighbors,
        n_components=5,
        min_dist=0.0,
        metric='cosine',
        random_state=42
    )
    
    # Initialize BERTopic model
    topic_model = BERTopic(
        embedding_model=sentence_model,
        vectorizer_model=vectorizer_model,
        umap_model=umap_model,
        min_topic_size=min_topic_size,
        nr_topics=20,
        top_n_words=10
    )

    # Train BERTopic model
    topics, probs = topic_model.fit_transform(sentences, embeddings)

    print(topic_model.get_topic_info())

    # Interpretation of topics (top 5 words)
    interpretation = []
    for topic in set(topics):
        words = topic_model.get_topic(topic)
        if words:
            interpretation.append("/".join([word[0] for word in words[:5]]))
    
    return topics, interpretation, topic_model