"use client";

import { useCoAgent } from "@copilotkit/react-core";

import { COPILOT_AGENT_NAME } from "@/app/api/copilotkit/agentName";

interface SharedState {
  cart?: {
    destination?: string;
    hotel?: string | null;
    checkIn?: string | null;
    checkOut?: string | null;
    nights?: number;
    currency?: string;
    total?: number;
  };
  quiz?: { level?: number; score?: number; streak?: number; answered?: number };
}

/**
 * Non-document shared state (booking cart / training progress) for the CopilotKit
 * client. The backend emits STATE_SNAPSHOT / STATE_DELTA over arbitrary keys and
 * CopilotKit exposes them through useCoAgent, the same hook the canvas uses.
 */
export function CopilotSharedStatePanel() {
  const { state } = useCoAgent<SharedState>({ name: COPILOT_AGENT_NAME });
  const cart = state?.cart;
  const quiz = state?.quiz;
  if (!cart && !quiz) return null;

  return (
    <div className="sharedstate-panel">
      <div className="sharedstate-head">
        <span className="sharedstate-title">Shared state</span>
        <span className="sharedstate-sub">agent ⇄ UI, live</span>
      </div>

      {cart && (
        <div className="sharedstate-block">
          <div className="sharedstate-label">Booking cart</div>
          <div className="sharedstate-rows">
            <Row k="Destination" v={cart.destination ?? "—"} />
            <Row k="Hotel" v={cart.hotel ?? "not selected"} />
            <Row
              k="Dates"
              v={cart.checkIn && cart.checkOut ? `${cart.checkIn} → ${cart.checkOut}` : "not set"}
            />
            <Row k="Nights" v={cart.nights != null ? String(cart.nights) : "—"} />
            <Row
              k="Total"
              v={cart.total ? `${cart.total} ${cart.currency ?? ""}`.trim() : "—"}
              strong
            />
          </div>
        </div>
      )}

      {quiz && (
        <div className="sharedstate-block">
          <div className="sharedstate-label">Training progress</div>
          <div className="sharedstate-stats">
            <Stat n={quiz.level ?? 1} l="Level" />
            <Stat n={quiz.score ?? 0} l="Score" />
            <Stat n={quiz.streak ?? 0} l="Streak" />
            <Stat n={quiz.answered ?? 0} l="Answered" />
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <div className="sharedstate-row">
      <span className="sharedstate-k">{k}</span>
      <span className={`sharedstate-v ${strong ? "strong" : ""}`}>{v}</span>
    </div>
  );
}

function Stat({ n, l }: { n: number; l: string }) {
  return (
    <div className="sharedstate-stat">
      <span className="sharedstate-n">{n}</span>
      <span className="sharedstate-sl">{l}</span>
    </div>
  );
}
