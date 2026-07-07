"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { RunSummary, fetchRunLog, fetchRuns } from "@/lib/api";
import { AguiEvent } from "@/lib/agui";
import { useStore } from "@/lib/store";

const SPEEDS: { label: string; delay: number }[] = [
  { label: "0.5x", delay: 200 },
  { label: "1x", delay: 90 },
  { label: "2x", delay: 40 },
  { label: "4x", delay: 16 },
];

/**
 * Replay dashboard. Lists captured runs from the backend and re-plays a run's
 * recorded AG-UI events back through the store, so reasoning, steps, cards, and
 * the HITL decision render exactly as they did live — a recording, not a re-run.
 *
 * Playback runs on a requestAnimationFrame loop that applies a batch of events
 * per frame against a virtual clock, so the pace follows the chosen delay and the
 * number of React renders stays bounded regardless of how many events a run has.
 */
export function ReplayPanel({ onClose }: { onClose: () => void }) {
  const handleEvent = useStore((s) => s.handleEvent);
  const resetChat = useStore((s) => s.resetChat);

  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [delay, setDelay] = useState(90);

  const eventsRef = useRef<Record<string, unknown>[]>([]);
  const indexRef = useRef(0);
  const playingRef = useRef(false);
  const delayRef = useRef(delay);
  const timerRef = useRef<number | null>(null);
  const clockStartRef = useRef(0);
  const indexStartRef = useRef(0);

  useEffect(() => {
    delayRef.current = delay;
  }, [delay]);

  const stopLoop = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => stopLoop, [stopLoop]);

  const refresh = useCallback(() => {
    fetchRuns().then(setRuns).catch(() => setRuns([]));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const frame = useCallback(() => {
    if (!playingRef.current) return;
    const elapsed = performance.now() - clockStartRef.current;
    const target = Math.min(
      eventsRef.current.length,
      indexStartRef.current + Math.floor(elapsed / delayRef.current) + 1,
    );
    while (indexRef.current < target) {
      handleEvent(eventsRef.current[indexRef.current] as unknown as AguiEvent);
      indexRef.current += 1;
    }
    setIndex(indexRef.current);
    if (indexRef.current >= eventsRef.current.length) {
      playingRef.current = false;
      setPlaying(false);
      return;
    }
    // A short timer (not rAF) so playback still advances when the tab is hidden;
    // the virtual clock above keeps the pace correct however the timer is throttled.
    timerRef.current = window.setTimeout(frame, 16);
  }, [handleEvent]);

  const start = useCallback(() => {
    clockStartRef.current = performance.now();
    indexStartRef.current = indexRef.current;
    playingRef.current = true;
    setPlaying(true);
    frame();
  }, [frame]);

  const loadRun = useCallback(
    async (runId: string) => {
      stopLoop();
      playingRef.current = false;
      setPlaying(false);
      setSelected(runId);
      const log = await fetchRunLog(runId);
      resetChat();
      eventsRef.current = log;
      indexRef.current = 0;
      setTotal(log.length);
      setIndex(0);
    },
    [stopLoop, resetChat],
  );

  function togglePlay() {
    if (eventsRef.current.length === 0) return;
    if (playingRef.current) {
      playingRef.current = false;
      setPlaying(false);
      stopLoop();
      return;
    }
    if (indexRef.current >= eventsRef.current.length) {
      resetChat();
      indexRef.current = 0;
      setIndex(0);
    }
    start();
  }

  function step() {
    if (playingRef.current || indexRef.current >= eventsRef.current.length) return;
    handleEvent(eventsRef.current[indexRef.current] as unknown as AguiEvent);
    indexRef.current += 1;
    setIndex(indexRef.current);
  }

  function restart() {
    stopLoop();
    playingRef.current = false;
    setPlaying(false);
    resetChat();
    indexRef.current = 0;
    setIndex(0);
  }

  const done = index >= total && total > 0;

  return (
    <div className="inspector">
      <div className="inspector-header">
        <span>Replay, {runs.length} runs</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={refresh}>
            Refresh
          </button>
          <button className="btn" onClick={onClose}>
            Hide
          </button>
        </div>
      </div>

      {selected && (
        <div className="replay-controls">
          <button className="btn approve" onClick={togglePlay} disabled={total === 0}>
            {playing ? "❚❚ Pause" : done ? "↻ Replay" : "▶ Play"}
          </button>
          <button className="btn" onClick={step} disabled={playing || done}>
            Step
          </button>
          <button className="btn" onClick={restart}>
            Restart
          </button>
          <select
            className="replay-speed"
            value={delay}
            onChange={(e) => setDelay(Number(e.target.value))}
            aria-label="Replay speed"
          >
            {SPEEDS.map((s) => (
              <option key={s.delay} value={s.delay}>
                {s.label}
              </option>
            ))}
          </select>
          <span className="replay-progress">
            {index}/{total}
          </span>
        </div>
      )}

      <div className="inspector-body">
        {runs.length === 0 && (
          <div className="empty-hint" style={{ marginTop: 20, fontSize: 13 }}>
            No captured runs yet. Send a message, then Refresh.
          </div>
        )}
        {runs.map((run) => (
          <button
            key={run.run_id}
            className={`replay-run ${run.run_id === selected ? "active" : ""}`}
            onClick={() => loadRun(run.run_id)}
          >
            <span className="replay-run-id">{run.run_id}</span>
            <span className="replay-run-meta">{run.count} events</span>
          </button>
        ))}
      </div>
    </div>
  );
}
