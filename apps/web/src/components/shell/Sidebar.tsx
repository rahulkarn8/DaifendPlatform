"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { navItems, navSections } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { DaifendLogo } from "@/components/brand/DaifendLogo";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:w-[280px] md:flex-col md:border-r md:border-border md:bg-sidebar">
      <div className="px-5 py-5">
        <DaifendLogo className="text-foreground" />
      </div>
      <div className="px-5 pb-4">
        <div className="flex items-center justify-between rounded-xl border border-border bg-[rgba(255,255,255,0.03)] px-3 py-2">
          <div className="flex flex-col">
            <div className="text-xs text-muted-foreground">Runtime posture</div>
            <div className="text-sm tracking-[-0.01em]">Contained</div>
          </div>
          <Badge className="border border-[rgba(159,180,255,0.25)] bg-[rgba(159,180,255,0.14)] text-[rgba(245,247,250,0.92)]">
            LIVE
          </Badge>
        </div>
      </div>

      <nav className="flex-1 px-3 pb-6">
        {navSections.map((section) => {
          const items = navItems.filter((i) => i.section === section);
          if (!items.length) return null;
          return (
            <div key={section} className="mb-5">
              <div className="px-2 pb-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground/80">
                {section}
              </div>
              <div className="space-y-1">
                {items.map((item) => {
                  const active =
                    pathname === item.href ||
                    (item.href !== "/dashboard" && pathname.startsWith(item.href));
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.key}
                      href={item.href}
                      className={cn(
                        "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                        "hover:bg-[rgba(255,255,255,0.04)]",
                        active
                          ? "bg-[rgba(159,180,255,0.10)] text-foreground shadow-[inset_0_0_0_1px_rgba(159,180,255,0.12)]"
                          : "text-[rgba(245,247,250,0.86)]",
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 opacity-80",
                          active ? "text-[var(--accent-blue)] opacity-90" : "",
                        )}
                      />
                      <span className="flex-1">{item.label}</span>
                      {item.key === "simulation" ? (
                        <span className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground group-hover:text-foreground/80">
                          demo
                        </span>
                      ) : null}
                    </Link>
                  );
                })}
              </div>
              <div className="px-2 pt-4">
                <Separator className="opacity-60" />
              </div>
            </div>
          );
        })}
      </nav>

      <div className="px-5 pb-5">
        <div className="rounded-xl border border-border bg-[rgba(255,255,255,0.02)] p-3">
          <div className="text-xs text-muted-foreground">
            “Traditional security protects infrastructure. Daifend protects AI
            systems.”
          </div>
        </div>
      </div>
    </aside>
  );
}

