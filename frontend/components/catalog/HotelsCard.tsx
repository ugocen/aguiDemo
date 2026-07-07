"use client";

import { useState } from "react";

import { HOTELS_TOOL } from "@/lib/catalog";
import { HotelsItem, useStore } from "@/lib/store";

/**
 * Tool-based generative UI: the agent's renderHotels tool call becomes clickable
 * hotel cards. Selecting one writes the choice into the shared booking cart
 * (STATE_DELTA round-trip) and tells the agent, so both sides stay in sync.
 */
export function HotelsCard({
  item,
  onAction,
}: {
  item: HotelsItem;
  onAction: (text: string) => void;
}) {
  const patchSharedState = useStore((s) => s.patchSharedState);
  const sharedState = useStore((s) => s.sharedState);
  const isRunning = useStore((s) => s.isRunning);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  function select(id: string) {
    if (isRunning) return;
    const hotel = item.hotels.find((h) => h.id === id);
    if (!hotel) return;
    setSelectedId(id);
    const cart = (sharedState.cart ?? {}) as Record<string, unknown>;
    const nights = Number(cart.nights ?? 1) || 1;
    patchSharedState([
      { op: "replace", path: "/cart/hotel", value: hotel.name },
      { op: "replace", path: "/cart/pricePerNight", value: hotel.pricePerNight },
      { op: "replace", path: "/cart/currency", value: hotel.currency },
      { op: "replace", path: "/cart/total", value: nights * hotel.pricePerNight },
    ]);
    onAction(
      `Selected ${hotel.name} in ${hotel.area} at ${hotel.pricePerNight} ${hotel.currency}/night.`,
    );
  }

  return (
    <div className="card">
      <span className="tool-badge">hotels, {HOTELS_TOOL}</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 10 }}>{item.title}</div>}
      <div className="hotel-grid">
        {item.hotels.map((hotel) => (
          <div
            key={hotel.id}
            className={`hotel-card ${selectedId === hotel.id ? "selected" : ""}`}
          >
            <div className="hotel-top">
              <span className="hotel-name">{hotel.name}</span>
              {hotel.rating > 0 && <span className="hotel-rating">★ {hotel.rating.toFixed(1)}</span>}
            </div>
            <div className="hotel-area">{hotel.area}</div>
            <div className="hotel-tags">
              {hotel.seaside && <span className="hotel-tag sea">Seaside</span>}
              {hotel.tursabApproved && <span className="hotel-tag tursab">TÜRSAB</span>}
              {hotel.tags.map((tag) => (
                <span key={tag} className="hotel-tag">
                  {tag}
                </span>
              ))}
            </div>
            <div className="hotel-bottom">
              <span className="hotel-price">
                {hotel.pricePerNight} {hotel.currency}
                <span className="hotel-per"> / night</span>
              </span>
              <button
                className="btn approve hotel-select"
                disabled={isRunning}
                onClick={() => select(hotel.id)}
              >
                {selectedId === hotel.id ? "Selected" : "Select"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
