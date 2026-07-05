# Changelog — bu projede şimdiye kadar ne yapıldı

Bu dosya, oturum boyunca eklenen her şeyin temalara göre özetidir (kronolojik
detay için `git log`). Kanonik rehber `AGENTS.md`, derin bağlam
`resources/HANDOFF.md`, kalanlar `TODO.md`.

## Phase 1 — yerel uygulama (çekirdek)
- **Backend** (FastAPI + LangGraph + `ag-ui-protocol`): tek-kaynak `translator`
  (tüm AG-UI event'leri buradan), `mock` + `langgraph` ajanları, SSE + 15s
  keepalive, in-memory HITL resume (`/agui/resume`), event capture + ordering
  lint, PostgreSQL geçmişi (swap edilebilir repository), dev/Entra auth.
- **Frontend** (Next.js App Router, TS strict, Zustand, Tiptap): iki bölgeli
  workspace (agents + history sidebar, chat, canvas), custom AG-UI/SSE client,
  canlı **Event Inspector**.
- **Kanıt**: `pytest` testleri, `docs/sample_run_log.jsonl` (lint-temiz).

## Mesaj / kart tipleri (10 tip, 8 tool)
text, lookup tool, **table**, **chart** (inline SVG), follow-up, suggested
questions, **citations**, **form**, approval (HITL), canvas. Her biri iki
client'ta da render edilir; catalog parity `smoke_e2e.py` ile denetlenir.

## İkinci client — CopilotKit
- `@copilotkit/*` 1.62.2 + `@ag-ui/client`; `/api/copilotkit` runtime route'u
  `HttpAgent` ile backend'e köprü.
- Tüm kartlar `useCopilotAction` ile (`CopilotGenerativeUI`); canvas `useCoAgent`
  ile (`CopilotCanvasPanel`); senaryo seçimi provider `properties` ile; onay
  `respond()` + `/agui/resume` köprüsü. `NEXT_PUBLIC_CLIENT` ile seçilir.
- Build-doğrulandı (`tsc` + `next build`); tam runtime doğrulaması tarayıcı ister.

## Senaryo ajanları (`agents/` — ayrı paket)
`research-assistant`, `doc-writer`, `data-analyst`, `support-triage` — her biri
farklı kart kombinasyonu. `forwardedProps.agentId` ile yönlendirilir, `/agents`
ile sidebar'a düşer, aynı translator'ı kullanır (AgentCore'a uygun).

## Vendor-agnostik LLM (Claude / OpenAI / Gemini / Marketplace)
`app/llm/factory.build_llm` tek model yolu; `LLM_PROVIDER` ile vendor seçilir.
`openai_compatible` (OpenAI + Marketplace), `anthropic_provider` (Claude Messages
API), `gemini_provider` (streamGenerateContent) — hepsi aynı `stream_completion`.
`test_llm_providers.py` her vendor'ın SSE parse'ını mock HTTP ile doğrular.

## Bulut varlıkları (hazır, deploy edilmedi)
- `deploy/agentcore/` — Bedrock AgentCore paketleme (`/ping`+`/invocations`) +
  Dockerfile (CLI veya ECR-register).
- `deploy/eks/` — minimal Helm chart (backend/frontend/ingress/config), RDS+Entra.
- `deploy/aws/` — **güvenli AWS flow**: IAM policy + `bootstrap_iam.sh` (root ile
  bir kez `agui-deployer` oluştur) + README. Sonra hep o profil, asla root.

## Çoklu-araç agent kurulumu
- `AGENTS.md` (kanonik, cross-tool) + `CLAUDE.md` (`@AGENTS.md` import → drift yok).
- **Claude Code**: `.claude/agents/` (card-type-builder, scenario-agent-builder,
  agui-verifier), `.claude/commands/`, `.claude/settings.json` (allow + deny).
- **Antigravity**: `.agents/rules/` (start/invariants/verify/isolation/aws),
  `.agents/workflows/`.
- **8 komut/workflow**: `/check` `/verify` `/smoke` `/run` `/build` `/add-card`
  `/new-scenario` `/aws-bootstrap`.
- `scripts/check_env.sh` (ön koşul doktoru), `backend/scripts/smoke_e2e.py`
  (uçtan uca SSE smoke, exit-code'lu).

## Kurallar / guardrail'ler
- **İzolasyon**: paketler hep venv/`node_modules` (global kurulum yok);
  `.claude/settings.json` global-install'ları hard-deny eder. AWS/harici servisler
  bu kapsam dışı.
- **AWS**: root sadece bootstrap; sonra `agui-deployer` profili.
- **`.gitignore` / `.dockerignore`** tüm klasörler düşünülerek sertleştirildi
  (env varyantları, cache'ler; imaj context'i sadece backend/agents/agentcore).

## Dokümantasyon
`README.md` (kapsamlı), `AGENTS.md`, `CLAUDE.md`, `TODO.md`, `docs/FINDINGS.md`,
`docs/PROJECT_STATUS_AND_ROADMAP.md`, `docs/sample_run_log.jsonl`,
`resources/HANDOFF.md`, bu `CHANGELOG.md`. Dokümanlar birbiriyle ve kodla senkron
tutuldu (çapraz-referanslar denetlendi).

## Kalan (TODO)
LLM tool-calling (#7 — vendor katmanı hazır), Entra sign-in (#9), AgentCore/EKS
deploy (#10 — önce `/aws-bootstrap`), CopilotKit tarayıcı doğrulaması (#4/#5),
dayanıklı HITL + replay (#11).
