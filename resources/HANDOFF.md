# AG-UI Demo — Devir / Bootstrap Dokümanı

> Bu doküman, projeyi **yeni bir local Claude Code session'ında** (veya elle)
> kaldığımız yerden devam ettirmek için yazıldı. Amaç, mevcut kod tabanının
> tamamını, neden böyle yaptığımızı, doğrulanmış/doğrulanmamış olanları, kalan
> işleri ve bunların adım adım implementasyon planını tek yerde toplamak.
>
> **Bir sonraki session'a ilk mesaj olarak şunu verebilirsin:**
> "resources/HANDOFF.md dosyasını oku, projeyi anla, sonra `docs/PROJECT_STATUS_AND_ROADMAP.md`
> ve `TODO.md`'ye bak. Kaldığımız yerden [şu işi] yapalım."

İçindekiler:
1. [Amaç](#1-amaç)
2. [Neyi neden yaptık (karar günlüğü)](#2-neyi-neden-yaptık-karar-günlüğü)
3. [Mevcut durum — ne çalışıyor, ne çalışmıyor](#3-mevcut-durum)
4. [Mimari ve uçtan uca akış](#4-mimari-ve-uçtan-uca-akış)
5. [Repo haritası — hangi dosya ne yapar](#5-repo-haritası)
6. [Local'de nasıl çalıştırılır ve doğrulanır](#6-localde-nasıl-çalıştırılır-ve-doğrulanır)
7. [Bilinen tuzaklar (gotchas)](#7-bilinen-tuzaklar)
8. [Eksikler ve yapılacaklar](#8-eksikler-ve-yapılacaklar)
9. [İmplementasyon planı (kalan işler, adım adım)](#9-i̇mplementasyon-planı)
10. [Git / branch durumu](#10-git--branch-durumu)

---

## 1. Amaç

**AG-UI protokolünü** uçtan uca sergileyen, Claude benzeri bir asistan workspace'i.
AG-UI (Agent-User Interaction Protocol): backend, tipli JSON event'leri (lifecycle,
text, tool call, state, custom) **Server-Sent Events (SSE)** üzerinden frontend'e
akıtır; frontend her event'i canlı olarak render eder.

Demo dört temel yeteneği + ek kart tiplerini canlı gösterir:
- **Streaming chat** — token'lar model ürettikçe belirir.
- **Görünür tool call** — canlı kart olarak.
- **Paylaşılan-state doküman canvas'ı** — ajan konuşurken canlı düzenler.
- **Human-in-the-loop onay** — ajan durur, kullanıcının kararıyla devam eder.
- **Ek mesaj tipleri** — table, chart, follow-up, suggested questions, citations, form.

Uzun vadeli hedef: ajanları AWS Bedrock **AgentCore**'da, uygulamayı **EKS**'te
çalıştırmak; kimlik **Microsoft Entra** ile; model çağrıları bir **GenAI
Marketplace** gateway'i üzerinden. Faz 1 (yerel) bitti; Faz 2/3 varlıkları hazır
ama deploy edilmedi.

Orijinal build spec'i: kullanıcının ilk verdiği plan (bu repoyu doğuran doküman).
Onun özeti `README.md` ve `docs/` altında yaşıyor.

---

## 2. Neyi neden yaptık (karar günlüğü)

Bu bölüm, kod tabanındaki "neden böyle?" sorularının cevabı. Yeni session'ın
bağlamı en çok buradan kazanır.

- **Tek event kaynağı (`translator.py`).** Tüm AG-UI protokol event'leri tek bir
  yerden yayınlanır. Ajanlar framework-bağımsız *semantik* event'ler üretir
  (`TextDelta`, `ToolCallStarted`, `DocumentDelta`, `ApprovalRequested`);
  translator bunları protokole çevirir ve sıralama/eşleşme kurallarını zorlar.
  Sebep: protokol doğruluğunu tek yerde garanti etmek, ajanları saf tutmak.

- **Ajan → generator + `asend` ile onay.** Ajan bir async generator; onayda
  `decision = yield ApprovalRequested(...)` yapıp kararı **generator'ın send
  kanalından** geri alır. Böylece ajan protokolü hiç bilmez, yalnız translator
  event üretir.

- **İki AG-UI client (custom + CopilotKit), `NEXT_PUBLIC_CLIENT` ile seçilir.**
  - `custom` (varsayılan): `lib/agui.ts`'te elle yazılmış SSE client + Zustand
    store + elle kartlar + canlı Event Inspector. **HITL ve canvas burada uçtan
    uca çalışıyor.**
  - `copilotkit`: CopilotKit provider + CopilotChat + `useCopilotAction` kartları,
    `/api/copilotkit` runtime route'u AG-UI `HttpAgent` ile backend'e köprü.
  - **Neden ikisi birden?** Plan CopilotKit'i "birincil", `@ag-ui/client` +
    elle pane'i "onaylı fallback" olarak veriyordu. Bizim HITL tasarımımız
    (tek suspend edilen run + `/agui/resume`) CopilotKit'in native multi-run
    HITL'ine birebir uymuyor; custom client bunu tam çalıştırıyor. CopilotKit'i
    de kullanıcı açıkça istediği için ekledik — kartlar `useCopilotAction` ile
    tanımlı, derleme doğrulandı, tam runtime doğrulaması tarayıcı ister.

- **CopilotKit 1.4.4 → 1.62.2 yükseltmesi.** 1.4.4 npm tarball'u **`dist`
  içermiyordu** (source-only), import edilemiyordu → `next build` kırılırdı.
  1.62.2 düzgün `dist` ile geliyor. Peer-dep çakışması yüzünden `npm install
  --legacy-peer-deps` gerekiyor (`@langchain/langgraph-sdk` peerOptional).

- **Senaryo ajanları ayrı `agents/` paketinde.** Kullanıcı "ayrı klasör" istedi.
  Dört scripted ajan (research/doc-writer/data-analyst/support-triage), her biri
  farklı kart kombinasyonu. Backend `build_agent`, `forwardedProps.agentId`'ye
  göre yönlendirir. Aynı translator'ı kullandıkları için AgentCore'a da uygun.

- **Scripted ajanlar (gerçek LLM değil).** Marketplace kimlik bilgisi olmadan
  demo çalışsın diye ajanlar deterministik. Kart gösterme "kararı" şu an =
  hangi ajanın/senaryonun seçildiği. Gerçek LLM tool-calling yolu #7'de.

- **In-memory HITL resume.** `run_id` anahtarlı `asyncio.Event`. Karar run
  suspend noktasına varmadan da gelebildiği için registry **sıra-bağımsız**
  (karar buffer'lanır). Prod'da dayanıklı workflow motoru gerekir (Temporal
  bilinçli olarak kullanılmadı — demo kapsamı).

- **Marketplace client OpenAI-uyumlu varsayıldı.** `stream` ve `chunked`
  fallback modları; aktif mod loglanır. Şu an yalnız **metin** streaming var;
  tool-calling yok (bkz. #7).

- **Kimlik header'dan, asla `RunAgentInput`'tan.** dev stub + Entra bearer
  doğrulama kodu yazıldı; Entra gerçek tenant'la test edilmedi.

- **Persistence: Postgres, swap edilebilir repository arkasında.** SQLite ile
  uçtan uca test edildi.

---

## 3. Mevcut durum

### Çalışan ve doğrulanmış (yerelde)
| Özellik | Durum | Nasıl doğrulandı |
|---|---|---|
| Streaming chat, tool card, table, chart, follow-up, suggested, citations, form | ✅ | 5 ajan yolu HTTP/SSE üzerinden koşuldu, hepsi lint-temiz |
| Canvas (custom client) | ✅ | STATE_SNAPSHOT/DELTA uçtan uca |
| HITL onay (custom client) | ✅ | `/agui/resume` ile suspend/resume, approve+reject |
| Persistence | ✅ | SQLite ile create/list/load + tool_events_json |
| Event capture + ordering lint | ✅ | `pytest` 4/4, `docs/sample_run_log.jsonl` lint-temiz |
| Backend/frontend catalog parity (8 tool) | ✅ | statik karşılaştırma |
| tsc + eslint + next build (iki client) | ✅ | |
| Scenario routing (`agentId`) | ✅ | 4 senaryo + mock default |

### Yazıldı ama tam doğrulanmadı (bu ortamda imkânsızdı)
| Özellik | Neden doğrulanmadı |
|---|---|
| CopilotKit HITL round-trip + canvas | **Tarayıcı yok** — sadece derleme/bundling doğrulandı |
| Docker imaj build'i (backend + agentcore) | **Docker daemon yok** — layout dosya-sistemi simülasyonuyla doğrulandı |
| Gerçek LLM (`AGENT_MODE=langgraph`) | **Marketplace anahtarı yok** |
| Entra sign-in | **Azure AD app registration yok** |
| Helm render | **helm CLI yok** — value referansları statik doğrulandı |

---

## 4. Mimari ve uçtan uca akış

```
FRONTEND (Next.js)                         BACKEND (FastAPI)
  page.tsx                                   POST /agui/run
   ├ AgentList / HistoryList (sidebar)         │
   ├ ChatArea (custom)  |  CopilotChat          ▼
   │   store.ts (Zustand reducer)            factory.build_agent(agentId)
   │   catalog.ts (ortak tool sözleşmesi)       │  (mock | langgraph | scenario)
   │   kart component'leri                       ▼
   └ lib/agui.ts (SSE oku)  <──SSE─────  translator.stream()  ← TEK event kaynağı
                                              │   ajan.run(input) → semantik events
                                              ▼
                                          EventEncoder → "data: {...}\n\n"
```

**"analyze my events" (Data Analyst seçili) örneği, adım adım:**
1. `ChatArea.send()` → gerekiyorsa `POST /conversations`, kullanıcı mesajını
   optimistic basar, `RunAgentInput` kurar (`tools`=8 şema, `forwardedProps.agentId`).
2. `runAgent()` → `fetch POST /agui/run` (+ bearer).
3. Backend: `get_current_principal` (dev: sabit), `agentId` okunur,
   `build_agent(..., "data-analyst")` → `DataAnalystAgent`. Kullanıcı turu Postgres'e.
4. `DataAnalystAgent.run()` semantik event yield eder: TextDelta, ToolCallStarted
   (renderTable), **ToolCallStarted (renderChart)**, renderFollowUp, renderSuggested.
5. `translator.stream()` bunları AG-UI event'lerine çevirir: RUN_STARTED →
   STATE_SNAPSHOT → TEXT_MESSAGE_* → (metni kapat) → TOOL_CALL_START/ARGS/END …
   → RUN_FINISHED. Her event `run_logs/<run_id>.jsonl`'e yazılır + loglanır.
6. `EventEncoder` SSE frame'i üretir; `_sse_with_keepalive` arka planda pompalar.
7. Frontend `lib/agui.ts` stream'i parse eder, `store.handleEvent(event)`.
8. `handleEvent` reducer: renderChart TOOL_CALL_START → boş `{kind:"chart"}`
   placeholder; TOOL_CALL_ARGS birikir; TOOL_CALL_END → parse → chart doldurulur.
9. `ChatArea` `item.kind==="chart"` → `<ChartCard>` → **inline SVG bar chart**.

**"Chart'a nasıl karar veriliyor?"** Şu an üç mekanizma var:
- **Senaryo ajanı**: karar yok, ajan kart setini hep gösterir; asıl karar =
  kullanıcının seçtiği ajan.
- **LangGraph ajanı** (`agent/graph.py`): `_plan_node` keyword-heuristic
  (mesajda "table"/"compare" → tablo; şu an **chart bayrağı yok**).
- **Gerçek LLM (henüz bağlı değil)**: AG-UI'ın asıl yolu — `tools` şemaları
  modele verilir, model **function calling** ile hangi tool'u çağıracağına karar
  verir. Bu #7.

Detaylı anlatım gerekiyorsa: son session'daki Türkçe mimari açıklaması bu
dokümanın temelidir; `docs/PROJECT_STATUS_AND_ROADMAP.md` de tamamlar.

---

## 5. Repo haritası

```
backend/app/
  main.py                  FastAPI app, CORS, router'lar, lifespan (create_all)
  config/settings.py       pydantic-settings, TÜM env buradan (tek Settings)
  api/agui_router.py       POST /agui/run (SSE), /agui/resume, /agui/runs/{id}/log
  api/conversations.py     GET/POST /conversations, GET /conversations/{id}
  api/agents.py            GET /agents (senaryo listesi)
  agui/translator.py       ★ TEK event kaynağı — burada protokol üretilir
  agui/catalog.py          ★ 8 frontend-tool şeması (backend tarafı)
  agui/resume.py           in-memory HITL resume registry (sıra-bağımsız)
  agui/lint.py             ordering lint (pairing/sıralama)
  agui/run_capture.py      run_logs/<run_id>.jsonl yazma + okuma
  agent/factory.py         build_agent(settings, agent_id) — yönlendirme
  agent/graph.py           LangGraphAgent (gerçek model yolu, plan node + stream)
  agent/mock.py            MockAgent (scripted showcase, tüm kartlar)
  agent/tools.py           lookup_knowledge (demo backend tool)
  agent/events.py          semantik event dataclass'ları
  agent/base.py            latest_user_text, initial_state
  llm/marketplace.py       ★ gateway client (stream/chunked) — şu an sadece metin
  db/models.py             Conversation, Message (SQLAlchemy)
  db/session.py            async engine, session_scope
  db/repository.py         HistoryRepository (Protocol) + SqlAlchemy impl
  auth/entra.py            get_current_principal (dev stub | Entra JWKS doğrulama)
  logging/setup.py         structlog
backend/tests/test_event_order.py   translator + HITL + lint testleri

agents/                    ★ senaryo ajanları (ayrı paket)
  registry.py              id → sınıf, scenario_descriptors()
  research_assistant.py    lookup+table+citations+suggested
  doc_writer.py            canvas+followup+approval
  data_analyst.py          table+chart+followup+suggested
  support_triage.py        lookup+approval+form+followup
  _common.py               tokens(), call_id()

frontend/
  app/page.tsx             workspace, NEXT_PUBLIC_CLIENT ile client seçimi
  app/providers.tsx        agents/conversations yükler (CopilotKit sarmalanabilir)
  app/api/copilotkit/route.ts     CopilotKit runtime → HttpAgent → /agui/run
  app/api/copilotkit/agentName.ts COPILOT_AGENT_NAME (client/server ayrımı için)
  lib/agui.ts              ★ custom SSE client (runAgent, resumeRun)
  lib/store.ts             ★ Zustand reducer (handleEvent) — event→UI
  lib/catalog.ts           ★ 8 tool şeması (frontend tarafı, backend ile birebir)
  lib/api.ts               conversations/agents fetch helper'ları
  lib/auth.ts              getBearerToken (dev stub; MSAL yeri hazır)
  components/chat/ChatArea.tsx      composer + item render + send orkestrasyonu
  components/catalog/*.tsx          ToolCard, TableCard, ChartCard, FollowUpCard,
                                     CitationsCard, FormCard, ApprovalCard, Suggested
  components/canvas/CanvasPanel.tsx Tiptap canvas (custom client)
  components/inspector/EventInspector.tsx  canlı AG-UI event akışı (dev view)
  components/copilot/               CopilotChatArea, CopilotGenerativeUI,
                                     CopilotCanvasPanel (useCoAgent)

deploy/agentcore/          Faz 2: agentcore_app.py (/ping,/invocations) + Dockerfile
deploy/eks/                Faz 3: Helm chart (backend/frontend/ingress/config)
docs/                      FINDINGS, PROJECT_STATUS_AND_ROADMAP, sample_run_log
README.md, TODO.md, .env.example, docker-compose.yml
```

---

## 6. Local'de nasıl çalıştırılır ve doğrulanır

Gereksinim: Python 3.11, Node 20+ (bu repo 22 ile de çalıştı), Docker (Postgres için).

```bash
# 0. env
cp .env.example .env       # varsayılanlar: AGENT_MODE=mock, AUTH_MODE=dev, NEXT_PUBLIC_CLIENT=custom

# 1. Postgres (opsiyonel; yoksa run'lar akar ama history olmaz)
docker compose up -d postgres

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
# sağlık: curl localhost:8000/health

# 3. Frontend (ayrı terminal)
cd frontend
npm install --legacy-peer-deps      # CopilotKit peer-dep çakışması için --legacy-peer-deps
npm run dev                          # http://localhost:3000
```

Demo denemesi: sidebar'dan bir ajan seç, şunu yaz:
`explain ag-ui, compare the types, next steps, draft a note then approve`

CopilotKit client'ı denemek için `.env`: `NEXT_PUBLIC_CLIENT=copilotkit`.

**Doğrulama komutları:**
```bash
cd backend && source .venv/bin/activate && pytest -q          # 4/4 geçmeli
cd backend && source .venv/bin/activate && python scripts/smoke_e2e.py  # uçtan uca SSE smoke
cd frontend && npm run typecheck && npm run lint && npm run build
```

**Agent kurulumu (çoklu araç için hazır):**
- `AGENTS.md` (kök) — **kanonik**, cross-tool agent rehberi (Antigravity + Claude
  Code + diğerleri okur). Tek doğruluk kaynağı; içeriği başka yere kopyalama.
- **Antigravity**: `.agents/rules/` (always-on kurallar) + `.agents/workflows/`
  (`/verify`, `/smoke`, `/run`, `/add-card`, `/new-scenario` slash workflow'ları).
  Not: bazı Antigravity sürümleri workflow'ları `.agent/workflows/` (tekil)
  okuyor; workflow yok sayılırsa klasörü yeniden adlandır.
- **Claude Code**: `CLAUDE.md` (`@AGENTS.md` import eder — drift olmaz), proje
  hafızası (komutlar, mimari değişmezleri, tuzaklar).
- `.claude/agents/` — subagent'lar: `card-type-builder` (yeni kart tipi ekler),
  `scenario-agent-builder` (yeni senaryo ajanı), `agui-verifier` (doğrular).
- `.claude/commands/` — slash komutları: `/verify`, `/smoke`, `/run`, `/add-card`,
  `/new-scenario`.
- `.claude/settings.json` — sık dev komutları için izin listesi (prompt azaltır).
- `backend/scripts/smoke_e2e.py` — committed uçtan uca doğrulama (exit code'lu).

---

## 7. Bilinen tuzaklar

Bu ortamda debug ederken bulundu; yeni session'da hatırla:

1. **`agents/` paketi import edilebilir olmalı.** Backend `pip install -e` ile
   sadece `app`'i path'e koyar. `agent/factory.py::ensure_agents_on_path()`
   yukarı yürüyerek `agents/registry.py`'yi bulur ve dizini path'e ekler.
   Docker imajlarında `agents/` **kopyalanmalı** — bu yüzden `backend/Dockerfile`
   repo kökünden build edilir (`docker build -f backend/Dockerfile .`).
2. **structlog reserved key.** `log.info("event_name", event=...)` çakışır;
   kwarg'ı `event_type` yaptık.
3. **HITL resume yarışı.** Karar suspend'ten önce gelebilir; `resume.py` kararı
   buffer'lar. Bunu bozma.
4. **SSE keepalive generator'ı iptal etmemeli.** `_sse_with_keepalive` ajanı
   arka plan task'ında pompalar; timeout yalnız queue okumasını etkiler.
5. **CopilotKit 1.4.x source-only.** 1.62.2 kullan; `--legacy-peer-deps` gerekli.
6. **Custom client HITL ≠ CopilotKit HITL.** Custom = tek run + `/agui/resume`.
   CopilotKit modunda onay args'ına `runId` enjekte edilip `resumeRun` köprüsü
   çağrılıyor; bu tarayıcıda test edilmeli.
7. **`.dockerignore` (repo kökü)** frontend/docs/venv'i imaj context'inden hariç
   tutar; backend imajı büyümesin diye.

---

## 8. Eksikler ve yapılacaklar

Canlı liste: `TODO.md`. Öncelik sırasıyla kalanlar:

- **#7 Gerçek LLM ile tool-calling** (en yüksek etki) — Marketplace anahtarı gerekir.
- **#9 Entra sign-in uçtan uca** — Azure AD app registration gerekir.
- **#10 AgentCore + EKS deploy** — AWS erişimi, manuel.
- **CopilotKit HITL/canvas tarayıcı doğrulaması** — #4/#5 kod hazır, gözle test.
- **#11 Dayanıklı HITL + replay dashboard** — büyük, opsiyonel.

---

## 9. İmplementasyon planı

### #7 — Gerçek LLM tool-calling (öncelikli)
**Amaç:** "chart mı table mı?" kararını heuristic yerine modele bıraktırmak.
1. `.env`: `AGENT_MODE=langgraph`, `MARKETPLACE_BASE_URL/API_KEY/MODEL` doldur.
2. `llm/marketplace.py`'ye tool-calling ekle: `_payload`'a OpenAI-uyumlu
   `tools` alanı (RunAgentInput.tools → `{"type":"function","function":{name,
   description, parameters}}`) ve `tool_choice:"auto"` ekle. Stream'de
   `choices[].delta.tool_calls`'ı da biriktir (şu an sadece `content` var).
3. `agent/graph.py::LangGraphAgent.run()`: modelin döndürdüğü `tool_calls`'ı
   `ToolCallStarted(name, args)` semantik event'lerine map et. Frontend-render
   tool'ları (renderChart/renderTable/...) için `ToolCallCompleted` gerekmez;
   `lookupKnowledge` gibi backend tool'ları için tool'u çalıştırıp
   `ToolCallCompleted(result)` yield et, sonucu modele geri besleyip ikinci tur
   yap (klasik tool-use döngüsü).
4. Doğrulama: gerçek anahtarla "compare X and Y in a chart" yazıp modelin
   `renderChart` çağırdığını gör. `lint.py` hâlâ temiz olmalı.
5. İstersek senaryo ajanlarını da aynı yolla LLM-kararlı yapabiliriz.

### #9 — Entra sign-in
1. Azure AD'de SPA app registration: redirect `http://localhost:3000`, expose
   API/scope. `.env`: `AUTH_MODE=entra`, `NEXT_PUBLIC_AUTH_MODE=entra`,
   `ENTRA_TENANT_ID/CLIENT_ID/AUDIENCE`, `NEXT_PUBLIC_ENTRA_CLIENT_ID/TENANT_ID/
   REDIRECT_URI/SCOPE`.
2. `frontend/app/providers.tsx`: `PublicClientApplication` (msal-browser) kur,
   `MsalProvider` ile sar.
3. `frontend/lib/auth.ts::acquireEntraToken()`: `acquireTokenSilent`
   (fallback `loginPopup`) ile access token döndür.
4. Backend `auth/entra.py` zaten JWKS doğrulaması yapıyor — sadece env dolunca
   aktif olur. `preferred_username`/`oid` claim'lerini kontrol et.
5. Doğrulama: giriş yapılmadan uygulama kilitli; history kullanıcıya scope'lu.

### #4/#5 — CopilotKit HITL & canvas tarayıcı doğrulaması
1. `NEXT_PUBLIC_CLIENT=copilotkit`, backend + frontend ayakta.
2. Onay senaryosu (doc-writer) çalıştır; Approve/Reject'in hem `respond()` hem
   `/agui/resume` üzerinden run'ı ilerlettiğini gör. Çift-tetikleme
   (respond + yeni run) gözlemlenirse: ya `respond()`'u kaldırıp yalnız
   `/agui/resume` köprüsüne güven, ya da backend'e CopilotKit-native mod ekle
   (onayda run'ı bitir, sonraki run'da tool-result'ı tüket — ajanları
   "mesajdan resume" edilebilir yap).
3. Canvas: `useCoAgent().state.document`'ın STATE_DELTA ile canlı güncellendiğini
   doğrula.

### #10 — Deploy (manuel)
`deploy/agentcore/README.md` (CLI veya ECR-register) ve `deploy/eks/README.md`
adımlarını izle. Backend imajını **repo kökünden** build et. RDS bağlantısını
`values.yaml` secrets'a, `AUTH_MODE=entra` ile.

### #11 — Dayanıklı HITL + replay dashboard (opsiyonel)
`resume.py`'yi dış store (ör. Redis/DB) ile değiştir; `/agui/runs/{id}/log`'u
tüketen küçük bir replay/lint UI'ı ekle.

---

## 10. Git / branch durumu

- Çalışılan branch: **`main`** (kullanıcı tercihi — her şey tek branch'te güncel).
- Default branch hâlâ `claude/implement-plan-y2lai0` (kozmetik; içerik `main`'de).
  Değiştirmek istersen GitHub Settings → Branches → default = `main`.
- Eski branch'ler silinmedi (kullanıcı istedi).
- Son anlamlı commit: "Debug pass: fix scenario agents in containers, form race,
  path resolution" (`db96ea7`).
- PR akışı bırakıldı; doğrudan `main`'e commit/push ediliyor.

**Yeni local session için hızlı başlangıç:**
```bash
git clone <repo> && cd aguiDemo
git checkout main
# sonra bölüm 6'daki setup + doğrulama adımları
```
