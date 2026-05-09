"use client";

import * as React from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { cn } from "@/lib/utils";

export type SystemNodeData = {
  title: string;
  subtitle?: string;
  kind:
    | "enterprise"
    | "agent"
    | "llm"
    | "vector"
    | "rag"
    | "daifend"
    | "intel"
    | "healing"
    | "siem"
    | "cloud";
  badges?: string[];
};

const kindTone: Record<SystemNodeData["kind"], string> = {
  enterprise:
    "border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.03)]",
  agent:
    "border-[rgba(93,214,161,0.20)] bg-[rgba(93,214,161,0.06)]",
  llm:
    "border-[rgba(159,180,255,0.22)] bg-[rgba(159,180,255,0.07)]",
  vector:
    "border-[rgba(244,178,74,0.22)] bg-[rgba(244,178,74,0.06)]",
  rag:
    "border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.03)]",
  daifend:
    "border-[rgba(159,180,255,0.30)] bg-[linear-gradient(145deg,rgba(159,180,255,0.10),rgba(255,255,255,0.02))]",
  intel:
    "border-[rgba(159,180,255,0.22)] bg-[rgba(159,180,255,0.06)]",
  healing:
    "border-[rgba(93,214,161,0.22)] bg-[rgba(93,214,161,0.06)]",
  siem:
    "border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.03)]",
  cloud:
    "border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.03)]",
};

export function SystemNode({ data, selected }: NodeProps<SystemNodeData>) {
  return (
    <div
      className={cn(
        "relative w-[240px] rounded-2xl border px-4 py-3 shadow-[0_0_0_1px_rgba(255,255,255,0.03),0_40px_100px_-80px_rgba(159,180,255,0.35)]",
        kindTone[data.kind],
        selected && "ring-1 ring-[rgba(159,180,255,0.35)]",
      )}
    >
      <div className="absolute inset-0 rounded-2xl bg-[radial-gradient(circle_at_25%_10%,rgba(159,180,255,0.14),transparent_55%)] opacity-70" />

      <div className="relative">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="truncate font-[var(--font-display)] text-[13px] tracking-[-0.02em]">
              {data.title}
            </div>
            {data.subtitle ? (
              <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                {data.subtitle}
              </div>
            ) : null}
          </div>
        </div>

        {data.badges?.length ? (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {data.badges.slice(0, 3).map((b) => (
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

      <Handle
        type="target"
        position={Position.Left}
        className="!h-2.5 !w-2.5 !border !border-[rgba(255,255,255,0.18)] !bg-[rgba(159,180,255,0.22)]"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-2.5 !w-2.5 !border !border-[rgba(255,255,255,0.18)] !bg-[rgba(93,214,161,0.18)]"
      />
    </div>
  );
}

