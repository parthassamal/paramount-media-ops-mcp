"""API endpoints for mission-control chatbot assistant."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mcp.chatbot import OpsChatbotService

router = APIRouter(prefix="/api/chatbot", tags=["Mission Control Chatbot"])
chatbot_service = OpsChatbotService()


class ChatAskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Operator question")
    session_id: Optional[str] = Field(default=None, description="Chat session id")
    incident_id: Optional[str] = Field(default=None, description="Optional Jira incident id")


class Citation(BaseModel):
    source: str
    reference: str


class ChatAskResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation]
    quality_score: float
    tool_trace: List[str]
    generated_at: str
    duration_ms: int


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]


@router.post("/ask", response_model=ChatAskResponse)
async def ask_chatbot(request: ChatAskRequest):
    """Ask mission-control assistant for operator guidance."""
    try:
        result = chatbot_service.ask(
            question=request.question,
            session_id=request.session_id,
            incident_id=request.incident_id,
        )
        return ChatAskResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot request failed: {exc}") from exc


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Return recent in-memory chat history for a session."""
    return ChatHistoryResponse(
        session_id=session_id,
        messages=chatbot_service.get_history(session_id),
    )
