"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import { navItems, navSections } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { DaifendLogo } from "@/components/brand/DaifendLogo";

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button
            variant="secondary"
            className="h-9 w-9 rounded-xl border border-border bg-[rgba(255,255,255,0.03)] p-0 hover:bg-[rgba(255,255,255,0.04)] md:hidden"
            aria-label="Open navigation"
          />
        }
      >
        <Menu className="h-4 w-4 opacity-80" />
      </SheetTrigger>
      <SheetContent side="left" className="w-[320px] bg-sidebar p-0">
        <div className="px-5 py-5">
          <SheetHeader>
            <SheetTitle className="text-left">
              <DaifendLogo className="text-foreground" />
            </SheetTitle>
          </SheetHeader>
          <div className="mt-2 text-xs text-muted-foreground">
            SECURING THE AI RUNTIME
          </div>
        </div>
        <Separator className="opacity-70" />
        <nav className="px-3 py-4">
          {navSections.map((section) => {
            const items = navItems.filter((i) => i.section === section);
            if (!items.length) return null;
            return (
              <div key={section} className="mb-4">
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
                        onClick={() => setOpen(false)}
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
              </div>
            );
          })}
        </nav>
      </SheetContent>
    </Sheet>
  );
}

