from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm import LLMService
from services.embedding import EmbeddingService
from core.langfuse_client import langfuse
from app.config import settings
from supabase import create_client
from services.rag_service import RAGService
from prompts.prompts import build_brand_dna_prompt, build_generation_prompt
from services.governance_service import GovernanceService
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
llm = LLMService()
embedding_service = EmbeddingService()
gov_service = GovernanceService(supabase)
rag_service = RAGService(supabase, embedding_service)


class BrandDNARequest(BaseModel):
    name: str
    tone: str
    audience: str
    description: str
    user_id: str


class QueryRequest(BaseModel):
    query: str
    brand_id: str


class GenerateRequest(BaseModel):
    prompt: str
    brand_id: str
    user_id: str = None


@router.post("/brand-dna")
def create_brand_dna(data: BrandDNARequest):
    # Generate a Brand DNA manual with OpenAI and store it with vector embeddings.
    try:
        trace = langfuse.trace(
            name="brand_dna_generation",
            user_id=data.user_id,
        )

        prompt = build_brand_dna_prompt(
            name=data.name,
            tone=data.tone,
            audience=data.audience,
            description=data.description,
        )
        generation = trace.generation(
            name="llm_call",
            model="gpt-4o-mini",
            input=prompt,
        )
        manual = llm.generate(prompt)
        generation.end(output=manual)

        clean_manual = manual.replace("```json", "").replace("```", "").strip()
        try:
            manual_json = json.loads(clean_manual)
        except Exception:
            raise HTTPException(status_code=400, detail="Manual no es JSON válido")

        response = (
            supabase.table("brand_dna")
            .insert(
                {
                    "user_id": data.user_id,
                    "name": data.name,
                    "tone": data.tone,
                    "audience": data.audience,
                    "description": data.description,
                    "manual": manual_json,
                }
            )
            .execute()
        )
        brand_id = response.data[0]["id"]

        chunks = [
            json.dumps(manual_json.get("brand_overview", {})),
            json.dumps(manual_json.get("tone_of_voice", {})),
            json.dumps(manual_json.get("target_audience", {})),
            json.dumps(manual_json.get("messaging_rules", {})),
            json.dumps(manual_json.get("do_and_dont", {})),
            json.dumps(manual_json.get("example_content", {})),
        ]

        embedding_span = trace.span(
            name="embedding_generation",
            input={"chunks_count": len(chunks)},
        )
        for chunk in chunks:
            embedding = embedding_service.embed(chunk)
            supabase.table("brand_dna_embeddings").insert(
                {"brand_dna_id": brand_id, "content": chunk, "embedding": embedding}
            ).execute()
        embedding_span.end(output={"embeddings_stored": len(chunks)})

        logger.info(f"Brand DNA created: {brand_id} for user {data.user_id}")
        return {"success": True, "id": brand_id, "manual": manual_json}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating brand DNA: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/brand-dna/search")
def search_brand_context(data: QueryRequest):
    # Perform semantic search over Brand DNA embeddings to find relevant brand rules.
    try:
        trace = langfuse.trace(
            name="rag_search",
            user_id="anonymous",
            session_id=data.brand_id,
        )
        context = rag_service.search_brand_context(
            query=data.query, brand_dna_id=data.brand_id
        )
        trace.span(
            name="search_result",
            input={"query": data.query, "brand_id": data.brand_id},
            output={"chunks_found": len(context)},
        )
        return {"success": True, "context": context}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rag/generate")
def generate_content(data: GenerateRequest):
    # Generate marketing content governed by Brand DNA rules and create a pending content item.
    try:
        trace = langfuse.trace(
            name="content_generation",
            user_id=data.user_id or "anonymous",
            session_id=data.brand_id,
        )

        context_chunks = rag_service.search_brand_context(
            query=data.prompt, brand_dna_id=data.brand_id
        )
        context = "\n\n".join(
            [json.dumps(c, ensure_ascii=False) for c in context_chunks]
        )

        trace.span(
            name="rag_context_retrieval",
            input={"prompt": data.prompt, "brand_id": data.brand_id},
            output={"chunks_retrieved": len(context_chunks)},
        )

        final_prompt = build_generation_prompt(user_prompt=data.prompt, context=context)
        generation = trace.generation(
            name="rag_llm_call",
            model="gpt-4o-mini",
            input=final_prompt,
        )
        response_text = llm.generate(final_prompt)
        generation.end(output=response_text)

        content_res = gov_service.create_content({
            "brand_dna_id": data.brand_id,
            "prompt": data.prompt,
            "generated_content": response_text,
            "user_id": data.user_id,
            "status": "pending",
        })
        
        content_id = content_res.data[0]["id"]

        return {
            "success": True,
            "response": response_text,
            "content_id": content_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/brands")
def list_brands(user_id: str = None, limit: int = 50):
    # List all Brand DNA manuals, optionally filtered by user.
    try:
        query = supabase.table("brand_dna").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        query = query.order("created_at", desc=True).limit(limit)
        res = query.execute()
        brands = []
        for brand in res.data:
            manual = brand.get("manual", "{}")
            if isinstance(manual, str):
                try:
                    manual = json.loads(manual)
                except:
                    manual = {}
            brands.append({
                "id": brand["id"],
                "name": brand["name"],
                "tone": brand["tone"],
                "audience": brand["audience"],
                "description": brand["description"],
                "created_at": brand["created_at"],
                "manual": manual
            })
        return brands
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
