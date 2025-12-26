import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
import yaml

_store = None
_client = None
_embeddings = None

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file) or {}

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from embedding.embedding_client import FastAPIEmbeddings
        _embeddings = FastAPIEmbeddings(
            base_url=config['EMBEDDING_SERVER_BASE_URL']
        )
    return _embeddings

def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path="./atom_db",
            settings=Settings(
                anonymized_telemetry=False
            )
        )
    return _client

def get_chroma_store():
    global _store
    if _store is None:
        _store = Chroma(
            client=get_client(),
            collection_name="atom",
            embedding_function=get_embeddings(),
        )
    return _store
