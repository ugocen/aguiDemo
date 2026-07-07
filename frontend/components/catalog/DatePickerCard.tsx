"use client";

import { useState } from "react";

import { DATE_PICKER_TOOL } from "@/lib/catalog";
import { DatePickerItem, useStore } from "@/lib/store";

function nightsBetween(checkIn: string, checkOut: string): number {
  const a = Date.parse(checkIn);
  const b = Date.parse(checkOut);
  if (Number.isNaN(a) || Number.isNaN(b) || b <= a) return 0;
  return Math.round((b - a) / 86_400_000);
}

/**
 * Shared-state date picker. Confirming the dates patches the booking cart
 * (nights, total) and tells the agent, keeping the agent's cart in sync with
 * what the user picked in the UI.
 */
export function DatePickerCard({
  item,
  onAction,
}: {
  item: DatePickerItem;
  onAction: (text: string) => void;
}) {
  const patchSharedState = useStore((s) => s.patchSharedState);
  const sharedState = useStore((s) => s.sharedState);
  const isRunning = useStore((s) => s.isRunning);
  const [checkIn, setCheckIn] = useState(item.checkIn);
  const [checkOut, setCheckOut] = useState(item.checkOut);
  const [confirmed, setConfirmed] = useState(false);

  const nights = nightsBetween(checkIn, checkOut);

  function confirm() {
    if (isRunning || nights <= 0) return;
    setConfirmed(true);
    const cart = (sharedState.cart ?? {}) as Record<string, unknown>;
    const price = Number(cart.pricePerNight ?? 0);
    patchSharedState([
      { op: "replace", path: "/cart/checkIn", value: checkIn },
      { op: "replace", path: "/cart/checkOut", value: checkOut },
      { op: "replace", path: "/cart/nights", value: nights },
      { op: "replace", path: "/cart/total", value: price * nights },
    ]);
    onAction(`Dates set: ${checkIn} to ${checkOut} (${nights} nights).`);
  }

  return (
    <div className="card">
      <span className="tool-badge">dates, {DATE_PICKER_TOOL}</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 10 }}>{item.title}</div>}
      <div className="datepick-row">
        <label className="datepick-field">
          <span className="datepick-label">Check-in</span>
          <input
            type="date"
            className="form-input"
            value={checkIn}
            disabled={confirmed}
            onChange={(e) => setCheckIn(e.target.value)}
          />
        </label>
        <label className="datepick-field">
          <span className="datepick-label">Check-out</span>
          <input
            type="date"
            className="form-input"
            value={checkOut}
            disabled={confirmed}
            onChange={(e) => setCheckOut(e.target.value)}
          />
        </label>
      </div>
      <div className="datepick-foot">
        <span className="datepick-nights">
          {nights > 0 ? `${nights} night${nights === 1 ? "" : "s"}` : "Pick a valid range"}
        </span>
        {confirmed ? (
          <span style={{ color: "var(--ok)" }}>Confirmed</span>
        ) : (
          <button
            className="btn approve"
            disabled={isRunning || nights <= 0}
            onClick={confirm}
          >
            Confirm dates
          </button>
        )}
      </div>
    </div>
  );
}
