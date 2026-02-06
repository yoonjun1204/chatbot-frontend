# backend/main.py
import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, get_db, SessionLocal
from models import Message, User
from sqlalchemy.orm import Session
from schemas import LoginRequest, LoginResponse
from routers import customer
from routers.admin import admin_master_router
import requests
import os
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# docker exec -it chatbot_db psql -U chatbot_user -d chatbot_db
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Support Chatbot API")

# Include the routers by actor
app.include_router(admin_master_router)
# app.include_router(agent.router) # Uncomment it when agent routes are ready
app.include_router(customer.router)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
# CORS so React frontend can call this API
app.add_middleware(
    CORSMiddleware,
    # Ensure this is a LIST of specific strings, not a wildcard "*"
    allow_origins=[
        FRONTEND_ORIGIN,
        "https://chatbot-frontend-ten-pink.vercel.app", # Add your specific Vercel URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@app.post("/api/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # 1. Find user by email
    user = db.query(User).filter(User.email == req.email).first()

    # 2. Basic password check (plaintext for demo/FYP)
    if not user or user.password != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # 3. Return basic profile + role
    return LoginResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role or "customer",
    )


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    sender: Optional[str] = "user"


@app.post("/api/chat")
def proxy_chat_to_rasa(req: ChatRequest):
    rasa_url = os.getenv("RASA_WEBHOOK_URL", "http://rasa:5005/webhooks/rest/webhook")

    payload = {
        "sender": str(req.conversation_id) if req.conversation_id else "user",
        "message": req.message
    }

    print(f"[DEBUG] Forwarding to Rasa at: {rasa_url} with payload: {payload}")

    try:
        
        response = requests.post(rasa_url, json=payload, timeout=10)
        response.raise_for_status()

        
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to Rasa: {e}")
        # Debug
        raise HTTPException(status_code=500, detail=f"Failed to connect to Rasa: {str(e)}")