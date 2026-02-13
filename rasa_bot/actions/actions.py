# rasa_bot/actions/actions.py
import re
import json
import os
import requests
from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    Restarted,
    UserUtteranceReverted,
    FollowupAction,
    ActiveLoop,
)
from rasa_sdk.types import DomainDict
import google.generativeai as genai

# Third-party library for fuzzy string matching
from rapidfuzz import process, fuzz

# SQLAlchemy for Database Connection (Raw SQL mode)
from sqlalchemy import create_engine, text


# =========================================================
# Service Layer: Real Database Service (Raw SQL)
# =========================================================
class DatabaseService:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        self.engine = None
        if not self.db_url:
            print("WARNING: DATABASE_URL not found. DB calls will fail.")
        else:
            try:
                self.engine = create_engine(self.db_url)
                print("INFO: Database connection configured successfully.")
            except Exception as e:
                print(f"ERROR: Failed to configure database engine: {e}")

    def get_order_status(self, order_id: Text) -> Optional[Dict[Text, Any]]:
        if not self.engine:
            return None
        try:
            with self.engine.connect() as connection:
                query = text(
                    """
                    SELECT status, estimated_delivery, product_name, quantity, total_price
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
                        "delivery_date": (
                            str(result["estimated_delivery"])
                            if result["estimated_delivery"]
                            else "Unknown"
                        ),
                        "product": result["product_name"],
                        "quantity": result["quantity"],
                        "price": result["total_price"],
                    }
                return None
        except Exception as e:
            print(f"ERROR: DB Query failed: {e}")
            return None

    def create_support_ticket(self, issue_description: Text) -> Text:
        return "TICKET-NEW"

    def search_products(self, keyword: Text = None) -> List[Dict[Text, Any]]:
        if not self.engine:
            return []
        try:
            with self.engine.connect() as connection:
                if keyword:
                    query = text(
                        """
                        SELECT name, price, description, color, size, type 
                        FROM products 
                        WHERE stock_quantity > 0 
                        AND (name ILIKE :kw OR description ILIKE :kw OR color ILIKE :kw OR type ILIKE :kw)
                        LIMIT 5
                        """
                    )
                    # Note: I added 'OR type ILIKE :kw' so searching "Formal" works now!
                    result = (
                        connection.execute(query, {"kw": f"%{keyword}%"})
                        .mappings()
                        .all()
                    )
                else:
                    query = text(
                        "SELECT name, price, description, color, size, type FROM products WHERE stock_quantity > 0 LIMIT 5"
                    )
                    result = connection.execute(query).mappings().all()
                return [dict(row) for row in result]
        except Exception as e:
            print(f"DB Product Search failed: {e}")
            return []


db_service = DatabaseService()
ORD_PAT = re.compile(r"\bORD[-\s]?\d{3,}\b", re.IGNORECASE)
DIGITS_PAT = re.compile(r"\b\d{5,}\b")


# ... (Helper functions _normalize_order_id and _extract_order_id_from_text remain the same) ...
def _normalize_order_id(raw: str) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip().upper().replace("_", "-").replace(" ", "")
    m = re.match(r"^(ORD)(\d{3,})$", s)
    if m:
        return f"ORD-{m.group(2)}"
    m = re.match(r"^(ORD)-(\d{3,})$", s)
    if m:
        return s
    if re.match(r"^\d{5,}$", s):
        return f"ORD-{s}"
    return None


def _extract_order_id_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    m = ORD_PAT.search(text)
    if m:
        return _normalize_order_id(m.group(0))
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
        candidates: List[str] = []
        if slot_value:
            candidates += [
                str(x)
                for x in (slot_value if isinstance(slot_value, list) else [slot_value])
                if x
            ]
        for e in tracker.latest_message.get("entities", []):
            if e.get("entity") == "order_id" and e.get("value"):
                candidates.append(str(e["value"]))
        extracted = _extract_order_id_from_text(tracker.latest_message.get("text", ""))
        if extracted:
            candidates.append(extracted)

        normalized = []
        seen = set()
        for c in candidates:
            n = _normalize_order_id(c) or _extract_order_id_from_text(c)
            if n and n not in seen:
                normalized.append(n)
                seen.add(n)

        if not normalized:
            # Only complain if the user INTENDED to give an ID.
            # If they asked a question (interruption), the rule handles it, so we can pass None here gracefully.
            return {"order_id": None}

        if len(normalized) > 1:
            dispatcher.utter_message(
                text=f"I found multiple IDs: {', '.join(normalized)}. Which one?"
            )
            return {"order_id": None}

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
            # UPDATED: Now prints Product, Quantity, and Price!
            dispatcher.utter_message(
                text=(
                    f"Order {order_id} is currently **{order['status']}**.\n"
                    f"📦 Item: {order['product']} (x{order['quantity']})\n"
                    f"💰 Total: ${order['price']:.2f}\n"
                    f"📅 Expected Delivery: {order['delivery_date']}"
                )
            )
        else:
            dispatcher.utter_message(
                text=f"I searched our database but couldn't find order {order_id}. Please double check the number."
            )

        return [SlotSet("order_id", None)]


class ActionSearchFaq(Action):
    def name(self) -> Text:
        return "action_search_faq"

    def run(self, dispatcher, tracker, domain):
        # --- FIX: ALWAYS USE FULL SENTENCE FOR SEARCH ---
        # Don't trust the extracted slot alone, it might miss context like "Silk"
        query = tracker.latest_message.get("text")

        if not query:
            # Fallback to slot if text is somehow empty
            query = tracker.get_slot("search_term")

        if not query:
            dispatcher.utter_message(
                text="I'm sorry, I missed what you were asking about."
            )
            return []

        query_lower = query.lower()
        print(f"\nDEBUG: Handling FAQ Search for: '{query_lower}'")

        kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)
        except:
            knowledge_base = []

        best_entry = None
        max_hits = 0

        # --- STEP 1: SMARTER KEYWORD SEARCH ---
        for entry in knowledge_base:
            keywords = entry.get("keywords", [])
            # Count matches
            hits = sum(1 for k in keywords if k in query_lower)

            # Print logic to see what's winning
            if hits > 0:
                print(
                    f"DEBUG: Checking '{entry['question']}' - Found {hits} keyword matches."
                )

            # Update winner if this entry has MORE matches than the previous best
            if hits > max_hits:
                max_hits = hits
                best_entry = entry

        print(
            f"DEBUG: Winner is '{best_entry['question'] if best_entry else 'None'}' with {max_hits} hits.\n"
        )

        # --- STEP 2: FUZZY MATCHING (Fallback) ---
        # Only use fuzzy if we found ZERO keyword matches
        fuzzy_score = 0
        if max_hits == 0:
            questions = [item["question"] for item in knowledge_base]
            match = process.extractOne(query, questions, scorer=fuzz.token_set_ratio)
            if match:
                fuzzy_score = match[1]
                # Only overwrite if fuzzy score is decent
                if fuzzy_score > 60:
                    best_entry = knowledge_base[match[2]]
                    print(
                        f"DEBUG: Fallback to Fuzzy Match: {best_entry['question']} (Score: {fuzzy_score})"
                    )

        # --- STEP 3: GENERATE RESPONSE ---
        if best_entry:
            if max_hits > 0 or fuzzy_score > 80:
                dispatcher.utter_message(text=f"FAQ: {best_entry['answer']}")
                return [SlotSet("search_term", None)]

            elif fuzzy_score > 50:
                system_prompt = f"User asked: '{query}'. Policy: '{best_entry['answer']}'. Rephrase to answer naturally."
                response = get_llm_response(system_prompt, query)
                dispatcher.utter_message(text=response)
                return [SlotSet("search_term", None)]

        # SCENARIO C: No Match
        system_prompt = f"You are a support agent. User asked: '{query}'. Answer generally or apologize."
        response = get_llm_response(system_prompt, query)
        dispatcher.utter_message(text=response)
        return [SlotSet("search_term", None)]


class ActionCreateSupportRequest(Action):
    def name(self) -> Text:
        return "action_create_support_request"

    def run(self, dispatcher, tracker, domain):
        db_service.create_support_ticket(tracker.latest_message.get("text", ""))
        dispatcher.utter_message(response="utter_ticket_ack")
        dispatcher.utter_message(response="utter_ticket_created")
        return []


class ActionHandover(Action):
    def name(self) -> Text:
        return "action_handover"

    def run(self, dispatcher, tracker, domain):
        try:
            with db_service.engine.connect() as connection:
                connection.execute(
                    text(
                        "UPDATE conversations SET status = 'waiting_for_agent' WHERE id = :cid"
                    ),
                    {"cid": tracker.sender_id},
                )
                connection.commit()
        except:
            pass
        dispatcher.utter_message(text="Connecting you to a human agent...")
        return []


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(response="utter_default_feedback")
        return []


class ActionSmartFallback(Action):
    def name(self) -> Text:
        return "action_smart_fallback"

    def run(self, dispatcher, tracker, domain):
        if tracker.get_slot("order_id"):
            return [FollowupAction("action_check_order_status")]
        dispatcher.utter_message(response="utter_default_feedback")
        return [UserUtteranceReverted()]


def get_llm_response(system_prompt, user_message):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "DEBUG ERROR: API Key is missing."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": f"SYSTEM: {system_prompt}\nUSER: {user_message}"}
                        ]
                    }
                ]
            },
        )
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return "The AI is currently busy. Please try again."
    except Exception as e:
        return f"SYSTEM ERROR: {str(e)}"


class ActionSalesBrain(Action):
    def name(self) -> Text:
        return "action_sales_brain"

    def run(self, dispatcher, tracker, domain):
        user_msg = tracker.latest_message.get("text")

        # --- 1. GET CONTEXT ---
        events = tracker.events_after_latest_restart()
        chat_history = ""
        for e in events:
            if e["event"] == "user":
                chat_history += f"User: {e.get('text')}\n"
            elif e["event"] == "bot":
                chat_history += f"Bot: {e.get('text')}\n"
        chat_history = chat_history[-600:]

        # --- 2. SMART INVENTORY SEARCH ---
        # Fetch products (including Size and Type columns if available)
        products = db_service.search_products(keyword=user_msg)

        if not products:
            # Broaden search: ignore filler words, check 3+ letter words
            ignore_words = {
                "the",
                "and",
                "for",
                "with",
                "can",
                "you",
                "have",
                "show",
                "me",
                "option",
                "choice",
                "stock",
                "available",
                "want",
                "need",
            }
            keywords = [
                w
                for w in user_msg.split()
                if len(w) >= 3 and w.lower() not in ignore_words
            ]

            for word in keywords:
                found = db_service.search_products(keyword=word)
                if found:
                    products.extend(found)

            # Deduplicate by name
            products = list({p["name"]: p for p in products}.values())

        # Fallback: Best Sellers if nothing found
        if not products:
            products = db_service.search_products(keyword=None)

        # --- 3. FORMAT DATA FOR AI ---
        # We explicitly label every field so the AI understands Size and Type
        if products:
            inv_text = "\n".join(
                [
                    f"- {p['name']} (${p['price']}) | Type: {p.get('type', 'N/A')} | Sizes: {p.get('size', 'N/A')} | Color: {p['color']} | Desc: {p['description']}"
                    for p in products
                ]
            )
        else:
            inv_text = "No stock found."

        # --- 4. THE HYBRID LOGIC PROMPT ---
        system_prompt = f"""
        You are 'Stitch', a helpful shirt store assistant.
        
        CURRENT INVENTORY (Real Database Data):
        {inv_text}
        
        CONVERSATION HISTORY:
        {chat_history}
        
        YOUR GOAL:
        Recommend the best item from the INVENTORY based on the user's constraints.
        
        LOGIC GUIDELINES:
        1. **Analyze Constraints:** Identify what the user wants.
           - **Specifics:** Color ("Red"), Size ("XXL"), Type ("Formal"), Material ("Cotton").
           - **Vibe:** "Wedding" (Formal), "Gym" (Activewear), "Beach" (Casual/Linen).
           - **Relative:** "Cheaper", "Darker", "Something else" (Compare to History).

        2. **Compare & Filter:**
           - **Size Check:** IF user asks for a size (e.g. "Small"), CHECK the 'Sizes' field. If missing, say "Stitch is sorry, no Small!"
           - **Prices:** If user asks for "Cheaper", look at the LAST price in history and pick a lower one.
           - **Color/Type:** Match user's request to the 'Color' or 'Type' fields.

        3. **Honesty Protocol:**
           - You can ONLY sell items from the INVENTORY list above.
           - If the exact request is NOT in the list (e.g. "Pink Hoodie" not found), say: "Stitch doesn't have [Request], but this [Alternative] is great!"
           - **NEVER** give general advice without a product recommendation.

        4. **Persona:** Energetic Stitch style, max 2 sentences. Format: **Product Name ($Price)**.
        """

        bot_reply = get_llm_response(system_prompt, user_msg)

        # --- 5. SAVE CONTEXT ---
        # Check if the bot mentioned a specific product, and save it to a slot.
        mentioned_product = None
        for p in products:
            if p["name"] in bot_reply:
                mentioned_product = p["name"]
                break

        dispatcher.utter_message(text=bot_reply)

        if mentioned_product:
            return [SlotSet("current_product_context", mentioned_product)]

        return []


class ActionLLMFallback(Action):
    def name(self) -> Text:
        return "action_llm_fallback"

    def run(self, dispatcher, tracker, domain):
        user_msg = tracker.latest_message.get("text")
        query_lower = user_msg.lower()

        # --- LAYER 1: CHECK FAQ JSON (Smart Match) ---
        kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)

            # 1. Keyword Count
            best_entry = None
            max_hits = 0
            for entry in knowledge_base:
                hits = sum(1 for k in entry.get("keywords", []) if k in query_lower)
                if hits > max_hits:
                    max_hits = hits
                    best_entry = entry

            if max_hits > 0:
                prompt = f"User asked: '{user_msg}'. Policy: '{best_entry['answer']}'. Answer briefly (1 sentence)."
                dispatcher.utter_message(text=get_llm_response(prompt, user_msg))
                return [UserUtteranceReverted()]

            # 2. Fuzzy Match
            questions = [item["question"] for item in knowledge_base]
            match = process.extractOne(user_msg, questions, scorer=fuzz.token_set_ratio)

            if match and match[1] >= 75:
                best_entry = knowledge_base[match[2]]
                prompt = f"User asked: '{user_msg}'. Policy: '{best_entry['answer']}'. Answer briefly (1 sentence)."
                dispatcher.utter_message(text=get_llm_response(prompt, user_msg))
                return [UserUtteranceReverted()]
        except:
            pass

        # --- LAYER 2: GENERAL INTELLIGENCE ---
        events = tracker.events_after_latest_restart()
        chat_history = ""
        for e in events[-6:]:
            if e["event"] == "user":
                chat_history += f"User: {e.get('text')}\n"
            elif e["event"] == "bot":
                chat_history += f"Bot: {e.get('text')}\n"

        # Check for Smart Context (Did we just talk about a shirt?)
        product_context = tracker.get_slot("current_product_context")
        context_str = (
            f"User is looking at: {product_context}" if product_context else ""
        )

        system_prompt = f"""
        You are Stitch, a helpful shirt store assistant.
        The user said something that didn't match our standard buttons.
        
        CONTEXT: {context_str}
        HISTORY: {chat_history}
        
        INSTRUCTIONS:
        1. **Context Check:** Is the user asking about the product mentioned in CONTEXT? (e.g. "Is it cotton?")
        2. **Helpful Answer:** Answer briefly based on general knowledge.
        3. **Redirect:** If off-topic, politely steer back to **Products**.
        4. **Brevity:** Keep it under 2 sentences.
        """

        bot_reply = get_llm_response(system_prompt, user_msg)
        dispatcher.utter_message(text=bot_reply)

        return [UserUtteranceReverted()]
