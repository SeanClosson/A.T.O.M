import uuid
from chromadb import PersistentClient


class LongTermMemory:
    def __init__(self, path="memory_store"):
        client = PersistentClient(path)
        self.collection = client.get_or_create_collection("jarvis_memory")

    def add(self, text: str, metadata=None):
        print(f"💾 WRITING TO CHROMA: {text}")
        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def query(self, text: str, k=5):
        results = self.collection.query(
            query_texts=[text],
            n_results=k
        )
        docs = results.get("documents", [[]])
        return docs[0] if docs else []
