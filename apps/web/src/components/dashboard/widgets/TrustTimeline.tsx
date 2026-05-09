"use client";

import * as React from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";
import { WidgetFrame } from "@/components/dashboard/WidgetFrame";
import { useTelemetryStore } from "@/store/telemetryStore";

function fmtTime(ts: number) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function TrustTimeline({
  dragHandleProps,
}: {
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
}) {
  const series = useTelemetryStore((s) => s.series);
  const derived = useTelemetryStore((s) => s.derived);
  const mounted = React.useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const data = React.useMemo(
    () =>
      series.map((p) => ({
        ts: p.ts,
        t: p.memoryTrust,
        r: p.ragIntegrity,
      })),
    [series],
  );

  return (
    <WidgetFrame
      title="Trust Timeline"
      hint="Memory trust vs. RAG integrity (live)."
      statusPill={
        <span className="rounded-full border border-[rgba(159,180,255,0.22)] bg-[rgba(159,180,255,0.10)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-foreground/90">
          {derived.memoryTrustScore.toFixed(1)} • {derived.ragIntegrityScore.toFixed(1)}
        </span>
      }
      dragHandleProps={dragHandleProps}
    >
      <div className="h-[220px]">
        {mounted ? (
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={1}>
            <LineChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <XAxis
                dataKey="ts"
                tickFormatter={fmtTime}
                tick={{ fill: "rgba(160,174,192,0.75)", fontSize: 11 }}
                axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
                tickLine={false}
                minTickGap={28}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: "rgba(160,174,192,0.75)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={32}
              />
              <Tooltip
                contentStyle={{
                  background: "rgba(14,17,23,0.92)",
                  border: "1px solid rgba(255,255,255,0.10)",
                  borderRadius: 12,
                  color: "rgba(245,247,250,0.92)",
                }}
                labelFormatter={(v) => fmtTime(Number(v))}
                formatter={(value, name) => {
                  const text =
                    typeof value === "number" ? value.toFixed(2) : String(value);
                  const label =
                    name === "t" ? "Memory Trust" : "RAG Integrity";
                  return [text, label] as [React.ReactNode, string];
                }}
              />
              <Line
                type="monotone"
                dataKey="t"
                stroke="rgba(159,180,255,0.92)"
                strokeWidth={2}
                dot={false}
                isAnimationActive
              />
              <Line
                type="monotone"
                dataKey="r"
                stroke="rgba(93,214,161,0.85)"
                strokeWidth={2}
                dot={false}
                isAnimationActive
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full w-full rounded-xl border border-border bg-[rgba(255,255,255,0.02)]" />
        )}
      </div>
    </WidgetFrame>
  );
}

