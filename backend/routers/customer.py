# backend/routers/customer.py
from models import Conversation, Message, User, ChatLog
from fastapi import APIRouter, Depends, HTTPException, Header
from schemas import ChatRequest, ChatResponse, EndChatRequest
from sqlalchemy.orm import Session
from sqlalchemy import func
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

    # ============================================================
    # 🟢 FIXED: AGENT ESCALATION HANDLING (Now with Logging)
    # ============================================================

    # CASE 1 & 2 Combined: Customer is waiting OR talking to agent
    if conv.status in ["waiting_for_agent", "active_agent"]:
        # 1. Save Message
        user_msg = Message(conversation_id=conv.id, sender="user", text=req.message)
        db.add(user_msg)
        db.commit()

        # 2. Determine Reply Status
        reply_txt = ""
        intent_label = "human_conversation"
        if conv.status == "waiting_for_agent":
            reply_txt = "Please wait, an agent will be with you shortly."
            intent_label = "system_wait"

        # 3. 🆕 ADD THIS: Save to Analytics ChatLog
        # We need to record what the user said, even if the bot didn't reply
        analytics_log = ChatLog(
            conversation_id=conv.id,
            actor_id=actual_user_id_str,  # Use the ID calculated earlier
            actor_email=conv.user_id,
            user_message=req.message,
            bot_response=reply_txt,
            intent=intent_label,
            confidence=1.0,
            response_time_ms=0,
        )
        db.add(analytics_log)
        db.commit()

        return ChatResponse(
            conversation_id=conv.id,
            reply=reply_txt,
            user_message_id=user_msg.id,
            bot_message_id=0,
            intent=intent_label,
            confidence=1.0,
        )

    # ============================================================
    # 🟢 STANDARD BOT FLOW STARTS HERE
    # ============================================================

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

    # 2. Get the Conversation to check status
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == user_msg.conversation_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # =========================================================
    # 🛑 CASE A: HUMAN AGENT CONNECTED
    # =========================================================
    if conv.status in ["active_agent", "waiting_for_agent"]:
        user_msg.text = req.message

        # 🟢 FIX: Update the Analytics Log & ensure Conversation ID is there
        existing_log = (
            db.query(ChatLog).filter(ChatLog.user_message_id == message_id).first()
        )
        if existing_log:
            existing_log.user_message = req.message
            existing_log.conversation_id = conv.id  # ✅ Explicitly set/confirm ID
            # Optional: Mark as edited in log for clarity
            existing_log.intent = "user_edit_during_human_session"
            db.commit()

        return ChatResponse(
            conversation_id=conv.id,
            reply=None,
            user_message_id=user_msg.id,
            bot_message_id=None,
            intent=None,
            entities={},
            quick_replies=[],
            payload={},
        )

    # =========================================================
    # 🤖 CASE B: BOT MODE
    # =========================================================

    # 3. Delete messages that happened AFTER this one
    db.query(Message).filter(
        Message.conversation_id == conv.id, Message.id > message_id
    ).delete()

    # 4. Update the text of the message
    user_msg.text = req.message
    db.commit()

    # 5. Generate a NEW response
    intent, entities, confidence = parse_message(req.message)
    reply_text, payload = handle_intent(intent, entities, db=db)

    if reply_text is None:
        rasa_responses = get_rasa_response(
            req.message, sender_id=str(conv.id), actor_email=req.user_id, db=db
        )
        reply_text = (
            "\n".join([m.get("text", "") for m in rasa_responses])
            if rasa_responses
            else "AI Error"
        )

    duration_ms = (time.time() - start_time) * 1000

    # 6. 🟢 UPDATE THE LOG (With ID Fix)
    existing_log = (
        db.query(ChatLog).filter(ChatLog.user_message_id == message_id).first()
    )
    if existing_log:
        existing_log.user_message = req.message
        existing_log.bot_response = reply_text
        existing_log.intent = intent
        existing_log.confidence = confidence
        existing_log.response_time_ms = duration_ms
        existing_log.conversation_id = conv.id  # ✅ Ensure ID is saved
        db.commit()

    # 7. Save the new bot message
    bot_msg = Message(conversation_id=conv.id, sender="bot", text=reply_text)
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return ChatResponse(
        conversation_id=conv.id,
        reply=reply_text,
        user_message_id=user_msg.id,
        bot_message_id=bot_msg.id,
        intent=intent,
        entities=entities,
        quick_replies=get_quick_replies(intent),
        payload=payload,
    )


@router.post("/escalate")
def escalate_conversation(req: ChatRequest, db: Session = Depends(get_db)):
    """Triggered when user clicks 'Talk to Human' button"""

    # 1. Validation (Keep your existing checks)
    if not req.conversation_id:
        raise HTTPException(status_code=400, detail="Conversation ID required")

    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 🛑 NEW: CHECK FOR ANY OTHER ACTIVE CHATS
    # We look for ANY chat by this user that is currently 'waiting' or 'active'
    # excluding the current one (just in case)
    existing_active_chat = (
        db.query(Conversation)
        .filter(Conversation.user_id == conv.user_id)
        .filter(Conversation.status.in_(["waiting_for_agent", "active_agent"]))
        .filter(Conversation.id != conv.id)  # Don't count the current one
        .first()
    )

    if existing_active_chat:
        return {
            "message": "Limit Reached",
            "reply": f"You are already connected to an agent in Chat #{existing_active_chat.id}. Please finish that conversation first.",
        }

    # Case 1: Already waiting?
    if conv.status == "waiting_for_agent":
        return {"message": "Already waiting", "reply": "You are already in the queue."}

    # Case 2: Already connected?
    if conv.status == "active_agent":
        return {
            "message": "Already connected",
            "reply": "You are already connected to a human agent.",
        }

    # ============================================================
    # 🧠 LEAST BUSY AGENT ALGORITHM
    # ============================================================

    # A. Get all users who are "agents"
    # (Make sure your User model has a 'role' column, or filter by email domain)
    all_agents = db.query(User).filter(User.role == "agent").all()

    target_agent = None

    if not all_agents:
        # Fallback: No agents exist in the system at all
        print("⚠️ No agents found in database!")
        # We will just put them in the general queue (unassigned)
    else:
        # B. Count active chats for each agent
        # We query the DB to see how many 'active_agent' chats each person has
        busy_counts = (
            db.query(Conversation.assigned_agent_id, func.count(Conversation.id))
            .filter(Conversation.status == "active_agent")
            .filter(Conversation.assigned_agent_id != None)
            .group_by(Conversation.assigned_agent_id)
            .all()
        )

        # Convert DB result to a dictionary: {agent_id: count}
        # e.g., {1: 5, 2: 0, 3: 2}
        workload = {agent.id: 0 for agent in all_agents}  # Start everyone at 0
        for agent_id, count in busy_counts:
            if agent_id in workload:
                workload[agent_id] = count

        # C. Find the agent with the MINIMUM count
        # This sorts the agents by workload and picks the first one
        best_agent_id = min(workload, key=workload.get)

        # D. Fetch the actual agent object
        target_agent = db.query(User).filter(User.id == best_agent_id).first()

    # ============================================================
    # 📝 UPDATE CONVERSATION
    # ============================================================

    conv.status = "waiting_for_agent"

    if target_agent:
        conv.assigned_agent_id = target_agent.id
        reply_msg = f"Connecting you to agent {target_agent.email}. Please wait..."
    else:
        conv.assigned_agent_id = None  # General Queue
        reply_msg = (
            "All agents are currently busy. You have been placed in the priority queue."
        )

    # Create System Message
    sys_msg = Message(
        conversation_id=conv.id,
        sender="bot",
        text=reply_msg,
    )
    db.add(sys_msg)
    db.commit()

    return {
        "message": "Escalation successful",
        "reply": sys_msg.text,
        "assigned_to": target_agent.email if target_agent else "General Queue",
    }


@router.post("/end_chat")
def end_chat(req: EndChatRequest, db: Session = Depends(get_db)):
    """
    Customer ends the human session. Status reverts to 'active_bot'.
    """
    # Note: We don't need to check req.message anymore because EndChatRequest doesn't have it.

    if not req.conversation_id:
        raise HTTPException(status_code=400, detail="Conversation ID required")

    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Only allow ending if currently waiting or talking to agent
    if conv.status == "active_bot":
        return {"message": "Already in bot mode"}

    # 1. Revert Status
    conv.status = "active_bot"

    # 2. Add System Message
    sys_msg = Message(
        conversation_id=conv.id,
        sender="bot",
        text="Human support session ended. You are back with the virtual assistant.",
    )
    db.add(sys_msg)
    db.commit()

    return {"message": "Chat ended", "reply": sys_msg.text}
