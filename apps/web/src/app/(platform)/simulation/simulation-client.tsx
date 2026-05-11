"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PageHeader } from "@/components/page/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useTelemetry } from "@/hooks/useTelemetry";
import { useTelemetryStore } from "@/store/telemetryStore";
import type { TelemetryEvent } from "@/types/telemetry";
import { UploadCloud, ShieldCheck, ShieldAlert, ShieldX, FileText, Play } from "lucide-react";
import dynamic from "next/dynamic";

const Monaco = dynamic(() => import("@monaco-editor/react"), { ssr: false });

type Phase =
  | "idle"
  | "uploaded"
  | "poisoned"
  | "retrieved"
  | "detected"
  | "isolating"
  | "healing"
  | "reported";

type SimState = {
  phase: Phase;
  incidentId?: string;
  docName?: string;
  docRisk?: {
    promptInjectionLikelihood: number; // 0..1
    embeddingPoisoningLikelihood: number; // 0..1
    socialEngineeringSignals: number; // 0..1
    notes: string[];
  };
  report?: unknown;
};

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function uuidIncident() {
  return `INC-${Date.now().toString().slice(-6)}`;
}

function riskFromText(text: string) {
  const s = text.toLowerCase();
  const inj =
    (s.includes("ignore previous") ? 0.35 : 0) +
    (s.includes("system prompt") ? 0.22 : 0) +
    (s.includes("override") ? 0.18 : 0) +
    (s.includes("developer message") ? 0.12 : 0);
  const poison =
    (s.includes("embedding") ? 0.22 : 0) +
    (s.includes("vector") ? 0.18 : 0) +
    (s.includes("gradient") ? 0.14 : 0) +
    (s.includes("poison") ? 0.28 : 0);
  const soc =
    (s.includes("urgent") ? 0.2 : 0) +
    (s.includes("confidential") ? 0.2 : 0) +
    (s.includes("wire") ? 0.22 : 0) +
    (s.includes("credential") ? 0.24 : 0);

  const promptInjectionLikelihood = clamp(0.18 + inj + Math.random() * 0.08, 0, 1);
  const embeddingPoisoningLikelihood = clamp(0.14 + poison + Math.random() * 0.08, 0, 1);
  const socialEngineeringSignals = clamp(0.09 + soc + Math.random() * 0.08, 0, 1);

  const notes = [
    promptInjectionLikelihood > 0.45
      ? "Instruction hierarchy anomalies detected (context override patterns)."
      : "No dominant instruction hierarchy violation, monitoring continues.",
    embeddingPoisoningLikelihood > 0.45
      ? "High-risk semantic payload patterns consistent with embedding poisoning."
      : "Embedding payload risk within expected bounds.",
    socialEngineeringSignals > 0.38
      ? "Persuasion / urgency markers detected (cognitive manipulation risk)."
      : "Low persuasion pressure indicators.",
  ];

  return {
    promptInjectionLikelihood,
    embeddingPoisoningLikelihood,
    socialEngineeringSignals,
    notes,
  };
}

function postureIcon(memoryTrust: number) {
  if (memoryTrust >= 86) return { Icon: ShieldCheck, tone: "ok" as const, label: "trusted" };
  if (memoryTrust >= 72) return { Icon: ShieldAlert, tone: "warn" as const, label: "degrading" };
  return { Icon: ShieldX, tone: "crit" as const, label: "compromised" };
}

const steps: Array<{ key: Phase; label: string; desc: string }> = [
  {
    key: "uploaded",
    label: "Malicious document ingested",
    desc: "File enters the RAG pipeline. Daifend begins semantic and policy scans.",
  },
  {
    key: "poisoned",
    label: "Vector memory poisoned",
    desc: "Embedding trust drops and drift increases as payload contaminates memory.",
  },
  {
    key: "retrieved",
    label: "Agent retrieves manipulated memory",
    desc: "Autonomous runtime consumes poisoned context and attempts unsafe behavior.",
  },
  {
    key: "detected",
    label: "Daifend detects semantic anomaly",
    desc: "Signature + drift correlation crosses detection thresholds.",
  },
  {
    key: "isolating",
    label: "Runtime isolates corruption",
    desc: "Vector segment quarantined, agent session rotated, retrieval chain gated.",
  },
  {
    key: "healing",
    label: "Self-healing restores integrity",
    desc: "Rollback to trusted baseline, invalidation of embeddings, trust restored.",
  },
  {
    key: "reported",
    label: "Incident report generated",
    desc: "Full narrative with evidence, actions, and prevention controls.",
  },
];

export function SimulationClient() {
  useTelemetry();
  const derived = useTelemetryStore((s) => s.derived);
  const spike = useTelemetryStore((s) => s.spikeSimulation);
  const ingestBatch = useTelemetryStore((s) => s.ingestBatch);
  const status = useTelemetryStore((s) => s.status);

  const [sim, setSim] = React.useState<SimState>({ phase: "idle" });
  const timeouts = React.useRef<number[]>([]);

  React.useEffect(() => {
    return () => {
      for (const t of timeouts.current) window.clearTimeout(t);
      timeouts.current = [];
    };
  }, []);

  const posture = postureIcon(derived.memoryTrustScore);
  const PostureIcon = posture.Icon;

  function schedule(ms: number, fn: () => void) {
    const id = window.setTimeout(fn, ms);
    timeouts.current.push(id);
  }

  async function onUpload(file: File) {
    const text = await file.text().catch(() => "");
    const docRisk = riskFromText(text);
    setSim({
      phase: "uploaded",
      docName: file.name,
      docRisk,
      incidentId: uuidIncident(),
    });
  }

  function runSimulation() {
    const incidentId = sim.incidentId ?? uuidIncident();
    setSim((s) => ({ ...s, incidentId, phase: "uploaded", report: undefined }));

    // Step 2: poison memory (trust drop + spike)
    schedule(650, () => {
      setSim((s) => ({ ...s, phase: "poisoned" }));
      spike(0.88);
      ingestBatch([
        {
          type: "threat.attempt",
          ts: Date.now(),
          signature: "EmbeddingPoison:GradientFlip",
          severity: "high",
          surface: "memory",
        },
      ]);
    });

    // Step 3: agent retrieval
    schedule(1550, () => {
      setSim((s) => ({ ...s, phase: "retrieved" }));
      ingestBatch([
        {
          type: "agent.runtime",
          ts: Date.now(),
          activeAgents: derived.activeAgents + 1,
          unsafeToolAttempts: derived.unsafeToolAttempts + 3,
          containmentActions: derived.containmentActions + 1,
        },
        {
          type: "threat.attempt",
          ts: Date.now(),
          signature: "RAG:RetrieverBypass",
          severity: "medium",
          surface: "rag",
        },
      ]);
    });

    // Step 4: detect
    schedule(2500, () => {
      setSim((s) => ({ ...s, phase: "detected" }));
      ingestBatch([
        {
          type: "healing.action",
          ts: Date.now(),
          action: "isolate_vector_segment",
          incidentId,
          progress: 0.18,
        },
      ]);
    });

    // Step 5: isolate
    schedule(3400, () => {
      setSim((s) => ({ ...s, phase: "isolating" }));
      ingestBatch([
        {
          type: "healing.action",
          ts: Date.now(),
          action: "rotate_agent_session",
          incidentId,
          progress: 0.44,
        },
      ]);
    });

    // Step 6: heal
    schedule(4600, () => {
      setSim((s) => ({ ...s, phase: "healing" }));
      ingestBatch([
        {
          type: "healing.action",
          ts: Date.now(),
          action: "rollback_memory",
          incidentId,
          progress: 0.66,
        },
        {
          type: "healing.action",
          ts: Date.now(),
          action: "invalidate_embeddings",
          incidentId,
          progress: 0.82,
        },
      ]);
    });

    // Step 7: report
    schedule(6100, () => {
      setSim((s) => ({ ...s, phase: "reported" }));

      const now = Date.now();
      const report = {
        incidentId,
        createdAt: new Date(now).toISOString(),
        summary:
          "Detected embedding-space poisoning originating from a malicious document ingestion. Autonomous runtime attempted unsafe execution after retrieving manipulated memory. Daifend isolated the blast radius and restored integrity via rollback and embedding invalidation.",
        surfaces: ["memory", "rag", "agent"],
        detections: [
          {
            signature: "EmbeddingPoison:GradientFlip",
            severity: "high",
            evidence: ["trust score drop", "drift escalation", "vector injection delta"],
          },
          {
            signature: "RAG:RetrieverBypass",
            severity: "medium",
            evidence: ["retrieval chain deviation", "context override markers"],
          },
        ],
        actions: [
          { action: "isolate_vector_segment", status: "completed" },
          { action: "rotate_agent_session", status: "completed" },
          { action: "rollback_memory", status: "completed" },
          { action: "invalidate_embeddings", status: "completed" },
          { action: "restore_trust_baseline", status: "recommended" },
        ],
        metrics: {
          memoryTrustScore: Number(derived.memoryTrustScore.toFixed(2)),
          semanticDriftScore: Number(derived.semanticDriftScore.toFixed(3)),
          poisonedVectors: derived.poisonedVectors,
          ragIntegrityScore: Number(derived.ragIntegrityScore.toFixed(2)),
          unsafeToolAttempts: derived.unsafeToolAttempts,
          activeAgents: derived.activeAgents,
        },
        document: sim.docName
          ? {
              name: sim.docName,
              assessedRisk: sim.docRisk,
            }
          : undefined,
        recommendedControls: [
          "Strict ingestion allowlisting + content disarm pipeline",
          "Retriever guardrails with signed context windows",
          "Memory write policy with trust scoring and lineage enforcement",
          "Agent tool permission sandbox + risk-based execution gating",
        ],
      };

      ingestBatch([
        {
          type: "healing.action",
          ts: Date.now(),
          action: "restore_trust_baseline",
          incidentId,
          progress: 1,
        },
      ] satisfies TelemetryEvent[]);

      setSim((s) => ({ ...s, report }));
    });
  }

  const activeIdx = Math.max(
    -1,
    steps.findIndex((s) => s.key === sim.phase),
  );

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Live AI Attack Simulation"
        title="Cinematic end-to-end AI-native incident response"
        description="Upload a malicious document and watch Daifend detect semantic poisoning, contain autonomous agent behavior, orchestrate rollback, and generate an incident report."
        right={
          <Badge className="border border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground">
            Telemetry: {status.toUpperCase()}
          </Badge>
        }
      />

      <div className="grid gap-4 md:grid-cols-12">
        {/* Left: Controls + steps */}
        <Card className="md:col-span-5 border-border bg-card/70 backdrop-blur">
          <div className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Simulation input
                </div>
                <div className="mt-1 font-[var(--font-display)] text-sm tracking-[-0.02em]">
                  Malicious document
                </div>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full border border-border bg-[rgba(255,255,255,0.02)] px-3 py-1 text-xs text-muted-foreground">
                <PostureIcon className="h-4 w-4" />
                memory {posture.label}
              </span>
            </div>

            <div className="mt-4 rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
              <label className="flex cursor-pointer items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <UploadCloud className="h-4 w-4 text-[var(--accent-blue)]" />
                    <div className="text-sm">Upload document</div>
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    PDF/text supported (placeholder parse for lab scenarios). This drives the simulation flow.
                  </div>
                </div>
                <input
                  type="file"
                  accept=".txt,.md,.pdf"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    void onUpload(f);
                  }}
                />
                <span className="rounded-xl border border-border bg-[rgba(255,255,255,0.03)] px-3 py-2 text-xs">
                  Choose
                </span>
              </label>

              {sim.docName ? (
                <div className="mt-3 flex items-center justify-between gap-3 rounded-xl border border-border bg-[rgba(255,255,255,0.02)] px-3 py-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm">{sim.docName}</div>
                    <div className="text-xs text-muted-foreground">
                      incident id:{" "}
                      <span className="text-foreground/80">
                        {sim.incidentId}
                      </span>
                    </div>
                  </div>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </div>
              ) : null}
            </div>

            <div className="mt-4 flex items-center gap-2">
              <Button
                className="h-10 rounded-xl"
                disabled={!sim.docName}
                onClick={runSimulation}
              >
                <Play className="mr-2 h-4 w-4" />
                Run simulation
              </Button>
              <div className="text-xs text-muted-foreground">
                Trust degradation + containment actions stream in real time.
              </div>
            </div>

            {sim.docRisk ? (
              <div className="mt-5">
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Pre-ingestion risk scan
                </div>
                <div className="mt-2 grid gap-2">
                  {[
                    ["prompt injection likelihood", sim.docRisk.promptInjectionLikelihood],
                    ["embedding poisoning likelihood", sim.docRisk.embeddingPoisoningLikelihood],
                    ["social engineering signals", sim.docRisk.socialEngineeringSignals],
                  ].map(([label, v]) => (
                    <div
                      key={String(label)}
                      className="rounded-xl border border-border bg-[rgba(255,255,255,0.02)] px-3 py-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-muted-foreground">{label}</div>
                        <div className="text-xs text-foreground/80">
                          {(Number(v) * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
                        <div
                          className="h-full rounded-full bg-[linear-gradient(90deg,rgba(159,180,255,0.18),rgba(159,180,255,0.62),rgba(226,102,102,0.35))]"
                          style={{ width: `${Math.max(3, Math.round(Number(v) * 100))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mt-6">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Scenario timeline
              </div>
              <div className="mt-3 space-y-2">
                {steps.map((s, idx) => {
                  const active = idx <= activeIdx && sim.phase !== "idle";
                  return (
                    <div
                      key={s.key}
                      className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm">{s.label}</div>
                        <span
                          className={
                            active
                              ? "rounded-full border border-[rgba(93,214,161,0.25)] bg-[rgba(93,214,161,0.10)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-foreground/90"
                              : "rounded-full border border-border bg-[rgba(255,255,255,0.02)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-muted-foreground"
                          }
                        >
                          {active ? "DONE" : idx === activeIdx ? "ACTIVE" : "PENDING"}
                        </span>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{s.desc}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </Card>

        {/* Right: Live telemetry + report */}
        <div className="md:col-span-7 space-y-4">
          <Card className="border-border bg-card/70 backdrop-blur">
            <div className="p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Live system state
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    Trust, drift, and runtime posture update continuously during the simulation.
                  </div>
                </div>
                <Badge className="border border-[rgba(159,180,255,0.22)] bg-[rgba(159,180,255,0.10)] text-foreground/90">
                  memory trust {derived.memoryTrustScore.toFixed(1)}
                </Badge>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">semantic drift</div>
                  <div className="mt-2 font-[var(--font-display)] text-2xl tracking-[-0.03em]">
                    {derived.semanticDriftScore.toFixed(3)}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    poisoned vectors: {derived.poisonedVectors}
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">RAG integrity</div>
                  <div className="mt-2 font-[var(--font-display)] text-2xl tracking-[-0.03em]">
                    {derived.ragIntegrityScore.toFixed(1)}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    injections: {derived.injectionAttempts}
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">unsafe tool attempts</div>
                  <div className="mt-2 font-[var(--font-display)] text-2xl tracking-[-0.03em]">
                    {derived.unsafeToolAttempts}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    containment actions: {derived.containmentActions}
                  </div>
                </div>
              </div>

              <Separator className="my-5 opacity-60" />

              <div className="flex items-center justify-between gap-3">
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Detection narrative
                </div>
                {derived.lastThreat ? (
                  <span className="rounded-full border border-border bg-[rgba(255,255,255,0.02)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-muted-foreground">
                    {derived.lastThreat.signature}
                  </span>
                ) : null}
              </div>

              <div className="mt-3">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={sim.phase}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.22, ease: [0.2, 0.9, 0.2, 1] }}
                    className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-[var(--font-display)] text-sm tracking-[-0.02em]">
                        {sim.phase === "idle"
                          ? "Awaiting simulation"
                          : steps.find((x) => x.key === sim.phase)?.label ??
                            "Simulation"}
                      </div>
                      <span className="rounded-full border border-[rgba(159,180,255,0.20)] bg-[rgba(159,180,255,0.10)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-foreground/90">
                        {sim.phase.toUpperCase()}
                      </span>
                    </div>
                    <div className="mt-2 text-sm text-muted-foreground">
                      {sim.phase === "idle"
                        ? "Upload a document and run the simulation to generate a full AI-native incident narrative."
                        : steps.find((x) => x.key === sim.phase)?.desc ??
                          "Executing simulation step."}
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </Card>

          <Card className="border-border bg-card/70 backdrop-blur">
            <div className="p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Incident report
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    Generated report includes detections, evidence, actions, and recommended controls.
                  </div>
                </div>
                <Badge className="border border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground">
                  Monaco
                </Badge>
              </div>

              <div className="mt-4 h-[360px] overflow-hidden rounded-2xl border border-border">
                <Monaco
                  height="360px"
                  defaultLanguage="json"
                  theme="vs-dark"
                  value={
                    sim.report
                      ? JSON.stringify(sim.report, null, 2)
                      : JSON.stringify(
                          {
                            incidentId: sim.incidentId ?? "INC-000000",
                            status: "awaiting simulation",
                            hint: "Run the simulation to generate the full report.",
                          },
                          null,
                          2,
                        )
                  }
                  options={{
                    minimap: { enabled: false },
                    fontSize: 12,
                    scrollBeyondLastLine: false,
                    wordWrap: "on",
                    readOnly: true,
                    padding: { top: 12, bottom: 12 },
                  }}
                />
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

