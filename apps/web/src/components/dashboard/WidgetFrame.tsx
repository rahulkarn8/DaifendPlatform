"use client";

import * as React from "react";
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

export function WidgetFrame({
  title,
  hint,
  statusPill,
  dragHandleProps,
  className,
  children,
}: {
  title: string;
  hint?: string;
  statusPill?: React.ReactNode;
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-border bg-card/70 backdrop-blur",
        "shadow-[0_0_0_1px_rgba(255,255,255,0.03),0_30px_90px_-70px_rgba(159,180,255,0.25)]",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4 border-b border-border/70 bg-[rgba(255,255,255,0.02)] px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="font-[var(--font-display)] text-[12px] uppercase tracking-[0.18em] text-foreground/90">
              {title}
            </div>
            {statusPill ? statusPill : null}
          </div>
          {hint ? (
            <div className="mt-1 line-clamp-1 text-xs text-muted-foreground">
              {hint}
            </div>
          ) : null}
        </div>
        <button
          type="button"
          aria-label="Drag widget"
          className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-xl border border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
          {...dragHandleProps}
        >
          <GripVertical className="h-4 w-4" />
        </button>
      </div>

      <div className="p-4">{children}</div>
    </section>
  );
}

