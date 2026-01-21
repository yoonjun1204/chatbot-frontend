# dependencies.py
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from typing import Optional


# Dependency to get current user from headers (simple FYP auth)
def get_current_user(
    current_user_id: Optional[int] = Header(None, alias="user_id"),
    db: Session = Depends(get_db),
):
    """
    Expects `user_id` in request headers
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Missing user_id header")

    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
