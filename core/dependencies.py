from core.supabase_client import supabase
from services.embedding import EmbeddingService
from services.rag_service import RAGService
from services.governance_service import GovernanceService
embedding_service = EmbeddingService()
def get_rag_service() -> RAGService:
    return RAGService(supabase, embedding_service)
def get_governance_service() -> GovernanceService:
    return GovernanceService(supabase)