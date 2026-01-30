# backend/routers/customer.py
from models import Conversation, Message, User, Order
from fastapi import APIRouter, Depends, HTTPException, Header
from schemas import ChatRequest, ChatResponse
from sqlalchemy.orm import Session
from database import get_db
from nlp import handle_intent, get_quick_replies
from rasa_client import parse_message, get_rasa_response, save_chat_log
from datetime import datetime, timedelta, timezone
import time

router = APIRouter(prefix="/api/customer", tags=["Customer"])

# Define Singapore Time offset
SGT = timezone(timedelta(hours=8))


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    # 1. Determine Identity
    # Use the email passed from the frontend
    current_email = req.user_id if req.user_id else "anonymous"

    # 🆕 NEW: Look up the real Database User ID (e.g., Alice = 3)
    db_user = db.query(User).filter(User.email == current_email).first()
    # We will use this for the 'actor_id' in logs
    actual_user_id_str = str(db_user.id) if db_user else "Guest"

    # 2. Find or create conversation
    if req.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == req.conversation_id)
            .first()
        )
    else:
        conv = None

    if not conv:
        conv = Conversation(user_id=current_email, created_at=datetime.now(SGT))
        db.add(conv)
        db.commit()
        db.refresh(conv)
    else:
        # Update email if they logged in mid-session
        if current_email != "anonymous" and conv.user_id != current_email:
            conv.user_id = current_email
            db.commit()

    # ... (Step 2 & 3: Message storage and NLP remain the same) ...
    user_msg = Message(conversation_id=conv.id, sender="user", text=req.message)
    db.add(user_msg)

    intent, entities, confidence = parse_message(req.message)

    # 4. Handle intent with Hybrid/Rasa Logic
    reply_text, payload = handle_intent(intent, entities, db=db)

    if reply_text is None:
        # DELEGATE TO RASA
        rasa_responses = get_rasa_response(
            req.message,
            sender_id=str(conv.id),
            actor_email=conv.user_id,  # This is the email (alicetan@...)
            db=db,
        )
        # Note: You need to ensure get_rasa_response uses actual_user_id_str
        # inside its save_chat_log call. See below.

        if rasa_responses:
            texts = [m.get("text", "") for m in rasa_responses if m.get("text")]
            reply_text = (
                "\n".join(texts) if texts else "I couldn't generate a response."
            )
        else:
            reply_text = "Sorry, I am having trouble reaching the AI engine."
    else:
        # LOCAL LOGGING (Hybrid Logic)
        duration_ms = (time.time() - start_time) * 1000
        save_chat_log(
            db,
            actor_id=actual_user_id_str,  # 🆕 CHANGED: Now "3" instead of "4"
            actor_email=conv.user_id,  # "alicetan@example.com"
            msg=req.message,
            res=reply_text,
            intent=intent,
            conf=confidence,
            duration=duration_ms,
            escalated=False,
        )

    # 5. Store bot message & return
    bot_msg = Message(conversation_id=conv.id, sender="bot", text=reply_text)
    db.add(bot_msg)
    db.commit()

    # 6. Quick replies
    quick_replies = get_quick_replies(intent)

    return ChatResponse(
        conversation_id=conv.id,
        reply=reply_text,
        intent=intent,
        entities=entities,
        quick_replies=quick_replies,
        payload=payload,
    )
