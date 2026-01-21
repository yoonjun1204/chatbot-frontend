# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    intent: str
    entities: Dict[str, Any]
    quick_replies: List[str]
    payload: Dict[str, Any]


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str


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
