import re
import json
import os
import requests
from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted, UserUtteranceReverted, FollowupAction
from rasa_sdk.types import DomainDict
import os
import google.generativeai as genai

# Third-party library for fuzzy string matching
from rapidfuzz import process, fuzz

# SQLAlchemy for Database Connection (Raw SQL mode)
from sqlalchemy import create_engine, text


# =========================================================
# Service Layer: Real Database Service (Raw SQL)
# =========================================================
class DatabaseService:
    """
    Service layer that connects to the real Neon Tech PostgreSQL database.
    Uses Raw SQL to avoid duplicating model definitions.
    """

    def __init__(self):
        # Read the DATABASE_URL from the Docker environment variables
        self.db_url = os.environ.get("DATABASE_URL")
        self.engine = None

        if not self.db_url:
            print("WARNING: DATABASE_URL not found. DB calls will fail.")
        else:
            try:
                # Neon requires SSL, usually handled by the URL params or default in sqlalchemy
                self.engine = create_engine(self.db_url)
                print("INFO: Database connection configured successfully.")
            except Exception as e:
                print(f"ERROR: Failed to configure database engine: {e}")

    def get_order_status(self, order_id: Text) -> Optional[Dict[Text, Any]]:
        """
        Retrieve order status from the REAL 'orders' table using SQL.
        """
        if not self.engine:
            print("ERROR: No DB engine available.")
            return None

        try:
            # We use a context manager to open/close the connection automatically
            with self.engine.connect() as connection:
                # SQL Query using the columns you provided
                # We use :order_id for safe parameter binding (prevents SQL injection)
                query = text(
                    """
                    SELECT status, estimated_delivery 
                    FROM orders 
                    WHERE order_number = :order_id
                """
                )

                result = (
                    connection.execute(query, {"order_id": order_id}).mappings().first()
                )

                if result:
                    return {
                        "status": result["status"],
                        # Convert date object to string if it exists
                        "delivery_date": (
                            str(result["estimated_delivery"])
                            if result["estimated_delivery"]
                            else "Unknown"
                        ),
                    }
                return None

        except Exception as e:
            print(f"ERROR: DB Query failed: {e}")
            return None

    def create_support_ticket(self, issue_description: Text) -> Text:
        """
        STUB: Simulate creating a support ticket.
        """
        # Placeholder ID
        return "TICKET-NEW"

    def search_products(self, keyword: Text = None) -> List[Dict[Text, Any]]:
        """
        Real SQL query to find products in Neon DB.
        """
        if not self.engine:
            return []

        try:
            with self.engine.connect() as connection:
                # If keyword is provided, search name/desc. If not, get everything.
                if keyword:
                    # ILIKE is case-insensitive search in PostgreSQL
                    query = text(
                        """
                        SELECT name, price, description, color 
                        FROM products 
                        WHERE stock_quantity > 0 
                        AND (name ILIKE :kw OR description ILIKE :kw OR color ILIKE :kw)
                        LIMIT 5
                    """
                    )
                    result = (
                        connection.execute(query, {"kw": f"%{keyword}%"})
                        .mappings()
                        .all()
                    )
                else:
                    query = text(
                        "SELECT name, price, description, color FROM products WHERE stock_quantity > 0 LIMIT 5"
                    )
                    result = connection.execute(query).mappings().all()

                # Convert to simple list of dicts
                return [dict(row) for row in result]

        except Exception as e:
            print(f"DB Product Search failed: {e}")
            return []


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

        # 4) Accept the single normalized value
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

        # Call the REAL database service
        order = db_service.get_order_status(order_id)

        if order:
            dispatcher.utter_message(
                text=(
                    f"Order {order_id} is currently {order['status']}. "
                    f"Expected delivery date: {order['delivery_date']}."
                )
            )
        else:
            dispatcher.utter_message(
                text=f"I searched our database but couldn't find order {order_id}. Please double check the number."
            )

        # RESET THE SLOT TO STOP LOOPS
        return [SlotSet("order_id", None)]


class ActionCreateSupportRequest(Action):
    def name(self) -> Text:
        return "action_create_support_request"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        issue_description = tracker.latest_message.get("text", "")
        db_service.create_support_ticket(issue_description)

        dispatcher.utter_message(response="utter_ticket_ack")
        dispatcher.utter_message(response="utter_ticket_created")
        return []


class ActionHandover(Action):
    def name(self) -> Text:
        return "action_handover"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        # 1. Get the conversation ID (Rasa stores this as sender_id)
        conversation_id = tracker.sender_id

        # 2. Update DB status to 'waiting_for_agent'
        # Since we are using Raw SQL in db_service, add a method there or execute directly
        try:
            with db_service.engine.connect() as connection:
                query = text(
                    "UPDATE conversations SET status = 'waiting_for_agent' WHERE id = :cid"
                )
                connection.execute(query, {"cid": conversation_id})
                connection.commit()  # Important for some DB drivers
        except Exception as e:
            print(f"DB Update failed: {e}")

        dispatcher.utter_message(
            text="Okay, I am connecting you to a human agent now. Please hold on."
        )
        return []


class ActionSearchFaq(Action):
    def name(self) -> Text:
        return "action_search_faq"

    def run(self, dispatcher, tracker, domain):
        query = tracker.get_slot("search_term")
        # If no slot, try the last message text
        if not query:
            query = tracker.latest_message.get("text")

        # Load KB
        kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)
        except:
            # Emergency Fallback
            knowledge_base = [
                {"question": "Returns", "answer": "30 days return policy."}
            ]

        # 1. FUZZY MATCHING
        # We extract the best match from the list of questions
        questions = [item["question"] for item in knowledge_base]
        match = process.extractOne(query, questions, scorer=fuzz.token_set_ratio)

        # match is a tuple: (matched_string, score, index)
        # e.g., ("How do I return?", 85, 0)

        if match:
            score = match[1]
            best_entry = knowledge_base[match[2]]

            # SCENARIO A: Perfect Match (Score > 80)
            # Just give the pre-written answer. It's fast and accurate.
            if score > 80:
                dispatcher.utter_message(text=f"FAQ: {best_entry['answer']}")
                return [SlotSet("search_term", None)]

            # SCENARIO B: Okay Match (Score > 50)
            # Use LLM to make it sound natural contextually
            elif score > 50:
                system_prompt = f"""
                You are a helpful support agent.
                The user asked: "{query}"
                We found this relevant policy in our FAQ: "{best_entry['answer']}"
                
                INSTRUCTION: Rephrase the policy to directly answer the user's specific question naturally. Keep it short.
                """
                response = get_llm_response(system_prompt, query)
                dispatcher.utter_message(text=response)
                return [SlotSet("search_term", None)]

        # SCENARIO C: No Match (Score < 50)
        # The user asked something not in our FAQ file.
        # Let's ask the LLM to try and answer based on "General Retail Knowledge" or apologize.

        system_prompt = f"""
        You are a helpful support agent for a shirt store.
        The user asked: "{query}"
        We could not find a specific policy in our FAQ database.
        
        INSTRUCTION: 
        1. If this is a general question (e.g. "What is cotton?"), answer it briefly.
        2. If it requires specific store policy (e.g. "What is your CEO's phone number?"), apologize and say you don't have that info.
        """
        response = get_llm_response(system_prompt, query)
        dispatcher.utter_message(text=response)

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


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_default_feedback")
        return []


class ActionSmartFallback(Action):
    def name(self) -> Text:
        return "action_smart_fallback"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")

        if order_id:
            # Found ID? Go check it!
            return [FollowupAction("action_check_order_status")]

        # No ID? Fallback as usual.
        dispatcher.utter_message(response="utter_default_feedback")
        return [UserUtteranceReverted()]


# =========================================================
# HYBRID INTELLIGENCE LAYER (LLM + Logic)
# =========================================================
def get_llm_response(system_prompt, user_message):
    """
    Direct API call to Google Gemini (Stable Flash Version)
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "DEBUG ERROR: API Key is missing."

        # USE THE STABLE ALIAS (This fixes the Limit: 0 error)
        model_name = "gemini-flash-latest"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"parts": [{"text": f"SYSTEM: {system_prompt}\nUSER: {user_message}"}]}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        elif response.status_code == 429:
            return "Note: The AI is busy (Rate Limit Reached). Please try again in 30 seconds."
        else:
            return f"GOOGLE ERROR: {response.status_code} - {response.text}"

    except Exception as e:
        return f"SYSTEM ERROR: {str(e)}"


class ActionSalesBrain(Action):
    def name(self) -> Text:
        return "action_sales_brain"

    def run(self, dispatcher, tracker, domain):
        user_msg = tracker.latest_message.get("text")

        # --- 1. GET HISTORY (Context) ---
        # Grab recent conversation so the LLM knows if you rejected a previous item
        events = tracker.events_after_latest_restart()
        chat_history = ""
        for e in events:
            if e["event"] == "user":
                chat_history += f"User: {e.get('text')}\n"
            elif e["event"] == "bot":
                chat_history += f"Bot: {e.get('text')}\n"

        # Keep only the last ~500 characters to save tokens
        chat_history = chat_history[-500:]

        # --- 2. SEARCH DATABASE (Smart Keyword Logic) ---
        # A. Try searching the full sentence first
        products = db_service.search_products(keyword=user_msg)

        # B. If no results, split sentence into keywords and search individually
        # This fixes the "I need something for the gym" issue
        if not products:
            ignore_words = [
                "need",
                "want",
                "have",
                "show",
                "looking",
                "something",
                "shirt",
                "wear",
                "with",
                "for",
                "the",
                "can",
                "you",
                "please",
            ]
            # Find meaningful words longer than 3 chars
            keywords = [
                w
                for w in user_msg.split()
                if len(w) > 3 and w.lower() not in ignore_words
            ]

            for word in keywords:
                found = db_service.search_products(keyword=word)
                if found:
                    products.extend(found)

            # Remove duplicates (in case 'winter' and 'jacket' find the same item)
            # We use a dictionary keyed by product name to filter duplicates
            products = list({p["name"]: p for p in products}.values())

        # C. Fallback: If STILL nothing, fetch generic best-sellers
        if not products:
            products = db_service.search_products(keyword=None)

        # Format for LLM
        inventory_context = ""
        if products:
            for p in products:
                inventory_context += (
                    f"- {p['name']} (${p['price']}): {p['color']}, {p['description']}\n"
                )
        else:
            inventory_context = "No stock currently available."

        # --- 3. PROMPT ENGINEERING ---
        system_prompt = f"""
        You are 'Stitch', a helpful fashion assistant.
        
        REAL-TIME INVENTORY:
        {inventory_context}
        
        CONVERSATION HISTORY (Use this for context, e.g., if user says 'I hate that'):
        {chat_history}
        
        INSTRUCTIONS:
        1. Recommend a product from the Inventory based on the User's LAST message and the Context.
        2. If the user rejected a previous suggestion, find a different alternative from the Inventory.
        3. Do NOT repeat greetings ("Hi there") if they are already in the history.
        4. Keep it conversational and under 3 sentences.
        """

        # 4. CALL LLM
        bot_reply = get_llm_response(system_prompt, user_msg)

        dispatcher.utter_message(text=bot_reply)
        return []


class ActionLLMFallback(Action):
    def name(self) -> Text:
        return "action_llm_fallback"

    def run(self, dispatcher, tracker, domain):
        user_msg = tracker.latest_message.get("text")

        # --- LAYER 1: CHECK FAQ JSON FIRST (The "Hard" Facts) ---
        kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)

            # Fuzzy match the user's message against FAQ questions
            questions = [item["question"] for item in knowledge_base]
            match = process.extractOne(user_msg, questions, scorer=fuzz.token_set_ratio)

            # If match score is high (> 75), it's definitely a policy question
            if match and match[1] >= 75:
                best_entry = knowledge_base[match[2]]
                # Optional: Use Gemini to rephrase it nicely so it doesn't sound robotic
                prompt = f"User asked: '{user_msg}'. Our policy is: '{best_entry['answer']}'. Answer the user naturally."
                response = get_llm_response(prompt, user_msg)
                dispatcher.utter_message(text=response)
                return [UserUtteranceReverted()]
        except Exception as e:
            print(f"FAQ Check failed: {e}")

        # --- LAYER 2: IF NO FAQ FOUND, ASK GEMINI (General Intelligence) ---
        # Get Context
        events = tracker.events_after_latest_restart()
        chat_history = ""
        for e in events:
            if e["event"] == "user":
                chat_history += f"User: {e.get('text')}\n"
            elif e["event"] == "bot":
                chat_history += f"Bot: {e.get('text')}\n"
        chat_history = chat_history[-500:]

        system_prompt = f"""
        You are 'Stitch', a helpful AI for Shirtify.
        
        CONTEXT:
        The user said something we didn't have a specific rule for.
        
        CHAT HISTORY:
        {chat_history}
        
        INSTRUCTIONS:
        1. If it's small talk ("Hi", "Thanks"), be polite.
        2. If it's a complex question about shirts/fashion, answer as best as you can.
        3. If you don't know, apologize and suggest asking about "Products", "Orders", or "Returns".
        """

        bot_reply = get_llm_response(system_prompt, user_msg)
        dispatcher.utter_message(text=bot_reply)

        return [UserUtteranceReverted()]
