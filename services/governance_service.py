import logging
from supabase import Client

logger = logging.getLogger(__name__)

class GovernanceService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def create_content(self, data: dict):
        # Create a new content item with pending status in Supabase.
        logger.info("Creating content")
        data["status"] = "pending"
        return self.supabase.table("content_items").insert(data).execute()

    def update_status(self, content_id: str, status: str, feedback: str = None):
        # Update content status (pending/approved/rejected) with optional feedback.
        logger.info(f"Updating content {content_id} to {status}")
        return (
            self.supabase.table("content_items")
            .update({
                "status": status,
                "feedback": feedback
            })
            .eq("id", content_id)
            .execute()
        )

    def get_content(self, content_id: str):
        # Fetch a single content item by ID from Supabase.
        logger.info(f"Fetching content {content_id}")
        return (
            self.supabase.table("content_items")
            .select("*")
            .eq("id", content_id)
            .single()
            .execute()
        )
