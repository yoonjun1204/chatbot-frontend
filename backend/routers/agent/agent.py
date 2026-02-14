# backend/routers/agent/agent.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Conversation, Message, ChatLog, User
from schemas import AgentMessageRequest, EndChatRequest
import time
from dependencies import get_current_user
from typing import List
from schemas import ConversationResponse
from sqlalchemy import or_

router = APIRouter()


@router.get("/pending_chats", response_model=List[ConversationResponse])
def get_pending_chats(
    db: Session = Depends(get_db), current_agent: User = Depends(get_current_user)
):
    """
    Fetch chats for the Agent Dashboard.
    Fixed: Joins with User table to return 'email' string instead of 'user_id' integer.
    """

    # 1. Query Conversation + User Email
    results = (
        db.query(Conversation, User.email)
        .join(User, Conversation.user_id == User.id)  # Join to get the email
        .filter(
            # Filter by Status: Only show Waiting or Active chats
            Conversation.status.in_(["waiting_for_agent", "active_agent"]),
            # Filter by Ownership: Unassigned OR Assigned to Me
            or_(
                Conversation.assigned_agent_id == current_agent.id,
                Conversation.assigned_agent_id == None,
            ),
        )
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    # 2. Reconstruct the response manually to fix the Type Error
    response_list = []
    for conv, user_email in results:
        response_list.append(
            {
                "id": conv.id,
                "user_id": user_email,  # ✅ SWAP: Using Email (str) instead of ID (int)
                "title": conv.title,
                "status": conv.status,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "assigned_agent_id": conv.assigned_agent_id,
            }
        )

    return response_list


# 2. AGENT JOINS A CHAT
@router.post("/join_chat/{conversation_id}")
def join_chat(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Update Status
    conv.status = "active_agent"

    # Notify User
    sys_msg = Message(
        conversation_id=conv.id,
        sender="bot",
        text="An agent has joined the chat. You are now speaking with a human.",
    )
    db.add(sys_msg)
    db.commit()

    return {"status": "joined", "conversation_id": conversation_id}


# 3. AGENT SENDS A MESSAGE (Fixed Schema)
@router.post("/message")
def agent_send_message(
    req: AgentMessageRequest,
    db: Session = Depends(get_db),
    current_agent: User = Depends(get_current_user),
):
    start_time = time.time()
    """
    Uses AgentMessageRequest to ensure we don't need a user_id.
    """
    # Double check conversation exists
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Create the message
    agent_msg = Message(
        conversation_id=req.conversation_id, sender="agent", text=req.message
    )
    db.add(agent_msg)
    db.commit()

    # Save to Analytics ChatLog
    duration_ms = (time.time() - start_time) * 1000
    analytics_log = ChatLog(
        conversation_id=conv.id,
        user_message="",  # User didn't say anything here, it's an agent reply
        actor_id=str(current_agent.id),
        actor_email=current_agent.email,
        bot_response=req.message,  # We treat the Agent's text as the "response"
        intent="human_agent_reply",  # Custom intent so you can filter it later
        confidence=1.0,  # 100% confidence because it's a human
        response_time_ms=duration_ms,  # No processing time needed
    )
    db.add(analytics_log)
    db.commit()

    return {"status": "sent", "message_id": agent_msg.id}


@router.post("/end_chat")
def agent_end_chat(req: EndChatRequest, db: Session = Depends(get_db)):
    """
    Agent ends the session. Conversation goes back to 'active_bot'.
    """
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat not found")

    # 1. Change status back to bot
    conv.status = "active_bot"

    # 2. System message
    sys_msg = Message(
        conversation_id=conv.id,
        sender="bot",  # System message usually comes from 'bot' or 'system'
        text="The agent has ended the session. You are now connected to the virtual assistant.",
    )
    db.add(sys_msg)
    db.commit()

    return {"status": "ended", "conversation_id": conv.id}
