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

    def get_order_status(
        self, order_id: Text, user_email: Text
    ) -> Optional[Dict[Text, Any]]:
        if not self.engine:
            return {"error": "db_error"}
        try:
            with self.engine.connect() as connection:
                # Security Fix: JOIN users table to verify ownership!
                query = text(
                    """
                    SELECT o.status, o.estimated_delivery, o.product_name, o.quantity, o.total_price
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    WHERE o.order_number = :order_id AND u.email = :user_email
                    """
                )
                result = (
                    connection.execute(
                        query, {"order_id": order_id, "user_email": user_email}
                    )
                    .mappings()
                    .first()
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
                # Returns None if order doesn't exist OR belongs to another email
                return None
        except Exception as e:
            print(f"ERROR: DB Query failed: {e}")
            return {"error": "db_error"}

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

        raw_order_id = tracker.get_slot("order_id")

        # 🛑 BULLETPROOF FIX: Normalize the ID right here just in case the form is bypassed
        order_id = _normalize_order_id(raw_order_id) or raw_order_id

        # EXTRACT USER EMAIL
        metadata = tracker.latest_message.get("metadata", {})
        user_email = metadata.get("user_id") or metadata.get("email")

        # Fallback for local shell testing
        if not user_email or user_email == "anonymous":
            user_email = "boblim@example.com"

        if not order_id:
            dispatcher.utter_message(text="No order ID provided.")
            return []

        # Pass the normalized ID and email to the DB service
        order = db_service.get_order_status(order_id, user_email)

        if order and "error" not in order:
            dispatcher.utter_message(
                text=(
                    f"Order {order_id} is currently **{order['status']}**.\n"
                    f"📦 Item: {order['product']} (x{order['quantity']})\n"
                    f"💰 Total: ${order['price']:.2f}\n"
                    f"📅 Expected Delivery: {order['delivery_date']}"
                )
            )
        elif order and "error" in order:
            dispatcher.utter_message(
                text="I'm having trouble connecting to the database right now."
            )
        else:
            dispatcher.utter_message(
                text=f"I searched our database but couldn't find order {order_id} under your account ({user_email}). Please double check the number."
            )

        # Do not clear the slot. Return empty list!
        return []


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
        print(f"\nDEBUG: Handling FAQ Search for: '{query_lower}'", flush=True)

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
                    f"DEBUG: Checking '{entry['question']}' - Found {hits} keyword matches.",
                    flush=True,
                )

            # Update winner if this entry has MORE matches than the previous best
            if hits > max_hits:
                max_hits = hits
                best_entry = entry

        print(
            f"DEBUG: Winner is '{best_entry['question'] if best_entry else 'None'}' with {max_hits} hits.\n",
            flush=True,
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
                        f"DEBUG: Fallback to Fuzzy Match: {best_entry['question']} (Score: {fuzzy_score})",
                        flush=True,
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

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")

        if order_id:
            # 🛑 THE FIX: Do not use FollowupAction here!
            # Directly execute the checking action right now to keep the HTTP connection open.
            check_action = ActionCheckOrderStatus()
            return check_action.run(dispatcher, tracker, domain)

        # Logic: No ID found, so this is a genuine failure.
        dispatcher.utter_message(response="utter_default_feedback")
        dispatcher.utter_message(response="utter_show_quick_replies")

        # UserUtteranceReverted tells Rasa: "Pretend the user didn't say that last gibberish."
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
        print(f"\nDEBUG: User said: '{user_msg}'", flush=True)  # <--- DEBUG

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

        # A. Try Strict Search First
        products = db_service.search_products(keyword=user_msg)
        if products:
            print(f"DEBUG: Strict search found {len(products)} items.", flush=True)

        # B. IF STRICT FAILS, TRY FUZZY CORRECTION
        if not products:
            print(
                "DEBUG: Strict search failed. Attempting Fuzzy Correction...",
                flush=True,
            )

            # 1. Gather tokens from DB
            correction_candidates = []
            if db_service.engine:
                try:
                    with db_service.engine.connect() as conn:
                        rows = conn.execute(
                            text("SELECT name, color, type FROM products")
                        ).fetchall()
                        for r in rows:
                            # Add Color and Type
                            if r[1]:
                                correction_candidates.append(str(r[1]))  # Color
                            if r[2]:
                                correction_candidates.append(str(r[2]))  # Type

                            # Add Name Tokens (Split "Cloud-Soft Hoodie" -> "Cloud", "Soft", "Hoodie")
                            if r[0]:
                                clean_name = (
                                    str(r[0]).replace("-", " ").replace("/", " ")
                                )
                                for token in clean_name.split():
                                    if len(token) >= 3:
                                        correction_candidates.append(token)

                    # Remove duplicates for speed
                    correction_candidates = list(set(correction_candidates))
                    print(
                        f"DEBUG: Loaded {len(correction_candidates)} tokens from DB (e.g. {correction_candidates[:3]})",
                        flush=True,
                    )

                except Exception as e:
                    print(f"DEBUG ERROR: DB Correction Load Failed: {e}", flush=True)

            # 2. Extract potential keywords from user message
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
                "please",
                "i",
            }
            user_words = [
                w
                for w in user_msg.split()
                if len(w) >= 3 and w.lower() not in ignore_words
            ]

            corrected_keywords = []
            for word in user_words:
                # Fuzzy match
                # Using ratio (Levenshtein) is best for fixing typos
                match = process.extractOne(
                    word, correction_candidates, scorer=fuzz.ratio
                )

                # LOWERED THRESHOLD TO 70 (Better for "demin" -> "Denim")
                if match and match[1] >= 70:
                    print(
                        f"DEBUG: Typo Fixed! '{word}' -> '{match[0]}' (Score: {match[1]})",
                        flush=True,
                    )
                    corrected_keywords.append(match[0])
                else:
                    print(f"DEBUG: No match for '{word}' (Best: {match})", flush=True)

            # 3. Search DB again with CORRECTED words
            for kw in corrected_keywords:
                found = db_service.search_products(keyword=kw)
                if found:
                    products.extend(found)

            products = list({p["name"]: p for p in products}.values())

        # Fallback: Best Sellers
        if not products:
            print("DEBUG: Fuzzy search failed. Loading Best Sellers.", flush=True)
            products = db_service.search_products(keyword=None)

        # --- 3. FORMAT DATA FOR AI ---
        if products:
            inv_text = "\n".join(
                [
                    f"- {p['name']} (${p['price']}) | Type: {p.get('type', 'N/A')} | Sizes: {p.get('size', 'N/A')} | Color: {p['color']} | Desc: {p['description']}"
                    for p in products
                ]
            )
        else:
            inv_text = "No stock found."

        # --- 4. UNIVERSAL PROMPT ---
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

        # Save Context
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
