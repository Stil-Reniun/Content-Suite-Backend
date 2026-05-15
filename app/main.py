import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_router import router as auth_router
from routes.brand_dna_router import router as brand_router
from routes.governance_router import router as gov_router
from core.langfuse_client import langfuse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Content Suite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(brand_router, prefix="/api", tags=["Brand DNA"])
app.include_router(gov_router, prefix="/api/gov", tags=["Governance"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Content Suite API"}

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down, flushing Langfuse events...")
    from core.langfuse_client import flush_langfuse
    flush_langfuse()


