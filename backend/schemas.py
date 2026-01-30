# backend/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


# --- customer.py ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    intent: Optional[str] = "unknown"
    entities: Optional[Dict[str, Any]] = {}
    quick_replies: Optional[List[str]] = []
    payload: Optional[Dict[str, Any]] = {}


# --- main.py ---
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str


# --- UserManagement.py ---
class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    # Adding "= None" ensures the API doesn't crash if one is missing
    access: Optional[Dict[str, bool]] = None
    status: Optional[str] = None


class CreateAgentRequest(BaseModel):
    name: str
    email: str
    password: str
    access: Dict[str, bool]


# --- LogsAndPerformance.py ---
class ChatLogBase(BaseModel):
    actor_id: str
    actor_email: Optional[str] = "anonymous"
    user_message: str
    bot_response: str
    intent: Optional[str] = None
    confidence: Optional[float] = 0.0
    response_time_ms: float
    is_escalated: bool = False


class ChatLogCreate(ChatLogBase):
    """Schema for creating a new log (used internally when the bot responds)"""

    pass


class ChatLogResponse(ChatLogBase):
    """Schema for returning log data to the Admin dashboard"""

    id: int
    timestamp: datetime

    # This allows Pydantic to read data from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


class PerformanceReport(BaseModel):
    total_conversations: int
    average_accuracy: float
    average_response_time_ms: float
    escalation_rate: str
    escalation_count: int


class CleanupResponse(BaseModel):
    message: str
