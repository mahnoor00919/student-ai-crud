from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.graph.workflow import run_chat, clear_thread

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: Optional[str] = Field(default="default", max_length=100)


class ChatResponse(BaseModel):
    response: str
    success: bool = False
    needs_clarification: bool = False
    tool_result: Optional[dict] = None
    thread_id: str = "default"


@router.post("/chat", response_model=ChatResponse)
def ai_chat(body: ChatRequest, db: Session = Depends(get_db)):
    """
    Natural-language CRUD endpoint.
    LLM extracts intent → LangGraph orchestrates → controlled tools hit the DB.
    """
    result = run_chat(
        user_message=body.message.strip(),
        db=db,
        thread_id=body.thread_id or "default",
    )
    return ChatResponse(**result)


@router.post("/reset")
def reset_conversation(thread_id: str = "default"):
    clear_thread(thread_id)
    return {"message": f"Conversation thread '{thread_id}' cleared."}
