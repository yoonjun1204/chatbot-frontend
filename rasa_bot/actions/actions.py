import re
import json
import os
from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted
from rasa_sdk.types import DomainDict

# Third-party library for fuzzy string matching
from rapidfuzz import process, fuzz


# =========================================================
# Service Layer: Mock Database Service (Future-proof)
# =========================================================
class DatabaseService:
    """
    Service layer that simulates database access.
    This class is designed to be replaced by a real PostgreSQL
    implementation without changing the Action layer.
    """

    def __init__(self):
        # Mock order table
        self.orders = {
            "ORD-10001": {"status": "Processing", "delivery_date": "2026-02-01"},
            "ORD-10002": {"status": "Shipped", "delivery_date": "2026-01-25"},
            "ORD-10003": {"status": "Delivered", "delivery_date": "2026-01-20"},
        }

        # Mock chat history table
        self.chat_history = [
            {
                "sender": "user",
                "message": "I want to return an item",
                "time": "2025-12-01 10:00:00",
            },
            {
                "sender": "bot",
                "message": "You can return items within 30 days.",
                "time": "2025-12-01 10:00:05",
            },
            {
                "sender": "user",
                "message": "How do I track my order ORD-10002?",
                "time": "2026-01-15 09:30:00",
            },
            {
                "sender": "bot",
                "message": "Your order ORD-10002 is currently shipped.",
                "time": "2026-01-15 09:30:10",
            },
        ]

    def get_order_status(self, order_id: Text) -> Optional[Dict[Text, Any]]:
        """
        Retrieve order status for a given order ID.
        """
        return self.orders.get(order_id)

    def create_support_ticket(self, issue_description: Text) -> Text:
        """
        Simulate creating a support ticket.
        """
        ticket_id = f"TICKET-{len(self.orders) + 1000}"
        return ticket_id

    def search_chat_history(self, keyword: Text) -> List[Dict[str, str]]:
        """
        Search chat history messages by keyword.
        """
        keyword_lower = keyword.lower()
        return [
            entry
            for entry in self.chat_history
            if keyword_lower in entry["message"].lower()
        ]


# Global service instance
db_service = DatabaseService()


ORD_PAT = re.compile(r"\bORD[-\s]?\d{3,}\b", re.IGNORECASE)
DIGITS_PAT = re.compile(r"\b\d{5,}\b")

def _normalize_order_id(raw: str) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip().upper()

    # common cleanup
    s = s.replace("_", "-").replace(" ", "")
    # Accept ORD10002 -> ORD-10002
    m = re.match(r"^(ORD)(\d{3,})$", s)
    if m:
        return f"ORD-{m.group(2)}"

    # Accept ORD-10002 already
    m = re.match(r"^(ORD)-(\d{3,})$", s)
    if m:
        return s

    # Accept digits only -> interpret as ORD-xxxxx (only if length >= 5)
    if re.match(r"^\d{5,}$", s):
        return f"ORD-{s}"

    return None

def _extract_order_id_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    # Prefer explicit ORD patterns
    m = ORD_PAT.search(text)
    if m:
        return _normalize_order_id(m.group(0))
    # Fallback: 5+ digits
    m = DIGITS_PAT.search(text)
    if m:
        return _normalize_order_id(m.group(0))
    return None


class ValidateOrderStatusForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_order_status_form"

    def validate_order_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        # 1) Collect candidates from (a) slot_value (b) extracted entities (c) raw text
        candidates: List[str] = []

        if slot_value is not None:
            if isinstance(slot_value, list):
                candidates += [str(x) for x in slot_value if x is not None]
            else:
                candidates.append(str(slot_value))

        for e in tracker.latest_message.get("entities", []):
            if e.get("entity") == "order_id" and e.get("value"):
                candidates.append(str(e["value"]))

        text = tracker.latest_message.get("text", "")
        extracted = _extract_order_id_from_text(text)
        if extracted:
            candidates.append(extracted)

        # dedupe + normalize
        normalized = []
        seen = set()
        for c in candidates:
            n = _normalize_order_id(c) or _extract_order_id_from_text(c)
            if n and n not in seen:
                normalized.append(n)
                seen.add(n)

        # 2) Handle no candidate
        if not normalized:
            dispatcher.utter_message(
                text="I couldn't find an Order ID. Please type something like ORD-12345 (or just the 5+ digits)."
            )
            return {"order_id": None}

        # 3) Handle multiple: ask user to confirm ONE instead of dead-looping
        if len(normalized) > 1:
            dispatcher.utter_message(
                text=f"I found multiple possible Order IDs: {', '.join(normalized)}. Please tell me which one to use."
            )
            return {"order_id": None}

        # 4) Accept the single normalized value (NO DB existence check here)
        return {"order_id": normalized[0]}


# =========================================================
# Action Layer
# =========================================================
class ActionCheckOrderStatus(Action):
    def name(self) -> Text:
        return "action_check_order_status"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(text="No order ID provided.")
            return []

        order = db_service.get_order_status(order_id)
        if order:
            dispatcher.utter_message(
                text=(
                    f"Order {order_id} is currently {order['status']}. "
                    f"Expected delivery date: {order['delivery_date']}."
                )
            )
        else:
            dispatcher.utter_message(text="Unable to retrieve order details.")

        return [SlotSet("order_id", None)]


class ActionCreateSupportRequest(Action):
    def name(self) -> Text:
        return "action_create_support_request"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        issue_description = tracker.latest_message.get("text", "")
        ticket_id = db_service.create_support_ticket(issue_description)

        dispatcher.utter_message(response="utter_ticket_ack")
        dispatcher.utter_message(response="utter_ticket_created")
        # Optional: expose ticket ID
        # dispatcher.utter_message(text=f"Your ticket ID is {ticket_id}")

        return []


class ActionHandover(Action):
    def name(self) -> Text:
        return "action_handover"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_handover_ack")
        return []


class ActionSearchFaq(Action):
    def name(self) -> Text:
        return "action_search_faq"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        query = tracker.get_slot("search_term")
        if not query:
            dispatcher.utter_message(text="Please provide a keyword to search the FAQ.")
            return []

        # Load knowledge base
        kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
        knowledge_base = []

        if os.path.exists(kb_path):
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    knowledge_base = json.load(f)
            except Exception:
                knowledge_base = []

        if not knowledge_base:
            knowledge_base = [
                {
                    "question": "What is your return policy?",
                    "answer": "You can return items within 30 days in original condition.",
                },
                {
                    "question": "How do I track my order?",
                    "answer": "Tracking information will be sent once your order is shipped.",
                },
            ]

        questions = [item["question"] for item in knowledge_base]

        best_answer = None
        match = process.extractOne(query, questions, scorer=fuzz.token_set_ratio)
        if match and match[1] >= 50:
            best_answer = knowledge_base[match[2]]["answer"]

        if best_answer:
            dispatcher.utter_message(text=best_answer)
        else:
            dispatcher.utter_message(
                text="I couldn't find a relevant answer in the FAQ."
            )

        return [SlotSet("search_term", None)]


class ActionSearchChatHistory(Action):
    def name(self) -> Text:
        return "action_search_chat_history"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        keyword = tracker.get_slot("search_term")
        if not keyword:
            dispatcher.utter_message(text="Please provide a keyword to search.")
            return []

        results = db_service.search_chat_history(keyword)

        if results:
            lines = []
            for entry in results[:5]:
                speaker = "You" if entry["sender"] == "user" else "Bot"
                lines.append(f"- {speaker}: {entry['message']}")
            dispatcher.utter_message(
                text=f"Here are the messages I found:\n" + "\n".join(lines)
            )
        else:
            dispatcher.utter_message(
                text=f"No chat history found containing '{keyword}'."
            )

        return [SlotSet("search_term", None)]


class ActionRestart(Action):
    def name(self) -> Text:
        return "action_restart"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_restart_ack")
        return [Restarted()]

# =========================================================
# Core Fallback Action (RulePolicy)
# =========================================================
class ActionDefaultFallback(Action):
    """Default fallback action used by Core (RulePolicy).

    This action must exist because `config.yml` sets:
        RulePolicy.core_fallback_action_name: "action_default_fallback"

    It responds with the standard fallback utterance and then shows quick replies
    to help users recover.
    """

    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_fallback")
        dispatcher.utter_message(response="utter_show_quick_replies")
        return []