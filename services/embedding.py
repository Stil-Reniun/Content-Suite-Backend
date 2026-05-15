import logging
from langchain_openai import OpenAIEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)
logger.info("Initializing Embedding model")

embedding_model = OpenAIEmbeddings(
    api_key=settings.OPENAI_API_KEY,
    model="text-embedding-3-small"
)

class EmbeddingService:
    def __init__(self):
        self.model = embedding_model

    def embed(self, text: str):
        # Convert text into a vector embedding for semantic similarity search.
        return self.model.embed_query(text)
