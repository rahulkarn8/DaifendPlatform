"use client";

import * as React from "react";
import { WidgetFrame } from "@/components/dashboard/WidgetFrame";
import { useTelemetryStore } from "@/store/telemetryStore";
import { cn } from "@/lib/utils";

function levelColor(v: number) {
  // v in 0..1
  const a = 0.05 + v * 0.35;
  return `rgba(159,180,255,${a.toFixed(3)})`;
}

export function SemanticDriftMatrix({
  dragHandleProps,
}: {
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
}) {
  const drift = useTelemetryStore((s) => s.derived.semanticDriftScore);
  const poisoned = useTelemetryStore((s) => s.derived.poisonedVectors);

  const grid = React.useMemo(() => {
    const rows = 8;
    const cols = 18;
    const base = Math.max(0, Math.min(1, drift));
    return Array.from({ length: rows }, (_, r) =>
      Array.from({ length: cols }, (_, c) => {
        const wave = Math.sin((c / cols) * Math.PI * 2 + r * 0.7) * 0.08;
        const noise = (Math.random() - 0.5) * 0.08;
        const v = Math.max(0, Math.min(1, base + wave + noise));
        return v;
      }),
    );
  }, [drift, poisoned]); // poisoned intentionally influences re-render cadence

  const posture =
    drift < 0.12 ? "stable" : drift < 0.22 ? "watch" : drift < 0.33 ? "degrading" : "corrupted";

  return (
    <WidgetFrame
      title="Semantic Drift"
      hint="Heatmap of embedding-space instability and anomalous semantic gradients."
      statusPill={
        <span
          className={cn(
            "rounded-full border px-2 py-0.5 text-[10px] tracking-[0.14em]",
            posture === "stable" &&
              "border-[rgba(93,214,161,0.25)] bg-[rgba(93,214,161,0.10)] text-foreground/90",
            posture === "watch" &&
              "border-[rgba(244,178,74,0.25)] bg-[rgba(244,178,74,0.10)] text-foreground/90",
            (posture === "degrading" || posture === "corrupted") &&
              "border-[rgba(226,102,102,0.25)] bg-[rgba(226,102,102,0.10)] text-foreground/90",
          )}
        >
          {posture.toUpperCase()}
        </span>
      }
      dragHandleProps={dragHandleProps}
    >
      <div className="flex items-end justify-between gap-3">
        <div className="grid grid-cols-[repeat(18,10px)] gap-1">
          {grid.flatMap((row, r) =>
            row.map((v, c) => (
              <div
                key={`${r}-${c}`}
                className="h-[10px] w-[10px] rounded-[3px] border border-[rgba(255,255,255,0.04)]"
                style={{ backgroundColor: levelColor(v) }}
              />
            )),
          )}
        </div>
        <div className="min-w-[120px] text-right">
          <div className="text-xs text-muted-foreground">drift score</div>
          <div className="mt-1 font-[var(--font-display)] text-2xl tracking-[-0.03em]">
            {drift.toFixed(3)}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            poisoned vectors: {poisoned}
          </div>
        </div>
      </div>
    </WidgetFrame>
  );
}

