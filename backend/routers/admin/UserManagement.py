# backend/routers/admin/UserManagement.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from dependencies import require_admin
from schemas import CreateAgentRequest, UpdateUserRequest
from typing import Optional
from models import User
from fastapi import Depends, HTTPException
from sqlalchemy.orm.attributes import flag_modified
from password_hash import get_password_hash

router = APIRouter()


# Admin endpoints for managing users (agents/admins)
@router.get("/")
def list_users(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # 🟢 FIX: Include 'customer' in the query so the Dashboard can count them
    query = db.query(User).filter(User.role.in_(["admin", "agent", "customer"]))

    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))

    users = query.all()

    result = []
    for u in users:
        # Default access for agents
        access = u.access or {
            "can_view_chats": True,
            "can_reply": True,
            "can_close_chat": False,
        }

        # Override for Admins (Full Control)
        if u.role == "admin":
            access = {
                "can_view_chats": True,
                "can_reply": True,
                "can_close_chat": True,
            }

        # 🟢 NEW: Override for Customers (Limited Control/View only)
        elif u.role == "customer":
            access = {
                "can_view_chats": False,
                "can_reply": False,
                "can_close_chat": False,
            }

        result.append(
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "status": u.status or "active",
                "access": access,
            }
        )

    return result


# 🟢 FIXED ENDPOINT: create_agent
@router.post("/")
def create_agent(
    req: CreateAgentRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    # 1. Check if email already exists
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # 2. Hash the password
    # We take the raw password from the request and hash it
    secure_password = get_password_hash(req.password)

    # 3. Create Agent (using 'hashed_password' column)
    agent = User(
        name=req.name,
        email=req.email,
        hashed_password=secure_password,  # ✅ CORRECT FIELD NAME
        role="agent",
        access=req.access,
        status="active",
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {"message": "Human agent created", "id": agent.id}


# Endpoint to update user (agent/admin) details
@router.put("/{user_id}")
def update_user(
    user_id: int,
    req: UpdateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update Name and Email if provided
    if req.name is not None:
        user.name = req.name
    if req.email is not None:
        # Optional: Check if email is already taken by someone else
        existing = (
            db.query(User).filter(User.email == req.email, User.id != user_id).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = req.email

    # Existing permission/status logic
    if user.role == "admin" and req.access is not None:
        raise HTTPException(status_code=400, detail="Cannot modify admin permissions")

    if req.access is not None:
        user.access = req.access
        flag_modified(user, "access")

    if req.status is not None:
        user.status = req.status

    db.commit()
    return {"message": "User updated successfully"}


# Endpoint to delete a user
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    if user_to_delete.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user_to_delete)
    db.commit()

    return {"detail": "User deleted successfully"}
