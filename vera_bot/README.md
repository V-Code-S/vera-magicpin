# Vera Bot — magicpin AI Challenge Submission

## Approach

**Architecture**: Trigger-kind dispatch + 4-context LLM composer with specialised prompt engineering per trigger type.

**Key design decisions**:

### 1. Trigger-kind dispatch
Rather than a single generic prompt, each trigger kind (`research_digest`, `recall_due`, `perf_dip`, `competitor_opened`, etc.) gets its own composition instructions that pre-wire the correct compulsion lever, voice requirements, CTA shape, and data anchors. This ensures a `regulation_change` trigger always leads with loss aversion + deadline, while a `curious_ask_due` trigger is never promotional.

### 2. Full 4-context integration
All four context layers are always present in the prompt with explicit annotations about which data field drives which part of the message. The composer is told explicitly: "THIS merchant CTR vs PEER CTR MEDIAN" so it can never miss the personalization hook.

### 3. Auto-reply detection
Pattern-matching on 20+ known WhatsApp Business auto-reply signatures (Hindi + English), plus exact-repetition detection. On first auto-reply: one graceful re-attempt. On second: exit. Zero turn-burning.

### 4. Intent-transition routing
Hardcoded routing for critical intents (`join`, `stop`, `accept`) that bypasses the LLM and responds instantly with the correct action. When a merchant says "let's do it", we don't ask another qualifying question — we switch to execution mode.

### 5. Anti-repetition guard
Hash-comparison of all sent message bodies per conversation. If LLM produces a repeat, falls back to a fresh generic close rather than sending the same message twice.

### 6. Graceful exit
5-turn hard limit + stop-intent detection + auto-reply exit logic. The bot knows when to stop.

## Tradeoffs

- **Temperature=0** for determinism as required. This means messages are highly consistent but not randomly varied per run — acceptable for a judged competition.
- **Flask over FastAPI** — Flask was pre-installed; avoided adding dependencies. No async, but each call completes well within the 30s limit.
- **In-memory context store** — sufficient for a 60-minute test window. Production would use Redis.
- **Single model call per composition** — no RAG/retrieval layer. The full 4-context prompt is sufficient given Claude's long context. For scale, embeddings over digest items would reduce token cost.

## What additional context would have helped most

1. **Real open slot data** for customer-facing messages — the dataset has placeholder slots; real availability would make booking triggers far more actionable.
2. **Historical suppression state** — knowing what was sent last week would prevent accidentally re-sending a digest item the merchant already saw.
3. **Merchant WhatsApp session state** — knowing if we're within the 24h session window changes whether we need a template or can send free-form.
4. **Merchant reply history from production** — the dataset has synthetic conversation history; real reply patterns would let us learn which trigger kinds generate the highest reply rates per category.

## How to run

### Start the bot server
```bash

pip install flask requests
python bot.py
# Bot runs on http://localhost:8080
```

### Generate submission.jsonl
```bash

cd vera_bot/
python generate_submission.py
# Output: submission.jsonl (30 lines)
```

### Test against judge simulator
```bash
# In challenge directory:
export BOT_URL=http://localhost:8080
python judge_simulator.py
```

## File structure
```
vera_bot/
├── bot.py                    # Main bot — Flask server + compose() function
├── conversation_handlers.py  # Multi-turn respond() function
├── generate_submission.py    # Generates submission.jsonl
├── submission.jsonl          # 30 test pair outputs (generated)
├── requirements.txt
└── README.md
```
