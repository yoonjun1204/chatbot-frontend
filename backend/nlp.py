# backend/nlp.py
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session


def get_quick_replies(intent: str) -> List[str]:
    """
    Smart suggestions to show in the UI based on the user's last intent.
    Updated to match the cleaner 'nlu.yml'.
    """

    # --- 1. THE SALES BRAIN (Crucial for driving sales) ---
    if intent == "ask_sales_advice":
        return [
            "Show me cheaper options",
            "Do you have this in Blue?",
            "Is it 100% Cotton?",
            "Show me something formal",
        ]

    # --- 2. PRODUCT BROWSING ---
    if intent == "product_info":
        return [
            "Best sellers",
            "New Arrivals",
            "Size Guide",
            "Fabric care instructions",
        ]

    # --- 3. ORDER TRACKING ---
    if intent == "check_order_status" or intent == "inform_order_id":
        return [
            "Check another order",
            "Where is my package?",
            "Report missing item",
            "Return this item",
        ]

    # --- 4. RETURNS & POLICIES ---
    if intent == "returns":
        return [
            "Start a return",
            "Exchange for different size",
            "What is the return window?",
            "Talk to support",
        ]

    # --- 5. SUPPORT & HANDOVER ---
    # Removed "Restart chat" since that feature is gone
    if intent == "human_handover" or intent == "submit_support_request":
        return ["Check ticket status", "Back to shopping", "Return Policy"]

    # --- 6. FAQ SEARCH ---
    # Removed "search_chat_history" block completely
    if intent == "search_faq" or intent == "ask_payment_methods":
        return [
            "Shipping costs",
            "International delivery",
            "Washing instructions",
            "Payment options",
        ]

    # --- 7. ERROR HANDLING (Smart Recovery) ---
    # If the bot didn't understand (Fallback), give them the 'Main Menu' options
    if intent == "nlu_fallback" or intent == "action_llm_fallback":
        return ["Recommend a shirt", "Check Order Status", "Return Policy", "Help"]

    # Removed "Restart Conversation" option
    if intent == "abusive":
        return ["Contact Human Agent", "Back to shopping"]

    # --- DEFAULT / GREET (The Main Menu) ---
    return [
        "I need a shirt for a wedding",  # Prompt the Sales Brain immediately
        "Check order status",
        "Return policy",
        "Browse Casual Shirts",
    ]


def handle_intent(
    intent: str,
    entities: Dict[str, Any],
    db: Session,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Modified: Logic removed to let Rasa Core & Action Server handle the conversation.
    Returns (None, payload) so main.py knows to use Rasa's response.
    """
    payload: Dict[str, Any] = {}

    # This section retains the payload processing, the fronted may still need to use user_identifier
    user_identifier: Optional[str] = entities.get("user_identifier")

    return None, payload
