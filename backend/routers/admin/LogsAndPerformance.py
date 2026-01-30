# backend/routers/admin/LogsAndPerformance.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import ChatLog
from schemas import ChatLogResponse, PerformanceReport
from models import User
from dependencies import require_admin


router = APIRouter()


# 1. Filter logs by date & 5. Search by actor
@router.get("/", response_model=List[ChatLogResponse])
def get_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(ChatLog)

    if start_date:
        query = query.filter(ChatLog.timestamp >= start_date)
    if end_date:
        adjusted_end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
        query = query.filter(ChatLog.timestamp <= adjusted_end_date)
    if actor_email:
        query = query.filter(ChatLog.actor_email.ilike(f"%{actor_email}%"))

    return query.all()


# 2 & 3. Read Performance Reports (Accuracy, Response Time, Escalation)
@router.get("/performance-report", response_model=PerformanceReport)
def get_performance_report(
    admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    logs = db.query(ChatLog).all()
    if not logs:
        return {
            "total_conversations": 0,
            "average_accuracy": 0.0,
            "average_response_time_ms": 0.0,
            "escalation_rate": "0%",
            "escalation_count": 0,
        }

    total = len(logs)
    avg_accuracy = sum(l.confidence for l in logs) / total
    avg_response_time = sum(l.response_time_ms for l in logs) / total
    escalation_count = sum(1 for l in logs if l.is_escalated)

    return {
        "total_conversations": total,
        "average_accuracy": round(avg_accuracy, 2),
        "average_response_time_ms": round(avg_response_time, 2),
        "escalation_rate": f"{(escalation_count / total) * 100:.2f}%",
        "escalation_count": escalation_count,
    }


# 4. Remove old logs to save space
@router.delete("/cleanup")
def delete_logs_flexible(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor_email: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(ChatLog)

    # Apply filters only if they are provided
    if start_date:
        query = query.filter(ChatLog.timestamp >= start_date)
    if end_date:
        adjusted_end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
        query = query.filter(ChatLog.timestamp <= adjusted_end_date)
    if actor_email:
        query = query.filter(ChatLog.actor_email == actor_email)

    # Count how many will be deleted for the response message
    to_delete = query.count()

    # Execute deletion
    query.delete(synchronize_session=False)
    db.commit()

    return {"message": f"Successfully purged {to_delete} logs matching your criteria."}
