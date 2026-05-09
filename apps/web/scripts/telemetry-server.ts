import http from "node:http";
import express from "express";
import cors from "cors";
import { Server } from "socket.io";

type TelemetryEvent =
  | {
      type: "memory.trust";
      ts: number;
      trustScore: number; // 0..100
      driftScore: number; // 0..1
      poisonedVectors: number;
    }
  | {
      type: "rag.integrity";
      ts: number;
      integrityScore: number; // 0..100
      injectionAttempts: number;
      maliciousDocsQuarantined: number;
    }
  | {
      type: "agent.runtime";
      ts: number;
      activeAgents: number;
      unsafeToolAttempts: number;
      containmentActions: number;
    }
  | {
      type: "threat.attempt";
      ts: number;
      signature: string;
      severity: "low" | "medium" | "high" | "critical";
      surface: "rag" | "memory" | "agent" | "model" | "identity";
    }
  | {
      type: "healing.action";
      ts: number;
      action:
        | "isolate_vector_segment"
        | "rollback_memory"
        | "invalidate_embeddings"
        | "rotate_agent_session"
        | "restore_trust_baseline";
      incidentId: string;
      progress: number; // 0..1
    };

const PORT = Number(process.env.TELEMETRY_PORT ?? 4001);
const ORIGIN = process.env.TELEMETRY_ORIGIN ?? "http://localhost:3000";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function jitter(base: number, amount: number) {
  return base + (Math.random() * 2 - 1) * amount;
}

function pick<T>(arr: T[]) {
  return arr[Math.floor(Math.random() * arr.length)];
}

const app = express();
app.use(cors({ origin: ORIGIN, credentials: true }));

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: ORIGIN, credentials: true },
});

app.get("/health", (_req, res) => res.json({ ok: true }));

let memoryTrust = 93.6;
let drift = 0.08;
let poisoned = 0;
let ragIntegrity = 96.2;
let activeAgents = 7;

function emitTick() {
  const ts = Date.now();

  drift = clamp(jitter(drift, 0.01), 0, 1);
  memoryTrust = clamp(jitter(memoryTrust, 0.25) - drift * 0.15, 0, 100);
  ragIntegrity = clamp(jitter(ragIntegrity, 0.22) - drift * 0.1, 0, 100);
  poisoned = clamp(Math.round(jitter(poisoned, 0.2)), 0, 250);
  activeAgents = clamp(Math.round(jitter(activeAgents, 0.35)), 0, 64);

  const batch: TelemetryEvent[] = [
    {
      type: "memory.trust",
      ts,
      trustScore: Number(memoryTrust.toFixed(2)),
      driftScore: Number(drift.toFixed(3)),
      poisonedVectors: poisoned,
    },
    {
      type: "rag.integrity",
      ts,
      integrityScore: Number(ragIntegrity.toFixed(2)),
      injectionAttempts: clamp(Math.round(jitter(2, 2)), 0, 22),
      maliciousDocsQuarantined: clamp(Math.round(jitter(1, 1)), 0, 10),
    },
    {
      type: "agent.runtime",
      ts,
      activeAgents,
      unsafeToolAttempts: clamp(Math.round(jitter(1, 2)), 0, 28),
      containmentActions: clamp(Math.round(jitter(1, 1.5)), 0, 10),
    },
  ];

  // occasional threat attempts
  if (Math.random() < 0.42) {
    batch.push({
      type: "threat.attempt",
      ts,
      signature: pick([
        "PromptInjection:ContextOverride",
        "EmbeddingPoison:GradientFlip",
        "AgentToolMisuse:ShellPivot",
        "RAG:RetrieverBypass",
        "ModelManipulation:SpecInversion",
        "SyntheticIdentity:SessionSpoof",
      ]),
      severity: pick(["low", "medium", "high", "critical"]),
      surface: pick(["rag", "memory", "agent", "model", "identity"]),
    });
  }

  io.emit("telemetry:batch", batch);
}

io.on("connection", (socket) => {
  socket.emit("telemetry:hello", {
    serverTime: Date.now(),
    streams: ["telemetry:batch"],
    mode: "demo",
  });

  socket.on("simulation:spike", ({ intensity }: { intensity?: number }) => {
    const k = clamp(intensity ?? 0.7, 0, 1);
    drift = clamp(drift + 0.08 * k, 0, 1);
    poisoned = clamp(poisoned + Math.round(18 * k), 0, 500);
    memoryTrust = clamp(memoryTrust - 3.5 * k, 0, 100);
    ragIntegrity = clamp(ragIntegrity - 3.0 * k, 0, 100);

    io.emit("telemetry:batch", [
      {
        type: "healing.action",
        ts: Date.now(),
        action: "isolate_vector_segment",
        incidentId: `INC-${Date.now().toString().slice(-6)}`,
        progress: 0.12,
      },
    ] satisfies TelemetryEvent[]);
  });
});

setInterval(emitTick, 900);

server.on("error", (err: NodeJS.ErrnoException) => {
  if (err.code === "EADDRINUSE") {
    // eslint-disable-next-line no-console
    console.error(
      `Telemetry port ${PORT} is already in use. ` +
        `If Daifend telemetry is already running, don't start a second instance. ` +
        `Or run with TELEMETRY_PORT=4002 (and set NEXT_PUBLIC_TELEMETRY_URL accordingly).`,
    );
    process.exit(1);
  }
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Daifend mock telemetry listening on http://localhost:${PORT}`);
  // eslint-disable-next-line no-console
  console.log(`CORS origin: ${ORIGIN}`);
});

