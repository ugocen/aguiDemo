# AG-UI Demo — Durum ve Yol Haritası

Bu doküman üç soruyu yanıtlar: **(1) şu ana kadar ne yaptık, (2) CopilotKit'te
hangi kart/mesaj tipleri uygun ve bizde hangileri hazır, (3) bundan sonra neler
yapabiliriz.**

---

## 1. Şu ana kadar ne yaptık

### Backend (FastAPI + LangGraph + `ag-ui-protocol`)
- **Tek kaynak translator** (`app/agui/translator.py`): tüm AG-UI event'leri tek
  yerden yayınlanır. Run lifecycle eşleşmesi, text mesajı için tek `messageId`,
  `TOOL_CALL_START/ARGS/END/RESULT` sırası, canvas için `STATE_SNAPSHOT/DELTA`
  ve human-in-the-loop suspend/resume tek noktada zorlanır.
- **Ajanlar**: `mock` (scriptli, kimlik bilgisi gerektirmez) ve `langgraph`
  (Marketplace üzerinden gerçek model). İkisi de semantik event üretir; onay
  kararı generator `asend` kanalından geri döner, böylece ajan framework'ten
  bağımsız kalır.
- **Marketplace client** (`app/llm/marketplace.py`): `stream` ve `chunked`
  fallback modları, aktif mod loglanır.
- **Kalıcılık**: PostgreSQL geçmişi, swap edilebilir repository arayüzü arkasında.
- **Auth**: dev stub + Microsoft Entra bearer doğrulama.
- **HITL resume**: run_id anahtarlı in-memory `asyncio.Event` (demo kapsamı,
  Temporal bilinçli olarak kullanılmadı).
- **Kanıt (M6)**: her run için event-log capture + ordering-lint ve testler.

### Frontend (Next.js App Router, TS strict, Zustand, Tiptap)
- Claude benzeri iki bölgeli workspace: solda **Agents + History**, sağda
  **chat**, ajan doküman düzenleyince açılan **Tiptap canvas**.
- **İki AG-UI client**, `NEXT_PUBLIC_CLIENT` ile seçilir:
  - `custom` (varsayılan): `lib/agui.ts` içindeki kendi hafif AG-UI/SSE
    istemcimiz, elle yazılmış kartlar ve **Event Inspector** (canlı event akışı).
  - `copilotkit`: CopilotKit provider + `CopilotChat` + `useCopilotAction`
    kartları, `/api/copilotkit` runtime route'u üzerinden AG-UI backend'e bağlı.
- **Mesaj/kart tipleri**: streaming metin, lookup tool kartı, **tablo**,
  **follow-up / sonraki adımlar**, önerilen sorular, onay (HITL), canvas.

### Senaryo ajanları (`agents/` — ayrı klasör)
Dört scriptli senaryo ajanı, her biri farklı bir kart kombinasyonu gösterir:
`research-assistant`, `doc-writer`, `data-analyst`, `support-triage`. Sidebar'dan
seçilir; frontend seçili ajan id'sini `forwardedProps` ile gönderir, backend
`build_agent` ilgili ajana yönlendirir. Ayrıntı: `agents/README.md`.

### Bulut varlıkları (hazır, deploy manuel)
- `deploy/agentcore/`: aynı ajanı AgentCore runtime kontratı (`/ping`,
  `/invocations`) arkasında paketler; hem CLI hem ECR-register yolu.
- `deploy/eks/`: frontend + backend için minimal Helm chart, RDS ve Entra.

### Doğrulama
- Backend testleri 4/4 geçer; dört senaryo ajanı da lint-temiz akış üretir.
- Frontend `tsc` ve `next build` (hem custom hem CopilotKit) temiz geçer.
- Uçtan uca SSE run'ı: streaming metin → tool → canvas → onay suspend →
  `/agui/resume` → `RUN_FINISHED`.

---

## 2. CopilotKit'te hangi kartlar/mesaj tipleri uygun

CopilotKit'in "hazır kart listesi" yoktur; generative UI'ı sen tanımlarsın. Bizim
kurduğumuz sürümde (1.62.2) mevcut yapı taşları ve bunların hangi mesaj tipine
uyduğu:

### Kartları/mesajları render eden primitive'ler
| CopilotKit primitive | Ne işe yarar | Bizim hangi mesaj tipimize uyar |
| --- | --- | --- |
| `useCopilotAction` + `render` | Ajanın çağırdığı bir tool'u kart olarak render eder | tablo, follow-up, önerilen sorular, lookup tool kartı |
| `useCopilotAction` + `renderAndWaitForResponse` | Human-in-the-loop; kullanıcı yanıtını `respond()` ile döndürür | onay (approval) kartı |
| `useCopilotAction` + `name: "*"` | Eşleşmeyen tüm tool çağrıları için genel (catch-all) render | bilinmeyen/gelecekteki kart tipleri |
| `useCoAgent` + `useCoAgentStateRender` | Paylaşılan agent state'ini UI'a bağlar ve render eder | canvas / shared-state dokümanı |
| `useCopilotChatSuggestions` | Sohbet için önerilen sorular üretir | suggested questions (native yol) |
| `useCopilotReadable` | Uygulama state'ini ajana bağlam olarak verir | seçili doküman/agent'ı bağlam yapmak |
| `CopilotChat` / `CopilotSidebar` / `CopilotPopup` | Hazır sohbet yüzeyleri | ana chat alanı |
| `Markdown`, `ImageRenderer`, `Suggestion(s)` | Mesaj içi zengin render | metin, görsel, öneri çipleri |
| `CopilotDevConsole` | Geliştirici konsolu | bizim Event Inspector'ın CopilotKit karşılığı |

### Bizde CopilotKit ile HAZIR olan kartlar
`components/copilot/CopilotGenerativeUI.tsx` içinde `useCopilotAction` ile:
- `lookupKnowledge` → tool kartı (`render`)
- `renderTable` → tablo kartı (`render`)
- `renderFollowUp` → follow-up listesi (`render`)
- `renderSuggestedQuestions` → öneri çipleri (`render`)
- `requestApproval` → onay kartı (`renderAndWaitForResponse`)

Bunların hepsi backend catalog'u ile birebir aynı isimlerde; ajan tool'u isimle
çağırır, CopilotKit eşleşen render'ı sohbet içinde gösterir.

### CopilotKit modunda artık hazır olanlar
- **Canvas**: shared-state doküman `useCoAgent` ile okunuyor ve
  `CopilotCanvasPanel` ile canlı render ediliyor.
- **Senaryo seçimi**: sidebar'daki seçili ajan id'si CopilotKit provider
  `properties`'i ile `forwardedProps` olarak backend'e geçiyor.
- **HITL onayı**: backend onay tool-call args'ına `runId` enjekte ediyor;
  CopilotKit onay kartı hem `respond()` çağırıyor hem de `/agui/resume`'a köprü
  kuruyor.

### Şu an bilinen sınır
- CopilotKit doğrulaması **derleme/bundling** seviyesinde yapıldı (`tsc` +
  `next build` geçiyor). HITL round-trip ve canvas'ın görsel davranışının tam
  doğrulaması için **tarayıcı + çalışan backend** gerekir; bu ortamda tarayıcı
  yok. `custom` client'ta HITL ve canvas zaten uçtan uca çalışıyor.

---

## 3. Bundan sonra neler yapabiliriz

### Kısa vade (CopilotKit'i tam oturtmak)
1. **CopilotKit-native HITL**: backend'e, onayda run'ı bitirip bir sonraki run'da
   tool sonucunu tüketen bir mod ekle; böylece `renderAndWaitForResponse` uçtan
   uca çalışır. (Alternatif: CopilotKit render içinden `/agui/resume`'a köprü.)
2. **Canvas'ı `useCoAgent` ile bağla**: shared-state dokümanını CopilotKit agent
   state'i olarak expose et, `useCoAgentStateRender` ile canlı render et.
3. **Native öneriler**: `useCopilotChatSuggestions` ile önerilen soruları
   CopilotKit'in kendi mekanizmasına taşı.
4. **CopilotKit modunda ajan seçimi**: sidebar'daki senaryo ajanını CopilotKit
   HttpAgent'a parametre olarak geçir (şu an CopilotKit modu tek ajana bağlı).

### Orta vade (yeni kart tipleri)
5. Yeni generative UI kartları: **chart/grafik**, **kaynak/citation listesi**,
   **dosya/attachment**, **form (yapılandırılmış girdi toplama)**, **kod bloğu**,
   **harita**. Her biri: iki catalog'a tool ekle → store reducer + component
   (custom) ve `useCopilotAction` render (CopilotKit).
6. Senaryo ajanlarını **gerçek LLM** (Marketplace/`langgraph`) ile güçlendir;
   scriptli akışları model kararlarıyla değiştir.

### Uzun vade (üretim ve bulut)
7. **AgentCore deploy** (Phase 2) ve **EKS deploy** (Phase 3) — varlıklar hazır,
   manuel adımlar `deploy/*/README.md`'de.
8. **Entra sign-in**'i aç, geçmişi ve run'ları kullanıcıya scope'la.
9. **Dayanıklı HITL**: in-memory resume yerine kalıcı workflow motoru.
10. Gözlemlenebilirlik: event loglarını topla, lint'le, replay dashboard'u kur.

---

## Nasıl denenir

```bash
# custom client (varsayılan, HITL uçtan uca çalışır, Event Inspector var)
cp .env.example .env
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev   # http://localhost:3000

# CopilotKit client
# .env: NEXT_PUBLIC_CLIENT=copilotkit
```

Sidebar'dan bir senaryo ajanı seç (ör. Doc Writer) ve mesaj gönder; her ajan
farklı kart kombinasyonu üretir. Kaynak eşleme tablosu ve mimari için kök
`README.md`'ye ve `docs/FINDINGS.md`'ye bakın.
