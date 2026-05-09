"use client";

import { create } from "zustand";
import { io, type Socket } from "socket.io-client";
import type { TelemetryDerived, TelemetryEvent, TelemetryHello } from "@/types/telemetry";
import { deriveFromBatch, initialDerived } from "@/lib/telemetry/mockDerivation";

type SeriesPoint = {
  ts: number;
  memoryTrust: number;
  drift: number;
  ragIntegrity: number;
  activeAgents: number;
};

type TelemetryState = {
  status: "disconnected" | "connecting" | "connected" | "fallback";
  url: string;
  socket?: Socket;
  hello?: TelemetryHello;
  derived: TelemetryDerived;
  series: SeriesPoint[];
  threatFeed: Array<Extract<TelemetryEvent, { type: "threat.attempt" }>>;
  healingFeed: Array<Extract<TelemetryEvent, { type: "healing.action" }>>;
  lastBatchTs?: number;
  connect: (url?: string) => void;
  disconnect: () => void;
  ingestBatch: (batch: TelemetryEvent[]) => void;
  spikeSimulation: (intensity?: number) => void;
};

function defaultUrl() {
  return process.env.NEXT_PUBLIC_TELEMETRY_URL ?? "http://localhost:4001";
}

export const useTelemetryStore = create<TelemetryState>((set, get) => ({
  status: "disconnected",
  url: defaultUrl(),
  derived: initialDerived(),
  series: [],
  threatFeed: [],
  healingFeed: [],
  connect: (url) => {
    const existing = get().socket;
    if (existing?.connected) return;

    const target = url ?? get().url ?? defaultUrl();
    set({ status: "connecting", url: target });

    const socket = io(target, {
      transports: ["websocket", "polling"],
      timeout: 2500,
      reconnectionAttempts: 3,
    });

    socket.on("connect", () => set({ status: "connected", socket }));
    socket.on("disconnect", () => set({ status: "disconnected" }));
    socket.on("connect_error", () => {
      // Keep the UI alive even if the mock server isn't running.
      set({ status: "fallback", socket: undefined });
    });

    socket.on("telemetry:hello", (hello: TelemetryHello) => set({ hello }));
    socket.on("telemetry:batch", (batch: TelemetryEvent[]) => {
      get().ingestBatch(batch);
    });

    set({ socket });
  },
  disconnect: () => {
    const s = get().socket;
    s?.disconnect();
    set({ socket: undefined, status: "disconnected" });
  },
  ingestBatch: (batch) => {
    set((s) => {
      const derived = deriveFromBatch(s.derived, batch);
      const ts = Date.now();

      const threatFeed = [...s.threatFeed];
      const healingFeed = [...s.healingFeed];
      for (const evt of batch) {
        if (evt.type === "threat.attempt") threatFeed.unshift(evt);
        if (evt.type === "healing.action") healingFeed.unshift(evt);
      }

      const nextSeries = [
        ...s.series,
        {
          ts,
          memoryTrust: derived.memoryTrustScore,
          drift: derived.semanticDriftScore,
          ragIntegrity: derived.ragIntegrityScore,
          activeAgents: derived.activeAgents,
        },
      ];

      return {
        derived,
        lastBatchTs: ts,
        series: nextSeries.slice(-180),
        threatFeed: threatFeed.slice(0, 24),
        healingFeed: healingFeed.slice(0, 18),
      };
    });
  },
  spikeSimulation: (intensity) => {
    const s = get().socket;
    if (s && get().status === "connected") {
      s.emit("simulation:spike", { intensity });
      return;
    }

    // fallback: locally degrade trust so the demo still works without server
    set((state) => {
      const k = Math.max(0, Math.min(1, intensity ?? 0.7));
      const ts = Date.now();
      const batch: TelemetryEvent[] = [
        {
          type: "memory.trust",
          ts,
          trustScore: Math.max(0, state.derived.memoryTrustScore - 3.5 * k),
          driftScore: Math.min(1, state.derived.semanticDriftScore + 0.08 * k),
          poisonedVectors: Math.min(9999, state.derived.poisonedVectors + Math.round(18 * k)),
        },
        {
          type: "threat.attempt",
          ts,
          signature: "EmbeddingPoison:GradientFlip",
          severity: "high",
          surface: "memory",
        },
      ];
      const derived = deriveFromBatch(state.derived, batch);
      const threatEvt = batch.find(
        (e): e is Extract<TelemetryEvent, { type: "threat.attempt" }> =>
          e.type === "threat.attempt",
      );

      const series = [
        ...state.series,
        {
          ts,
          memoryTrust: derived.memoryTrustScore,
          drift: derived.semanticDriftScore,
          ragIntegrity: derived.ragIntegrityScore,
          activeAgents: derived.activeAgents,
        },
      ].slice(-180);

      return {
        derived,
        lastBatchTs: ts,
        series,
        threatFeed: threatEvt ? [threatEvt, ...state.threatFeed].slice(0, 24) : state.threatFeed,
      };
    });
  },
}));

