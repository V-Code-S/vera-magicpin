"""
conversation_handlers.py — Multi-turn conversation handling for Vera Bot

Implements the optional respond() function for multi-turn capability.
This is a tiebreaker component per the challenge spec §7.4.
"""

from dataclasses import dataclass, field
from typing import Optional
from bot import (
    compose_message,
    get_merchant,
    get_category,
    get_trigger,
    get_customer,
    is_auto_reply,
    detect_intent,
)


@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: str
    trigger_id: str
    customer_id: Optional[str] = None
    turns: list = field(default_factory=list)
    state: str = "active"  # active | ended | waiting
    auto_reply_count: int = 0
    sent_bodies: list = field(default_factory=list)
    category_slug: str = ""


def respond(state: ConversationState, merchant_message: str) -> dict:
    """
    Given the conversation state + merchant's latest message, produce the bot's reply.
    
    Returns dict with keys:
      action: "send" | "wait" | "end"
      body: str (if action="send")
      cta: str (if action="send")
      rationale: str
    """
    
    if state.state == "ended":
        return {
            "action": "end",
            "rationale": "Conversation already ended"
        }
    
    # Record the incoming message
    state.turns.append({
        "from_role": "merchant",
        "message": merchant_message,
        "turn": len(state.turns) + 1
    })
    
    # ── AUTO-REPLY DETECTION ──
    if is_auto_reply(merchant_message, {"turns": state.turns}):
        state.auto_reply_count += 1
        
        if state.auto_reply_count == 1:
            body = "Lagta hai yeh ek automated reply hai. Kya owner/manager directly baat kar sakte hain? Just 1-2 min ka kaam hai 🙏"
            state.turns.append({"from_role": "vera", "message": body})
            return {
                "action": "send",
                "body": body,
                "cta": "open_ended",
                "rationale": "First auto-reply detected — one more attempt to reach real person"
            }
        else:
            state.state = "ended"
            return {
                "action": "end",
                "rationale": "Multiple auto-replies confirmed — graceful exit to save turns"
            }
    
    # Reset auto-reply counter on genuine reply
    state.auto_reply_count = 0
    
    # ── INTENT ROUTING ──
    intent = detect_intent(merchant_message)
    
    if intent == "stop":
        state.state = "ended"
        return {
            "action": "end",
            "rationale": "Explicit stop/not-interested intent — graceful exit, no further nudges"
        }
    
    if intent == "join":
        body = "Badhiya! Main abhi registration link share karti/karta hoon. Aapka exact business name aur city bataiye — baaki sab main handle kar lungi/lunga. ✅"
        state.turns.append({"from_role": "vera", "message": body})
        state.state = "action_mode"
        return {
            "action": "send",
            "body": body,
            "cta": "open_ended",
            "rationale": "Join intent detected — switching to action mode immediately"
        }
    
    # ── TURN LIMIT ──
    vera_turns = sum(1 for t in state.turns if t.get("from_role") == "vera")
    if vera_turns >= 5:
        state.state = "ended"
        return {
            "action": "end",
            "rationale": "5-turn limit reached — ending gracefully"
        }
    
    # ── LOAD CONTEXT ──
    merchant = get_merchant(state.merchant_id)
    if not merchant:
        state.state = "ended"
        return {"action": "end", "rationale": "Merchant context not found"}
    
    category_slug = state.category_slug or merchant.get("category_slug", "")
    category = get_category(category_slug)
    if not category:
        state.state = "ended"
        return {"action": "end", "rationale": "Category context not found"}
    
    trigger = get_trigger(state.trigger_id) or {
        "id": state.trigger_id, "kind": "generic",
        "scope": "merchant", "source": "internal", "payload": {}, "urgency": 2
    }
    
    customer = get_customer(state.customer_id) if state.customer_id else None
    
    # ── COMPOSE REPLY ──
    # Include full conversation context
    conv_history = state.turns[-8:]
    
    try:
        result = compose_message(
            category, merchant, trigger, customer,
            conversation_history=conv_history,
            mode="reply"
        )
    except Exception as e:
        return {
            "action": "send",
            "body": "Zaroor, ek second — abhi check karke bata deta/deti hoon 🙏",
            "cta": "open_ended",
            "rationale": f"Compose error ({e}) — sending acknowledgment"
        }
    
    body = result.get("body", "")
    
    # Anti-repetition
    if body in state.sent_bodies:
        body = "Koi aur sawaal ho toh zaroor bataiye! Main hoon yahaan. 😊"
        result["cta"] = "open_ended"
        result["rationale"] = "Anti-repetition guard — sending fresh closing offer"
    
    state.turns.append({"from_role": "vera", "message": body})
    state.sent_bodies.append(body)
    
    return {
        "action": "send",
        "body": body,
        "cta": result.get("cta", "open_ended"),
        "rationale": result.get("rationale", "")
    }
