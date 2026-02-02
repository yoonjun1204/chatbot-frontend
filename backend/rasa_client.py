# backend/rasa_client.py
import os
import requests
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import ChatLog, User
import traceback

RASA_URL = os.getenv(
    "RASA_URL", "https://rasa-chatbot-784693230618.asia-southeast1.run.app/model/parse"
)
# 🆕 New URL for full conversation flow (Core + Action Server)
RASA_WEBHOOK_URL = os.getenv(
    "RASA_WEBHOOK_URL",
    "https://rasa-chatbot-784693230618.asia-southeast1.run.app/webhooks/rest/webhook",
)

# Define Singapore Time offset
SGT = timezone(timedelta(hours=8))


def parse_message(message: str):
    """
    Uses Rasa NLU to get intent, entities, AND confidence.
    """
    payload = {"text": message}
    try:
        r = requests.post(RASA_URL, json=payload)
        r.raise_for_status()
        data = r.json()

        # 1. Extract Intent Name
        intent_data = data.get("intent", {})
        intent_name = intent_data.get("name")

        # 2. Extract Confidence (Default to 0.0 if missing)
        confidence = intent_data.get("confidence", 0.0)

        # 3. Extract Entities
        entities = {e["entity"]: e["value"] for e in data.get("entities", [])}

        # Return ALL THREE
        return intent_name, entities, confidence

    except Exception as e:
        print(f"Rasa NLU Error: {e}")
        # Return safe defaults on error
        return None, {}, 0.0


def get_rasa_response(message: str, sender_id: str, actor_email: str, db: Session):
    """
    Sends message to Rasa, measures performance, and logs to DB.
    """
    # 1. Start timer for "Response Time" metric
    start_time = time.time()

    # 2. Get NLU data (Intent & Confidence/Accuracy)
    intent_name, _, confidence = parse_message(message)

    payload = {"sender": sender_id, "message": message}

    try:
        # 3. Call Rasa Webhook for the actual bot response
        r = requests.post(RASA_WEBHOOK_URL, json=payload, timeout=30)
        r.raise_for_status()
        rasa_output = r.json()

        # 4. Stop timer and calculate duration
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # 5. Extract response text and check for escalation
        bot_text = (
            " ".join([m.get("text", "") for m in rasa_output])
            if rasa_output
            else "No response"
        )

        # Logic for Escalation Rate:
        # Flagged if confidence is low OR if the intent is "out_of_scope"
        is_escalated = confidence < 0.6 or intent_name == "out_of_scope"

        db_user = db.query(User).filter(User.email == actor_email).first()
        db_id = str(db_user.id) if db_user else "Guest"

        # USE THE HELPER
        save_chat_log(
            db,
            actor_id=db_id,
            actor_email=actor_email,
            msg=message,
            res=bot_text,
            intent=intent_name,
            conf=confidence,
            duration=duration_ms,
            escalated=(confidence < 0.6 or intent_name == "out_of_scope"),
        )

        return rasa_output

    except Exception as e:
        print(f"🔥 CRITICAL RASA ERROR: {e}")
        traceback.print_exc()
        # Log the failure even if Rasa is down
        save_chat_log(
            db,
            actor_id="System",
            actor_email=actor_email,
            msg=message,
            res="ERROR",
            intent="system_error",
            conf=0.0,
            duration=0.0,
            escalated=True,
        )
        return []


def save_chat_log(
    db: Session,
    actor_id: str,
    actor_email: str,
    msg: str,
    res: str,
    intent: str,
    conf: float,
    duration: float,
    escalated: bool,
):
    """
    Unified helper to save performance metrics to the ChatLog table.
    """
    new_log = ChatLog(
        actor_id=actor_id,
        actor_email=actor_email,
        user_message=msg,
        bot_response=res,
        intent=intent or "unknown",
        confidence=conf or 0.0,
        response_time_ms=duration,
        is_escalated=escalated,
        timestamp=datetime.now(SGT),
    )
    db.add(new_log)
    db.commit()
