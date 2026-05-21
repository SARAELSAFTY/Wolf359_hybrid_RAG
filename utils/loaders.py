import json
import numpy as np
import faiss
import networkx as nx
from networkx.readwrite import json_graph
import os

from config import EMBEDDINGS_PATH, FAISS_INDEX_PATH, METADATA_PATH, GRAPH_PATH

def load_embeddings():
    if not os.path.exists(EMBEDDINGS_PATH):
        raise FileNotFoundError(f"Embeddings not found at {EMBEDDINGS_PATH}")
    return np.load(EMBEDDINGS_PATH)

def load_faiss_index():
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")
    return faiss.read_index(str(FAISS_INDEX_PATH))

def load_metadata():
    if not os.path.exists(METADATA_PATH):
        raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}")
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_graph():
    if not os.path.exists(GRAPH_PATH):
        return None
    with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return json_graph.node_link_graph(data)

def save_graph(graph):
    data = json_graph.node_link_data(graph)
    with open(GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


