"use client";

import * as React from "react";
import { Search, Command as CommandIcon, Bell, CircleDot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { MobileNav } from "@/components/shell/MobileNav";

export function Topbar({
  title,
  subtitle,
  onOpenCommandPalette,
}: {
  title: string;
  subtitle?: string;
  onOpenCommandPalette: () => void;
}) {
  return (
    <div className="sticky top-0 z-30 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="flex items-center gap-4 px-4 py-3 md:px-6">
        <MobileNav />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <h1 className="truncate font-[var(--font-display)] text-[15px] tracking-[-0.02em]">
              {title}
            </h1>
            <span className="hidden items-center gap-1 rounded-full border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.03)] px-2 py-0.5 text-[11px] text-muted-foreground md:flex">
              <CircleDot className="h-3 w-3 text-[var(--accent-blue)]" />
              telemetry streaming
            </span>
          </div>
          {subtitle ? (
            <div className="truncate text-xs text-muted-foreground">
              {subtitle}
            </div>
          ) : null}
        </div>

        <div className="hidden md:flex md:items-center md:gap-2">
          <Button
            variant="secondary"
            className={cn(
              "h-9 w-[280px] justify-start gap-2 rounded-xl border border-border bg-[rgba(255,255,255,0.03)] px-3 text-xs text-muted-foreground",
              "hover:bg-[rgba(255,255,255,0.04)]",
            )}
            onClick={onOpenCommandPalette}
          >
            <Search className="h-4 w-4" />
            <span className="flex-1 text-left">Command palette…</span>
            <span className="inline-flex items-center gap-1 rounded-md border border-border bg-[rgba(255,255,255,0.02)] px-2 py-1 font-mono text-[10px] text-muted-foreground">
              <CommandIcon className="h-3 w-3" />K
            </span>
          </Button>

          <Button
            variant="secondary"
            className="h-9 w-9 rounded-xl border border-border bg-[rgba(255,255,255,0.03)] p-0 hover:bg-[rgba(255,255,255,0.04)]"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4 opacity-80" />
          </Button>
        </div>
      </div>
    </div>
  );
}

