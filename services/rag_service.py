import logging
import json
from supabase import Client
from services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, supabase: Client, embedding: EmbeddingService):
        self.supabase = supabase
        self.embedding = embedding

    def search_brand_context(self, query: str, brand_dna_id: str):
        # Find relevant brand rules using vector similarity search in Supabase.
        logger.info(f"RAG search for brand_id: {brand_dna_id}")
        query_embedding = self.embedding.embed(query)
        result = self.supabase.rpc(
            "match_brand_dna",
            {
                "query_embedding": query_embedding,
                "match_count": 5,
                "filter_brand_id": brand_dna_id,
            },
        ).execute()
        clean_results = []
        if not result.data:
            logger.info("No RAG results found")
            return clean_results
        for doc in result.data:
            try:
                clean_results.append(json.loads(doc["content"]))
            except json.JSONDecodeError:
                clean_results.append(doc["content"])
        logger.info(f"RAG results: {len(clean_results)} items")
        return clean_results
