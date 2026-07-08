# Claude Prompt — Phase E

## Grounded Retrieval + Hallucination Prevention

You are a senior Python architect working on the existing ESTIA AI Concierge project.

CRITICAL RULES:

* Do NOT rebuild the project.
* Do NOT redesign the architecture.
* Do NOT change the frontend.
* Do NOT add database storage.
* Do NOT add new external dependencies.
* Do NOT change the knowledge base content.
* Do NOT modify voice.py or image.py.
* Do NOT start unrelated features.
* Work incrementally.

Current issue:
Conversation memory works, but restaurant recommendations may hallucinate names that do not exist in the knowledge base.

Example:
Guest first says:
"We are staying at Porto Elounda with two children aged 5 and 8."

Then asks:
"Where should we have dinner tonight?"

ESTIA must recommend only restaurants that exist in the retrieved knowledge base, such as:

* Cosmos Restaurant
* Elies Restaurant
* Elies Beach House

ESTIA must never invent restaurant names such as Aglio e Olio or Kafenion.

Goal:
Implement Phase E — Grounded Retrieval + Hallucination Prevention.

Scope:
Improve grounding and retrieval quality using the existing architecture.

Required improvements:

1. Retrieval Query Enrichment
   When GuestContext exists, enrich the RAG query before retrieval.

Example enriched query:
"Guest context: property Porto Elounda, family, children aged 5 and 8. User asks: Where should we have dinner tonight?"

This enriched query should be used for retrieve_context.

2. Intent Detection
   Add lightweight rule-based intent detection for:

* restaurant / dining
* bar / drinks
* spa / wellness
* transfer / transportation
* yacht
* family / children
* golf

No LLM calls.

3. Category-Aware Retrieval
   If intent is detected, use it to improve retrieval.

Example:
If intent = restaurant, retrieval should prefer restaurant knowledge.
If intent = bar, retrieval should prefer bar knowledge.
If intent = spa, retrieval should prefer spa knowledge.

Do not over-engineer.

4. Strict Grounding Prompt
   Update the system prompt so ESTIA follows this rule:

ESTIA may only recommend restaurants, bars, facilities, services, experiences and schedules that appear in the retrieved hotel knowledge.

ESTIA must never invent:

* restaurant names
* bar names
* services
* prices
* schedules
* availability
* booking confirmations

If the information is not in the retrieved context, ESTIA should say that it does not have confirmed information and recommend contacting Concierge.

5. Tests
   Add offline tests for:

* enriched query includes property
* enriched query includes family context
* enriched query includes children ages
* restaurant intent detection
* bar intent detection
* spa intent detection
* grounded prompt contains "never invent"
* empty context still works
* no frontend changes

Files likely to modify:

* app/api/routes/chat.py
* app/services/chat_service.py
* app/services/context_extraction.py or new app/services/retrieval_context.py
* tests/

Files NOT to modify:

* static/
* app/api/routes/voice.py
* app/api/routes/image.py
* Dockerfile
* docker-compose.yml
* knowledge/

Workflow:

E1 — DESIGN ONLY
Return:

* proposed design
* exact files to modify
* data flow
* test plan
* risks
  Do NOT write code.
  STOP.

E2 — RETRIEVAL QUERY ENRICHMENT ONLY
Only after I type CONTINUE:

* implement query enrichment
* add tests
  STOP.

E3 — INTENT DETECTION ONLY
Only after I type CONTINUE:

* implement lightweight intent detection
* add tests
  STOP.

E4 — GROUNDED PROMPT ONLY
Only after I type CONTINUE:

* add strict grounding rules to chat_service/system prompt
* add tests
  STOP.

E5 — FINAL VALIDATION ONLY
Only after I type CONTINUE:

* provide full test checklist
* summarize files changed
* update docs/development_guide.md
  STOP.

At the end of every milestone write exactly:

=================================================
PHASE E MILESTONE COMPLETE — TYPE CONTINUE
==========================================

Start now with E1 only.
Do not write code.
