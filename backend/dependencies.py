# backend/dependencies.py
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from typing import Optional


# Dependency to get current user from headers (simple FYP auth)
def get_current_user(
    current_user_id: Optional[str] = Header(None, alias="user_id"),  # Change int to str
    db: Session = Depends(get_db),
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Missing user_id header")

    # Try to convert to int, if it fails (like "anonymous"), it's not a valid Admin/Agent
    try:
        user_id_int = int(current_user_id)
        user = db.query(User).filter(User.id == user_id_int).first()
    except ValueError:
        # It's a string like "anonymous", which isn't in the User table
        raise HTTPException(status_code=404, detail="User not found (Non-numeric ID)")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
