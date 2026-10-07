"""Structured output schemas for LLM intent extraction."""
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    READ_ALL = "READ_ALL"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CONFIRM_DELETE = "CONFIRM_DELETE"
    CLARIFY = "CLARIFY"
    UNKNOWN = "UNKNOWN"
    CHITCHAT = "CHITCHAT"


class ExtractedFields(BaseModel):
    name: Optional[str] = None
    roll_number: Optional[int] = None
    age: Optional[int] = None
    email: Optional[str] = None
    # For updates – the new values
    new_name: Optional[str] = None
    new_roll_number: Optional[int] = None
    new_age: Optional[int] = None
    new_email: Optional[str] = None
    # Identifiers
    student_id: Optional[int] = None
    # Confirmation
    confirmed: Optional[bool] = None


class IntentResult(BaseModel):
    intent: IntentType = IntentType.UNKNOWN
    fields: ExtractedFields = Field(default_factory=ExtractedFields)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None
    raw_summary: Optional[str] = None

class GraphState(BaseModel):
    """LangGraph state – persists across conversational turns via thread_id."""

    messages: List[Dict[str, str]] = Field(default_factory=list)
    user_message: str = ""
    intent_result: Optional[IntentResult] = None
    missing_fields: List[str] = Field(default_factory=list)
    pending_operation: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    response: str = ""
    needs_clarification: bool = False
    thread_id: str = "default"

    # Runtime-only CRUD tools
    tools: Optional[Any] = None

    model_config = {"arbitrary_types_allowed": True}