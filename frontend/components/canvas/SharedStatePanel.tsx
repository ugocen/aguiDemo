"use client";

import { useStore } from "@/lib/store";

interface Cart {
  destination?: string;
  hotel?: string | null;
  checkIn?: string | null;
  checkOut?: string | null;
  nights?: number;
  currency?: string;
  total?: number;
}

interface Quiz {
  level?: number;
  score?: number;
  streak?: number;
  answered?: number;
}

/**
 * Live view of the non-document shared state (booking cart, training progress).
 * Both the agent (STATE_DELTA) and the UI (patchSharedState) write here, so this
 * panel reflects the bidirectional shared state as it changes.
 */
export function SharedStatePanel() {
  const sharedState = useStore((s) => s.sharedState);
  const cart = sharedState.cart as Cart | undefined;
  const quiz = sharedState.quiz as Quiz | undefined;

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
