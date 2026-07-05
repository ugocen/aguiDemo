# Architecture invariants (never break)

See `AGENTS.md` for detail. The non-negotiables:

1. Only `backend/app/agui/translator.py` emits AG-UI protocol events. Agents yield
   semantic events (`app/agent/events.py`); they never import the translator.
2. Every model call goes through `app/llm/marketplace.py`.
3. `backend/app/agui/catalog.py` and `frontend/lib/catalog.ts` must declare the
   same tool names and schemas.
4. Identity comes from the bearer, never from `RunAgentInput`.
5. Agents receive the approval decision via generator `asend`; they stay pure.

Conventions: minimal comments, no comment on the same line as code, English in
code, config from the single env-driven `Settings` object (never hardcode).
