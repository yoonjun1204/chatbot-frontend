# backend/models.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Date,
    Text,
    Float,
    Boolean,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from database import Base


# 1. Define the Singapore offset (+8)
def sg_now():
    return datetime.now(timezone(timedelta(hours=8)))


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender = Column(String, index=True)  # "user" or "bot"
    text = Column(String)
    created_at = Column(DateTime, default=sg_now)

    conversation = relationship("Conversation", back_populates="messages")


class User(Base):
    """
    Simple User table.
    For FYP you can keep plaintext passwords or simple hash,
    but in real life always hash properly.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # simple for demo/FYP
    name = Column(String, nullable=True)

    # NEW: role for access control
    # Possible values: "customer", "admin", "agent"
    role = Column(String, default="customer", nullable=False)

    # NEW fields for admin panel
    access = Column(JSON, default={})  # permissions
    status = Column(String, default="active")  # active | suspended
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )

    orders = relationship("Order", back_populates="user")


class Order(Base):
    """
    Order table linked to User.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True)
    status = Column(String, default="Processing")
    estimated_delivery = Column(Date, nullable=True)
    customer_name = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="orders")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )
    actor_id = Column(String, index=True)  # User ID or Session ID
    actor_email = Column(String, index=True, nullable=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    intent = Column(String)  # From Rasa
    confidence = Column(Float)  # Accuracy check
    response_time_ms = Column(Float)
    is_escalated = Column(Boolean, default=False)  # True if handed to human agent
    user_message_id = Column(Integer, nullable=True)  # Link to the Message.id
