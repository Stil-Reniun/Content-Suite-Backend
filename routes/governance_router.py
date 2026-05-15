import logging
import json
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.governance_service import GovernanceService
from services.multimodal_audit import MultimodalAuditService
from services.rag_service import RAGService
from core.supabase_client import supabase
from core.langfuse_client import langfuse
from services.embedding import EmbeddingService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
embedding_service = EmbeddingService()
gov_service = GovernanceService(supabase)
audit_service = MultimodalAuditService()
rag_service = RAGService(supabase, embedding_service)


class ApproveRequest(BaseModel):
    content_id: str
    approved: bool
    feedback: str = None
    user_id: str


class ContentCreateRequest(BaseModel):
    brand_dna_id: str
    prompt: str
    user_id: str


@router.post("/content/create")
def create_content(data: ContentCreateRequest):
    # Create a new content item with pending status for the approval workflow.
    try:
        trace = langfuse.trace(
            name="content_create",
            user_id=data.user_id,
            session_id=data.brand_dna_id,
        )
        trace.span(
            name="create_content_input",
            input={"brand_dna_id": data.brand_dna_id, "prompt": data.prompt},
        )
        res = gov_service.create_content({
            "brand_dna_id": data.brand_dna_id,
            "prompt": data.prompt,
            "user_id": data.user_id,
            "status": "pending",
        })
        trace.span(
            name="create_content_output",
            output={"content_id": res.data[0]["id"], "status": "pending"},
        )
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/content/pending")
def list_pending_content(brand_dna_id: str = None):
    # List all content items awaiting approval, optionally filtered by brand.
    try:
        query = gov_service.supabase.table("content_items").select("*").eq("status", "pending")
        if brand_dna_id:
            query = query.eq("brand_dna_id", brand_dna_id)
        query = query.order("created_at", desc=True)
        res = query.execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/content/approved")
def list_approved_content(brand_dna_id: str = None):
    # List all approved content items, optionally filtered by brand.
    try:
        query = gov_service.supabase.table("content_items").select("*").eq("status", "approved")
        if brand_dna_id:
            query = query.eq("brand_dna_id", brand_dna_id)
        query = query.order("created_at", desc=True)
        res = query.execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/content/{content_id}")
def get_content(content_id: str):
    # Fetch a single content item by ID.
    try:
        res = gov_service.get_content(content_id)
        if not res.data:
            raise HTTPException(status_code=404, detail="Content not found")
        return {"success": True, "data": res.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/content")
def list_content(brand_dna_id: str = None, status: str = None, limit: int = 50):
    # List content items with optional filters for brand, status, and limit.
    try:
        query = gov_service.supabase.table("content_items").select("*")
        if brand_dna_id:
            query = query.eq("brand_dna_id", brand_dna_id)
        if status:
            query = query.eq("status", status)
        query = query.order("created_at", desc=True).limit(limit)
        res = query.execute()
        return {"success": True, "data": res.data, "count": len(res.data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/content/finalize-approval")
def finalize_approval(content_id: str, user_id: str):
    # Finalize content approval after visual audit passes. Only APPROVER_B can execute.
    try:
        trace = langfuse.trace(
            name="finalize_approval",
            user_id=user_id,
            session_id=content_id,
        )

        start_time = time.time()
        user = gov_service.supabase.table("profile_users")\
            .select("role")\
            .eq("id", user_id)\
            .single()\
            .execute()
        role = user.data["role"]
        if role != "APPROVER_B":
            raise Exception("Only APPROVER_B can finalize approval")

        content = gov_service.get_content(content_id).data
        if not content:
            raise Exception("Content not found")
        if content.get("audit_status") != "passed":
            raise Exception("Content must pass audit before approval")
        if content["status"] != "pending":
            raise Exception("Content already processed")

        trace.span(
            name="validation",
            input={"role": role, "audit_status": content.get("audit_status")},
            output={"valid": True},
        )

        gov_service.update_status(content_id, "approved", "Aprobado tras auditoría visual exitosa")

        elapsed = time.time() - start_time
        trace.span(
            name="approval_result",
            output={"status": "approved", "elapsed_seconds": elapsed},
        )

        return {
            "success": True,
            "status": "approved",
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/content/approve")
def approve_content(data: ApproveRequest):
    # Approve or reject content based on APPROVER_A decision.
    try:
        trace = langfuse.trace(
            name="content_approval",
            user_id=data.user_id,
            session_id=data.content_id,
        )

        start_time = time.time()
        user = gov_service.supabase.table("profile_users")\
            .select("role")\
            .eq("id", data.user_id)\
            .single()\
            .execute()
        role = user.data["role"]
        if role != "APPROVER_A":
            raise Exception("Only APPROVER_A can approve/reject content")

        content = gov_service.get_content(data.content_id).data
        if not content:
            raise Exception("Content not found")
        if content["status"] != "pending":
            raise Exception("Content already processed")

        trace.span(
            name="validation",
            input={"role": role, "content_status": content["status"]},
            output={"valid": True},
        )

        status = "approved" if data.approved else "rejected"
        gov_service.update_status(data.content_id, status, data.feedback)

        elapsed = time.time() - start_time
        trace.span(
            name="approval_result",
            input={"approved": data.approved, "feedback": data.feedback},
            output={"status": status, "elapsed_seconds": elapsed},
        )

        return {
            "success": True,
            "status": status,
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/content/audit-image")
async def audit_image(content_id: str, user_id: str, file: UploadFile = File(...)):
    # Audit an uploaded image against Brand DNA rules using OpenAI vision model. Only APPROVER_B.
    try:
        trace = langfuse.trace(
            name="multimodal_audit",
            user_id=user_id,
            session_id=content_id,
        )

        start_time = time.time()
        user = gov_service.supabase.table("profile_users")\
            .select("role, is_active")\
            .eq("id", user_id)\
            .single()\
            .execute()
        if not user.data or not user.data["is_active"]:
            raise Exception("Invalid or inactive user")
        if user.data["role"] != "APPROVER_B":
            raise Exception("Only APPROVER_B can audit images")

        content = gov_service.get_content(content_id).data
        if not content:
            raise Exception("Content not found")
        if content["status"] not in ["pending", "approved"]:
            raise Exception("Content must be pending or approved for audit")
        brand_id = content["brand_dna_id"]

        trace.span(
            name="user_validation",
            input={"user_id": user_id, "content_id": content_id},
            output={"role": user.data["role"], "valid": True},
        )

        context_chunks = rag_service.search_brand_context(
            query="brand rules",
            brand_dna_id=brand_id
        )
        context = "\n".join([
            json.dumps(c, ensure_ascii=False) for c in context_chunks
        ])

        trace.span(
            name="rag_context_retrieval",
            input={"brand_id": brand_id, "query": "brand rules"},
            output={"chunks_retrieved": len(context_chunks)},
        )

        image_bytes = await file.read()
        audit_span = trace.span(
            name="gemini_vision_audit",
            input={"image_size": len(image_bytes), "context_length": len(context)},
        )
        result = audit_service.audit_image(image_bytes, context)
        audit_span.end(output={"approved": result.get("approved"), "score": result.get("score")})

        gov_service.supabase.table("content_items").update({
            "audit_result": result,
            "audit_status": "passed" if result.get("approved") else "failed"
        }).eq("id", content_id).execute()

        elapsed = time.time() - start_time
        trace.span(
            name="audit_result",
            output={
                "approved": result.get("approved"),
                "score": result.get("score"),
                "elapsed_seconds": elapsed,
            },
        )

        return {
            "success": True,
            "audit": result,
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/brands")
def list_brands(user_id: str = None, limit: int = 50):
    # List all brands with their basic info and manual.
    try:
        query = gov_service.supabase.table("brand_dna").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        query = query.order("created_at", desc=True).limit(limit)
        res = query.execute()
        brands = []
        for brand in res.data:
            brands.append({
                "id": brand["id"],
                "name": brand["name"],
                "tone": brand["tone"],
                "audience": brand["audience"],
                "description": brand["description"],
                "created_at": brand["created_at"],
                "manual": brand.get("manual", {}),
            })
        return {"success": True, "data": brands, "count": len(brands)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/brands/{brand_id}")
def get_brand(brand_id: str):
    # Fetch a single brand by ID.
    try:
        res = gov_service.supabase.table("brand_dna").select("*").eq("id", brand_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"success": True, "data": res.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/selection/brands")
def get_brands_for_selection(user_id: str = None):
    # Return a simplified brand list for UI selection dropdowns.
    try:
        query = gov_service.supabase.table("brand_dna").select("id, name, tone, audience, description, created_at")
        if user_id:
            query = query.eq("user_id", user_id)
        query = query.order("created_at", desc=True)
        res = query.execute()
        return {
            "success": True,
            "brands": [
                {
                    "id": b["id"],
                    "name": b["name"],
                    "tone": b["tone"],
                    "audience": b["audience"],
                    "description": b["description"],
                }
                for b in res.data
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/selection/content/{brand_id}")
def get_content_for_selection(brand_id: str, status: str = None):
    # Return content items for a specific brand, truncated for UI display.
    try:
        query = gov_service.supabase.table("content_items").select(
            "id, prompt, generated_content, status, audit_status, created_at"
        ).eq("brand_dna_id", brand_id)
        if status:
            query = query.eq("status", status)
        query = query.order("created_at", desc=True)
        res = query.execute()
        return {
            "success": True,
            "content_items": [
                {
                    "id": c["id"],
                    "prompt": c["prompt"],
                    "generated_content": c["generated_content"][:200] + "..." if len(c.get("generated_content", "")) > 200 else c.get("generated_content", ""),
                    "status": c["status"],
                    "audit_status": c.get("audit_status"),
                }
                for c in res.data
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
