"use client";

import * as React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  type NodeTypes,
  type Node,
  type Edge,
  type NodeMouseHandler,
  type EdgeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";

import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/page/PageHeader";
import { Badge } from "@/components/ui/badge";
import { SystemNode, type SystemNodeData } from "@/components/architecture/SystemNode";
import { architectureEdges, architectureNodes, type FlowSurface } from "@/components/architecture/flowData";
import { useTelemetry } from "@/hooks/useTelemetry";
import { useTelemetryStore } from "@/store/telemetryStore";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const nodeTypes: NodeTypes = {
  system: SystemNode,
};

type Selection =
  | { kind: "none" }
  | { kind: "node"; id: string; node?: Node<SystemNodeData> }
  | { kind: "edge"; id: string; edge?: Edge & { data?: { surface?: FlowSurface } } };

function surfaceLabel(s?: FlowSurface) {
  switch (s) {
    case "agent":
      return "Agent runtime";
    case "memory":
      return "Vector memory";
    case "rag":
      return "RAG pipeline";
    case "control":
      return "Policy / control";
    case "intel":
      return "Threat intelligence";
    case "healing":
      return "Self-healing";
    case "soc":
      return "SOC export";
    default:
      return "Unknown surface";
  }
}

function FlowCanvas({
  onSelect,
  selectedId: _selectedId,
}: {
  onSelect: (sel: Selection) => void;
  selectedId?: string;
}) {
  useTelemetry();
  const derived = useTelemetryStore((s) => s.derived);
  const healingFeed = useTelemetryStore((s) => s.healingFeed);
  const threatFeed = useTelemetryStore((s) => s.threatFeed);
  const [now, setNow] = React.useState(() => Date.now());
  React.useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const isHealingHot = React.useMemo(() => {
    const last = healingFeed[0];
    if (!last) return false;
    return now - last.ts < 12_000;
  }, [healingFeed, now]);

  const risk01 = React.useMemo(() => {
    const risk =
      (100 - derived.memoryTrustScore) * 0.55 +
      (100 - derived.ragIntegrityScore) * 0.25 +
      derived.semanticDriftScore * 55 +
      Math.min(35, derived.unsafeToolAttempts) * 0.65 +
      Math.min(50, derived.poisonedVectors / 6) * 0.4;
    return Math.max(0, Math.min(1, risk / 85));
  }, [derived]);

  const nodes = React.useMemo(() => {
    const trust = derived.memoryTrustScore;
    const drift = derived.semanticDriftScore;
    const rag = derived.ragIntegrityScore;

    const memoryPosture =
      trust >= 86 ? "trusted" : trust >= 72 ? "degrading" : "compromised";
    const ragPosture = rag >= 90 ? "valid" : rag >= 78 ? "contested" : "unsafe";
    const driftPosture =
      drift < 0.12 ? "stable" : drift < 0.22 ? "watch" : drift < 0.33 ? "degrading" : "corrupted";

    return architectureNodes.map((n) => {
      if (n.id === "vector") {
        return {
          ...n,
          data: {
            ...n.data,
            badges: ["memory", memoryPosture, `poisoned:${derived.poisonedVectors}`],
          },
        };
      }
      if (n.id === "rag") {
        return {
          ...n,
          data: {
            ...n.data,
            badges: ["retrieval", ragPosture, `inj:${derived.injectionAttempts}`],
          },
        };
      }
      if (n.id === "agents") {
        return {
          ...n,
          data: {
            ...n.data,
            badges: [
              `active:${derived.activeAgents}`,
              `unsafe:${derived.unsafeToolAttempts}`,
              `contain:${derived.containmentActions}`,
            ],
          },
        };
      }
      if (n.id === "daifend") {
        return {
          ...n,
          data: {
            ...n.data,
            badges: [
              "policy",
              "audit",
              driftPosture,
              isHealingHot ? "response:active" : "response:standby",
            ],
          },
        };
      }
      return n;
    });
  }, [derived, isHealingHot]);

  const edges = React.useMemo(() => {
    const baseOpacity = 0.28 + risk01 * 0.55;
    const controlOpacity = 0.22 + (1 - risk01) * 0.35 + (isHealingHot ? 0.15 : 0);
    const healOpacity = isHealingHot ? 0.75 : 0.35;

    return architectureEdges.map((e) => {
      const surface = (e as { data?: { surface?: FlowSurface } }).data?.surface;
      const isControl = e.className?.includes("df-edge--control");
      const isHeal = e.className?.includes("df-edge--heal");
      const isMuted = e.className?.includes("df-edge--muted");

      const opacity = isHeal
        ? healOpacity
        : isControl
          ? controlOpacity
          : isMuted
            ? baseOpacity * 0.8
            : baseOpacity;

      const width = 1.1 + risk01 * 1.2 + (isHeal ? 0.35 : 0);

      const hasHotThreat =
        threatFeed[0] &&
        now - threatFeed[0].ts < 10_000 &&
        (threatFeed[0].surface === "memory" ? surface === "memory" : true);

      const hot =
        (surface === "memory" && derived.memoryTrustScore < 78) ||
        (surface === "rag" && derived.ragIntegrityScore < 84) ||
        (surface === "agent" && derived.unsafeToolAttempts >= 4) ||
        (surface === "healing" && isHealingHot) ||
        (risk01 > 0.72 && hasHotThreat);

      return {
        ...e,
        className: cn(e.className, hot && "df-edge--hot"),
        style: {
          ...(e.style ?? {}),
          opacity,
          strokeWidth: width,
        },
      };
    });
  }, [derived, isHealingHot, now, risk01, threatFeed]);

  const onNodeClick: NodeMouseHandler = (_e, node) => {
    onSelect({ kind: "node", id: String(node.id), node: node as Node<SystemNodeData> });
  };
  const onEdgeClick: EdgeMouseHandler = (_e, edge) => {
    onSelect({
      kind: "edge",
      id: String(edge.id),
      edge: edge as Edge & { data?: { surface?: FlowSurface } },
    });
  };

  return (
    <div
      className={cn(
        "h-[620px] w-full overflow-hidden rounded-2xl border border-border",
        isHealingHot &&
          "shadow-[0_0_0_1px_rgba(255,255,255,0.04),0_0_80px_-30px_rgba(93,214,161,0.22)]",
      )}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={() => onSelect({ kind: "none" })}
        defaultEdgeOptions={{ zIndex: 1 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          gap={20}
          size={1}
          color="rgba(255,255,255,0.05)"
        />
        <Controls
          showInteractive={false}
          className="!bg-[rgba(14,17,23,0.7)] !border !border-border !rounded-xl"
        />
        <MiniMap
          pannable
          zoomable
          maskColor="rgba(5,5,5,0.55)"
          nodeColor={(n) => {
            if (n.id === "daifend") return "rgba(159,180,255,0.72)";
            if (n.id === "healing") return "rgba(93,214,161,0.60)";
            if (n.id === "vector") return "rgba(244,178,74,0.55)";
            return "rgba(160,174,192,0.36)";
          }}
          className="!bg-[rgba(14,17,23,0.7)] !border !border-border !rounded-xl"
        />
      </ReactFlow>
    </div>
  );
}

export function ArchitectureClient() {
  useTelemetry();
  const derived = useTelemetryStore((s) => s.derived);
  const status = useTelemetryStore((s) => s.status);
  const threatFeed = useTelemetryStore((s) => s.threatFeed);
  const healingFeed = useTelemetryStore((s) => s.healingFeed);

  const [selection, setSelection] = React.useState<Selection>({ kind: "none" });

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Architecture"
        title="Enterprise AI system map — secured by Daifend"
        description="Interactive architecture view of apps, agents, LLMs, vector memory, RAG pipelines, and Daifend’s control plane. Flows are animated to convey policy enforcement and security telemetry."
        right={
          <div className="flex items-center gap-2">
            <Badge className="border border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground">
              Telemetry: {status.toUpperCase()}
            </Badge>
            <Badge className="border border-[rgba(159,180,255,0.22)] bg-[rgba(159,180,255,0.10)] text-foreground/90">
              drift {derived.semanticDriftScore.toFixed(3)}
            </Badge>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-12">
        <Card className="md:col-span-8 border-border bg-card/60 backdrop-blur">
          <div className="p-5">
            <ReactFlowProvider>
              <FlowCanvas
                onSelect={setSelection}
                selectedId={selection.kind === "none" ? undefined : selection.id}
              />
            </ReactFlowProvider>
            <div className="mt-4 text-xs text-muted-foreground">
              Live binding: drift and trust modulate flow intensity; recent healing
              actions “heat up” control-plane and rollback pathways. Click a node
              or flow to inspect.
            </div>
          </div>
        </Card>

        <Card className="md:col-span-4 border-border bg-card/60 backdrop-blur">
          <div className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Inspector
                </div>
                <div className="mt-1 font-[var(--font-display)] text-sm tracking-[-0.02em]">
                  {selection.kind === "node"
                    ? selection.node?.data.title ?? "Node"
                    : selection.kind === "edge"
                      ? String(selection.edge?.label ?? "Flow")
                      : "Select a node or flow"}
                </div>
              </div>
              <Button
                variant="secondary"
                className="h-9 rounded-xl border border-border bg-[rgba(255,255,255,0.03)] px-3 text-xs text-muted-foreground hover:bg-[rgba(255,255,255,0.04)]"
                onClick={() => setSelection({ kind: "none" })}
              >
                Clear
              </Button>
            </div>

            <Separator className="my-4 opacity-60" />

            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="w-full" variant="line">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="signals">Signals</TabsTrigger>
                <TabsTrigger value="controls">Controls</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="mt-4 space-y-3">
                {selection.kind === "none" ? (
                  <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4 text-sm text-muted-foreground">
                    Click any node (Apps, Agents, Vector DB, Daifend…) or a flow edge
                    (retrieval, integrity, rollback…) to view live posture and context.
                  </div>
                ) : selection.kind === "node" ? (
                  <>
                    <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                      <div className="text-xs text-muted-foreground">kind</div>
                      <div className="mt-1 text-sm text-foreground/90">
                        {(selection.node?.data.kind ?? "system").toUpperCase()}
                      </div>
                      {selection.node?.data.subtitle ? (
                        <div className="mt-2 text-sm text-muted-foreground">
                          {selection.node.data.subtitle}
                        </div>
                      ) : null}
                      {selection.node?.data.badges?.length ? (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {selection.node.data.badges.map((b) => (
                            <span
                              key={b}
                              className="rounded-full border border-border bg-[rgba(255,255,255,0.02)] px-2 py-0.5 text-[10px] tracking-[0.12em] text-muted-foreground"
                            >
                              {b.toUpperCase()}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>

                    <div className="grid gap-3">
                      <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                        <div className="text-xs text-muted-foreground">current posture</div>
                        <div className="mt-2 text-sm text-foreground/90">
                          memory trust {derived.memoryTrustScore.toFixed(1)} • drift{" "}
                          {derived.semanticDriftScore.toFixed(3)} • RAG{" "}
                          {derived.ragIntegrityScore.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                    <div className="text-xs text-muted-foreground">surface</div>
                    <div className="mt-1 text-sm text-foreground/90">
                      {surfaceLabel(selection.edge?.data?.surface)}
                    </div>
                    <div className="mt-2 text-sm text-muted-foreground">
                      {String(selection.edge?.source)} → {String(selection.edge?.target)}
                    </div>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="signals" className="mt-4 space-y-3">
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">recent threat</div>
                  <div className="mt-1 text-sm text-foreground/90">
                    {threatFeed[0]
                      ? `${threatFeed[0].signature} • ${threatFeed[0].severity.toUpperCase()} • ${threatFeed[0].surface}`
                      : "No recent signature window."}
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">recent healing</div>
                  <div className="mt-1 text-sm text-foreground/90">
                    {healingFeed[0]
                      ? `${healingFeed[0].action} • ${healingFeed[0].incidentId} • ${(healingFeed[0].progress * 100).toFixed(0)}%`
                      : "No healing actions in the last window."}
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">telemetry status</div>
                  <div className="mt-1 text-sm text-foreground/90">{status.toUpperCase()}</div>
                </div>
              </TabsContent>

              <TabsContent value="controls" className="mt-4 space-y-3">
                <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
                  <div className="text-xs text-muted-foreground">recommended controls</div>
                  <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
                    <li>
                      <span className="text-foreground/80">Memory lineage enforcement</span>{" "}
                      with trust scoring + quarantines on anomalous writes.
                    </li>
                    <li>
                      <span className="text-foreground/80">Retriever chain validation</span>{" "}
                      with signed context windows and injection blocking.
                    </li>
                    <li>
                      <span className="text-foreground/80">Agent tool sandboxing</span>{" "}
                      with risk-based permission escalation and audit trails.
                    </li>
                    <li>
                      <span className="text-foreground/80">Autonomous rollback orchestration</span>{" "}
                      gated by confidence thresholds and policy constraints.
                    </li>
                  </ul>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </Card>
      </div>
    </div>
  );
}

