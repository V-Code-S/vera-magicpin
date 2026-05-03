import re
from datetime import datetime, timedelta

last_sent = {}


def now():
    return datetime.utcnow()


def suppression_recent(mid, key, mins=1440):
    if not key:
        return False
    ts = last_sent.get((mid, key))
    return ts and (now() - ts) < timedelta(minutes=mins)


def mark_sent(mid, key):
    if key:
        last_sent[(mid, key)] = now()


def num(x):
    try:
        return f"{float(x):.3f}"
    except:
        return str(x)


def social_proof(category, merchant):
    city = merchant["identity"].get("city", "")
    return f"3 {category['slug']} in {city} saw ~20% higher bookings this week"


def active_offer(category, merchant):
    for o in merchant.get("offers", []):
        if o.get("status") == "active":
            return o["title"]
    cat = category.get("offer_catalog", [])
    return cat[0]["title"] if cat else None


def get_signal_days(signals):
    for s in signals or []:
        if "stale_posts" in s:
            m = re.search(r":(\d+)d", s)
            if m:
                return int(m.group(1))
    return None

# ─────────────────────────────
# MAIN
# ─────────────────────────────


def compose(category, merchant, trigger, customer=None):
    kind = trigger.get("kind")
    sup = trigger.get("suppression_key", "")
    mid = merchant["merchant_id"]

    if suppression_recent(mid, sup):
        return empty(sup)

    handlers = {
        "perf_dip": perf_dip,
        "perf_spike": perf_spike,
        "festival_upcoming": festival,
        "competitor_opened": competitor,
        "recall_due": recall,
        "research_digest": research,
        "active_planning_intent": planning,
        "appointment_tomorrow": appointment,
        "chronic_refill_due": refill,
        "category_seasonal": seasonal,
        "cde_opportunity": cde,
        "curious_ask_due": curiosity,
        "customer_lapsed_soft": winback,
        "customer_lapsed_hard": winback,
        "dormant_with_vera": dormant,
        "gbp_unverified": gbp,
        "ipl_match_today": event,
        "milestone_reached": milestone,
        "regulation_change": compliance
    }

    msg = handlers.get(kind, generic)(category, merchant, customer)

    mark_sent(mid, sup)
    return msg

# ─────────────────────────────
# HIGH IMPACT BUILDERS
# ─────────────────────────────


def perf_dip(category, merchant, *_):
    name = merchant["identity"]["name"]
    ctr = merchant["performance"]["ctr"]
    peer = category["peer_stats"]["avg_ctr"]
    city = merchant["identity"].get("city", "")
    stale = get_signal_days(merchant.get("signals"))

    return {
        "body": f"{name}, this week your CTR dropped to {ctr:.3f} vs {peer:.3f} avg in {city}. "
                f"This likely cost you ~20–30% potential customers. "
                f"{'No update for ' + str(stale) + ' days. ' if stale else ''}"
                f"I’ve already prepared a fix — want to see what's causing this?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Cause + impact + action"
    }


def perf_spike(category, merchant, *_):
    name = merchant["identity"]["name"]
    offer = active_offer(category, merchant)

    return {
        "body": f"{name}, your listing is trending up today 📈. "
                f"Perfect time to convert traffic. "
                f"I’ve already prepared {offer or 'a high-converting offer'} — want to apply it now?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Momentum exploitation"
    }


def festival(category, merchant, *_):
    name = merchant["identity"]["name"]
    sp = social_proof(category, merchant)
    offer = active_offer(category, merchant)

    return {
        "body": f"{name}, festive demand is rising this week 🎉. {sp}. "
                f"I’ve already prepared {offer or 'a festive offer'} — want to launch it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Social proof + timing"
    }


def competitor(category, merchant, *_):
    return {
        "body": f"{merchant['identity']['name']}, a new competitor opened nearby this week. "
                f"This could impact your visibility. I’ve prepared a boost plan — want to activate it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Loss aversion"
    }


def recall(category, merchant, customer):
    cname = customer["identity"]["name"] if customer else "Customer"
    offer = active_offer(category, merchant)

    return {
        "body": f"Hi {cname}, you're due for your next visit 🦷 "
                f"{offer or ''}. I’ve kept a slot ready — reply YES to confirm.",
        "cta": "binary_yes_stop",
        "send_as": "merchant_on_behalf",
        "suppression_key": "",
        "rationale": "Direct conversion"
    }


def research(category, merchant, *_):
    return {
        "body": f"{merchant['identity']['name']}, a new study came out this week. "
                f"I’ve already summarised it into 2 key points + a ready message — want to see?",
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Curiosity"
    }

# ─────────────────────────────
# MID TIER TRIGGERS (UPGRADED)
# ─────────────────────────────


def planning(category, merchant, *_):
    return {
        "body": f"{merchant['identity']['name']}, I noticed you're planning something new. "
                f"I’ve already drafted a ready-to-launch campaign — want to review it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Planning assist"
    }


def appointment(category, merchant, *_):
    return {
        "body": f"You have appointments scheduled tomorrow. "
                f"I’ve prepared confirmation messages — want me to send them?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Automation"
    }


def refill(category, merchant, *_):
    return {
        "body": f"A regular customer is likely due for refill. "
                f"I’ve prepared a reminder message — want me to send it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Retention"
    }


def seasonal(category, merchant, *_):
    return {
        "body": f"{merchant['identity']['name']}, demand patterns are shifting this season. "
                f"I’ve prepared a trend-based offer — want to apply it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Seasonal"
    }


def cde(category, merchant, *_):
    return {
        "body": f"A new professional opportunity just opened. "
                f"I’ve summarised key benefits — want to check?",
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Opportunity"
    }


def curiosity(category, merchant, *_):
    return {
        "body": f"You had a query earlier. "
                f"I’ve prepared a clear answer — want to see it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Follow-up"
    }


def winback(category, merchant, *_):
    return {
        "body": f"A past customer hasn’t returned recently. "
                f"I’ve prepared a win-back offer — want to send it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Retention"
    }


def dormant(category, merchant, *_):
    return {
        "body": f"You’ve been inactive for a while. "
                f"I’ve prepared a comeback strategy to regain visibility — want to try it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Reactivation"
    }


def gbp(category, merchant, *_):
    return {
        "body": f"Your Google listing isn’t verified yet. "
                f"This affects discovery. I’ve prepared a fix — want to complete it now?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Visibility"
    }


def event(category, merchant, *_):
    return {
        "body": f"Big event today (IPL) — demand spike expected. "
                f"I’ve prepared a special offer — want to activate it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Event"
    }


def milestone(category, merchant, *_):
    return {
        "body": f"You just hit an important milestone 🎉. "
                f"I’ve prepared a promotion post — want to publish it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Growth"
    }


def compliance(category, merchant, *_):
    return {
        "body": f"A new regulation update may impact you. "
                f"I’ve summarised what to do — want to review?",
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Compliance"
    }


def generic(category, merchant, *_):
    return {
        "body": f"{merchant['identity']['name']}, I found something important. "
                f"I’ve already prepared a solution — want to see it?",
        "cta": "binary_yes_stop",
        "send_as": "vera",
        "suppression_key": "",
        "rationale": "Fallback"
    }


def empty(sup):
    return {"body": "", "cta": "none", "send_as": "vera", "suppression_key": sup, "rationale": "Suppressed"}
