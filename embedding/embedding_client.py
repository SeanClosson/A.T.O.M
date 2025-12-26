import openai
from typing import List

class FastAPIEmbeddings:
    def __init__(self, base_url: str, api_key: str = "not-needed"):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = "sentence-transformers/all-MiniLM-L6-v2"
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents - sends RAW strings to FastAPI"""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts  # Raw strings, no tokenization
        )
        return [item.embedding for item in response.data]
    
    def embed_query(self, text: str) -> List[float]:
        """Embed single query"""
        return self.embed_documents([text])[0]
