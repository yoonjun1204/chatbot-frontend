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


# =========================================================
# Validation Layer: Order Status Form Validation (Security)
# =========================================================
class ValidateOrderStatusForm(FormValidationAction):
    """
    Multi-layer validation for order_id slot.
    Implements defense-in-depth:
    1. Regex format validation
    2. Entity ambiguity detection
    3. Database existence check
    """

    def name(self) -> Text:
        return "validate_order_status_form" # domain.yml looking for

    def validate_order_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if slot_value is None:
            return {"order_id": None}

        # Normalize input
        order_id = str(slot_value).strip().upper()

        # ---------------------------
        # Defense Line 1: Regex check
        # ---------------------------
        pattern = r"^ORD-\d{5}$"
        if not re.match(pattern, order_id):
            dispatcher.utter_message(
                text="The order ID format is invalid. Please use the format ORD-12345."
            )
            return {"order_id": None}

        # --------------------------------
        # Defense Line 2: Ambiguity check
        # --------------------------------
        entities = [
            e
            for e in tracker.latest_message.get("entities", [])
            if e.get("entity") == "order_id"
        ]

        if len(entities) > 1:
            ids_found = [e.get("value") for e in entities]
            dispatcher.utter_message(
                text=f"I detected multiple order IDs ({', '.join(ids_found)}). Please specify one."
            )
            return {"order_id": None}

        # ------------------------------------
        # Defense Line 3: Existence check (DB)
        # ------------------------------------
        if db_service.get_order_status(order_id) is None:
            dispatcher.utter_message(
                text=f"No order found with ID {order_id}. Please double-check."
            )
            return {"order_id": None}

        return {"order_id": order_id}


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