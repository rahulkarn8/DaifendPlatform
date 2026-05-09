"use client";

import * as React from "react";
import { WidgetFrame } from "@/components/dashboard/WidgetFrame";
import { useTelemetryStore } from "@/store/telemetryStore";
import { cn } from "@/lib/utils";

const label: Record<string, string> = {
  isolate_vector_segment: "Isolate vector segment",
  rollback_memory: "Rollback memory snapshot",
  invalidate_embeddings: "Invalidate embedding region",
  rotate_agent_session: "Rotate agent session",
  restore_trust_baseline: "Restore trust baseline",
};

function fmtAgo(ts: number) {
  const s = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m`;
}

export function SelfHealingActions({
  dragHandleProps,
}: {
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
}) {
  const feed = useTelemetryStore((s) => s.healingFeed);

  return (
    <WidgetFrame
      title="Self-Healing Engine"
      hint="Autonomous containment and rollback orchestration (live)."
      dragHandleProps={dragHandleProps}
    >
      <div className="space-y-2">
        {feed.length ? (
          feed.slice(0, 8).map((a) => (
            <div
              key={`${a.ts}-${a.incidentId}-${a.action}`}
              className="rounded-xl border border-border bg-[rgba(255,255,255,0.02)] px-3 py-2"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm tracking-[-0.01em]">
                    {label[a.action] ?? a.action}
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    incident{" "}
                    <span className="text-foreground/80">{a.incidentId}</span> •{" "}
                    {fmtAgo(a.ts)} ago
                  </div>
                </div>
                <span className="shrink-0 rounded-full border border-[rgba(93,214,161,0.25)] bg-[rgba(93,214,161,0.10)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-foreground/90">
                  {(a.progress * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
                <div
                  className={cn(
                    "h-full rounded-full",
                    "bg-[linear-gradient(90deg,rgba(93,214,161,0.0),rgba(93,214,161,0.75),rgba(159,180,255,0.6))]",
                  )}
                  style={{ width: `${Math.max(4, Math.min(100, a.progress * 100))}%` }}
                />
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-xl border border-border bg-[rgba(255,255,255,0.02)] p-3 text-sm text-muted-foreground">
            No healing actions in the last window. Trigger the Attack Simulation
            to observe isolation + rollback events.
          </div>
        )}
      </div>
    </WidgetFrame>
  );
}

