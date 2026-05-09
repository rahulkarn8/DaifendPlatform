"use client";

import * as React from "react";
import { WidgetFrame } from "@/components/dashboard/WidgetFrame";
import { useTelemetryStore } from "@/store/telemetryStore";
import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import { cn } from "@/lib/utils";

export function RuntimePosture({
  dragHandleProps,
}: {
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
}) {
  const d = useTelemetryStore((s) => s.derived);

  const posture = React.useMemo(() => {
    const risk =
      (100 - d.memoryTrustScore) * 0.45 +
      (100 - d.ragIntegrityScore) * 0.35 +
      Math.min(35, d.unsafeToolAttempts) * 0.6 +
      Math.min(50, d.poisonedVectors / 6) * 0.4 +
      d.semanticDriftScore * 65;

    if (risk < 26) return { label: "contained", tone: "ok" as const };
    if (risk < 44) return { label: "watch", tone: "warn" as const };
    if (risk < 62) return { label: "degrading", tone: "warn" as const };
    return { label: "active compromise", tone: "crit" as const };
  }, [d]);

  const Icon =
    posture.tone === "ok" ? ShieldCheck : posture.tone === "warn" ? ShieldAlert : ShieldX;

  return (
    <WidgetFrame
      title="Agent Runtime"
      hint="Policy enforcement, unsafe tool use, and containment effectiveness."
      statusPill={
        <span
          className={cn(
            "rounded-full border px-2 py-0.5 text-[10px] tracking-[0.14em]",
            posture.tone === "ok" &&
              "border-[rgba(93,214,161,0.25)] bg-[rgba(93,214,161,0.10)] text-foreground/90",
            posture.tone === "warn" &&
              "border-[rgba(244,178,74,0.25)] bg-[rgba(244,178,74,0.10)] text-foreground/90",
            posture.tone === "crit" &&
              "border-[rgba(226,102,102,0.25)] bg-[rgba(226,102,102,0.10)] text-foreground/90",
          )}
        >
          {posture.label.toUpperCase()}
        </span>
      }
      dragHandleProps={dragHandleProps}
    >
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">active agents</div>
            <Icon
              className={cn(
                "h-4 w-4",
                posture.tone === "ok" && "text-[rgba(93,214,161,0.9)]",
                posture.tone === "warn" && "text-[rgba(244,178,74,0.95)]",
                posture.tone === "crit" && "text-[rgba(226,102,102,0.95)]",
              )}
            />
          </div>
          <div className="mt-2 font-[var(--font-display)] text-3xl tracking-[-0.04em]">
            {d.activeAgents}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            containment actions: {d.containmentActions}
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
          <div className="text-xs text-muted-foreground">unsafe tool attempts</div>
          <div className="mt-2 font-[var(--font-display)] text-3xl tracking-[-0.04em]">
            {d.unsafeToolAttempts}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            enforcement:{" "}
            <span className="text-foreground/80">
              {d.unsafeToolAttempts > 0 ? "blocked & audited" : "quiet"}
            </span>
          </div>
        </div>
      </div>
    </WidgetFrame>
  );
}

