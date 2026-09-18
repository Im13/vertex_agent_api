from typing import Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A chat message from user or agent."""
    role: str = Field(..., description="Role: 'user' or 'model'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request to chat with an agent."""
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(default="default_user", description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Response from agent."""
    agent: str = Field(..., description="Agent name")
    message: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(..., description="Response timestamp")


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    agent: str
    user_id: str
    message_count: int
    created_at: Optional[str] = None


class AgentInfo(BaseModel):
    """Agent information."""
    name: str
    description: str
    model: str
    available: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    agents_available: int

//Add to rebuild