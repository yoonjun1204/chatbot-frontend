# backend/routers/customer.py
from models import Conversation, Message, User, ChatLog
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
        conv = Conversation(
            user_id=current_email, title="New Chat", created_at=datetime.now(SGT)
        )
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
    db.flush()

    # AUTO-TITLE LOGIC: Update title if this is the first user message
    msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
    if msg_count == 1:
        # Use first 25 chars of the first message as the title
        new_title = req.message[:25] + ("..." if len(req.message) > 25 else "")
        conv.title = new_title

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
    db.refresh(user_msg)
    db.refresh(bot_msg)

    # 6. Quick replies
    quick_replies = get_quick_replies(intent)

    return ChatResponse(
        conversation_id=conv.id,
        reply=reply_text,
        user_message_id=user_msg.id,
        bot_message_id=bot_msg.id,
        intent=intent,
        entities=entities,
        quick_replies=quick_replies,
        payload=payload,
    )


@router.get("/conversations")
def get_user_chat_history(user_email: str, db: Session = Depends(get_db)):
    """Fetches the list of all chat sessions for the sidebar."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_email)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    # 1. Find the conversation
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Delete associated messages first (if not using cascade delete in DB)
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()

    # 3. Delete the conversation itself
    db.delete(conv)
    db.commit()
    return {"message": "Chat deleted successfully"}


@router.patch("/message/{message_id}")
def edit_message(message_id: int, req: ChatRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    # 1. Find the target message
    user_msg = db.query(Message).filter(Message.id == message_id).first()
    if not user_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    conv_id = user_msg.conversation_id

    # 2. Delete all messages that happened AFTER this one in this conversation
    # This keeps the history clean like Gemini
    db.query(Message).filter(
        Message.conversation_id == conv_id, Message.id > message_id
    ).delete()

    # 3. Update the text of the message
    user_msg.text = req.message
    db.commit()

    # 4. Generate a NEW response (Reuse your existing logic)
    intent, entities, confidence = parse_message(req.message)
    reply_text, payload = handle_intent(intent, entities, db=db)

    if reply_text is None:
        rasa_responses = get_rasa_response(
            req.message, sender_id=str(conv_id), actor_email=req.user_id, db=db
        )
        reply_text = (
            "\n".join([m.get("text", "") for m in rasa_responses])
            if rasa_responses
            else "AI Error"
        )

    # Calculate how long the "Edit" took to process
    duration_ms = (time.time() - start_time) * 1000

    # 4. UPDATE THE LOG
    existing_log = (
        db.query(ChatLog).filter(ChatLog.user_message_id == message_id).first()
    )
    if existing_log:
        existing_log.user_message = req.message
        existing_log.bot_response = reply_text
        existing_log.intent = intent
        existing_log.confidence = confidence
        existing_log.response_time_ms = duration_ms
        db.commit()

    # 5. Save the new bot message
    bot_msg = Message(conversation_id=conv_id, sender="bot", text=reply_text)
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return ChatResponse(
        conversation_id=conv_id,
        reply=reply_text,
        user_message_id=user_msg.id,
        bot_message_id=bot_msg.id,
        intent=intent,
        entities=entities,
        quick_replies=get_quick_replies(intent),
        payload=payload,
    )
