# backend/main.py
import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, get_db, SessionLocal
from models import Message, User
from sqlalchemy.orm import Session
from schemas import LoginRequest, LoginResponse, RegisterRequest
from password_hash import get_password_hash, verify_password, create_access_token
from routers import customer
from routers.admin import admin_master_router
from routers.agent import agent_master_router
import requests
import os
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from passlib.exc import UnknownHashError

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Support Chatbot API")

# Include the routers by actor
app.include_router(admin_master_router)
app.include_router(agent_master_router)
app.include_router(customer.router)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
# CORS so React frontend can call this API
app.add_middleware(
    CORSMiddleware,
    # Ensure this is a LIST of specific strings, not a wildcard "*"
    allow_origins=[
        FRONTEND_ORIGIN,
        "https://chatbot-frontend-ten-pink.vercel.app",
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


@app.post("/api/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # 🟢 LAZY MIGRATION LOGIC
    try:
        # 1. Try to verify securely (Normal Path)
        if not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

    except UnknownHashError:
        # 2. Fallback: The DB password is not a valid hash (it's plain text)
        # Check if it matches exactly as a string
        if req.password == user.hashed_password:
            print(f"⚠️ Migrating user {user.email} to secure hash...")

            # A. Hash the password immediately
            new_hash = get_password_hash(req.password)

            # B. Save it to the database so this never happens again
            user.hashed_password = new_hash
            db.add(user)
            db.commit()

            # C. Allow login to proceed
        else:
            # Password was wrong anyway
            raise HTTPException(status_code=401, detail="Incorrect email or password")

    # 🟢 FIX: Generate a real JWT Token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )

    return {
        "access_token": access_token,  # 👈 Send this to frontend
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
    }


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    sender: Optional[str] = "user"


@app.post("/api/chat")
def proxy_chat_to_rasa(req: ChatRequest):
    rasa_url = os.getenv("RASA_WEBHOOK_URL", "http://rasa:5005/webhooks/rest/webhook")

    payload = {
        "sender": str(req.conversation_id) if req.conversation_id else "user",
        "message": req.message,
    }

    print(f"[DEBUG] Forwarding to Rasa at: {rasa_url} with payload: {payload}")

    try:

        response = requests.post(rasa_url, json=payload, timeout=10)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to Rasa: {e}")
        # Debug
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to Rasa: {str(e)}"
        )


@app.post("/api/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    # 1. Check if email exists
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash Password & Create User
    new_user = User(
        email=req.email,
        name=req.name,
        role=req.role,
        hashed_password=get_password_hash(req.password),
    )
    db.add(new_user)
    db.commit()

    return {"message": "Account created successfully"}
