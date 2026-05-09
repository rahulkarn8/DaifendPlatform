"use client";

import * as React from "react";
import Link from "next/link";
import { WidgetFrame } from "@/components/dashboard/WidgetFrame";
import { useTelemetryStore } from "@/store/telemetryStore";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";

function pillForSeverity(sev: string) {
  if (sev === "critical")
    return "border-[rgba(226,102,102,0.28)] bg-[rgba(226,102,102,0.10)] text-foreground/90";
  if (sev === "high")
    return "border-[rgba(244,178,74,0.28)] bg-[rgba(244,178,74,0.10)] text-foreground/90";
  if (sev === "medium")
    return "border-[rgba(159,180,255,0.25)] bg-[rgba(159,180,255,0.10)] text-foreground/90";
  return "border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground";
}

function fmtAgo(ts: number) {
  const s = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m`;
}

export function ThreatTicker({
  dragHandleProps,
}: {
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
}) {
  const feed = useTelemetryStore((s) => s.threatFeed);
  const status = useTelemetryStore((s) => s.status);
  const [expanded, setExpanded] = React.useState(false);

  const visibleCount = expanded ? 12 : 6;
  const visible = feed.slice(0, visibleCount);

  return (
    <WidgetFrame
      title="Threat Telemetry"
      hint="AI-native attack attempts observed across RAG, memory, agents, and model surfaces."
      statusPill={
        <span className="rounded-full border border-border bg-[rgba(255,255,255,0.02)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-muted-foreground">
          {status.toUpperCase()}
        </span>
      }
      dragHandleProps={dragHandleProps}
    >
      <div className="space-y-3">
        {feed.length ? (
          <>
            <ScrollArea className={cn("rounded-2xl", expanded ? "h-[360px]" : "h-[260px]")}>
              <div className="space-y-2 pr-3">
                {visible.map((t, idx) => (
                  <div
                    key={`${t.ts}-${t.signature}-${t.surface}-${idx}`}
                    className="flex items-center justify-between gap-3 rounded-xl border border-border bg-[rgba(255,255,255,0.02)] px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-sm tracking-[-0.01em]">
                        {t.signature}
                      </div>
                      <div className="mt-0.5 text-xs text-muted-foreground">
                        surface:{" "}
                        <span className="text-foreground/80">{t.surface}</span> •{" "}
                        {fmtAgo(t.ts)} ago
                      </div>
                    </div>
                    <span
                      className={cn(
                        "shrink-0 rounded-full border px-2 py-0.5 text-[10px] tracking-[0.14em]",
                        pillForSeverity(t.severity),
                      )}
                    >
                      {t.severity.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </ScrollArea>

            <div className="flex items-center justify-between gap-3">
              <div className="text-xs text-muted-foreground">
                showing {Math.min(visibleCount, feed.length)} of {feed.length}
              </div>
              <div className="flex items-center gap-3">
                {feed.length > 6 ? (
                  <button
                    type="button"
                    className="text-xs text-muted-foreground hover:text-foreground/90"
                    onClick={() => setExpanded((v) => !v)}
                  >
                    {expanded ? "Show less" : "Show more"}
                  </button>
                ) : null}
                <Link
                  href="/threat-intelligence"
                  className="text-xs text-[var(--accent-blue)] hover:text-foreground"
                >
                  View in Threat Intelligence
                </Link>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-xl border border-border bg-[rgba(255,255,255,0.02)] p-3 text-sm text-muted-foreground">
            No signatures in the last window. Telemetry stream will populate this
            feed as attacks are detected.
          </div>
        )}
      </div>
    </WidgetFrame>
  );
}

