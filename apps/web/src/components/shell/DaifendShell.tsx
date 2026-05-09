"use client";

import * as React from "react";
import { Sidebar } from "@/components/shell/Sidebar";
import { Topbar } from "@/components/shell/Topbar";
import { CommandPalette } from "@/components/shell/CommandPalette";
import { usePathname, useRouter } from "next/navigation";
import { navItems } from "@/lib/navigation";

function titleForPath(pathname: string) {
  const item = navItems.find(
    (i) =>
      pathname === i.href || (i.href !== "/dashboard" && pathname.startsWith(i.href)),
  );
  return (
    item?.label ??
    (pathname === "/" ? "Dashboard" : pathname.replace("/", "").replaceAll("-", " "))
  );
}

function subtitleForPath(pathname: string) {
  if (pathname.startsWith("/ai-memory-security"))
    return "Vector memory integrity, trust scoring, drift and poisoning detection.";
  if (pathname.startsWith("/agent-runtime"))
    return "Autonomous agent containment, permissions, reasoning chain auditability.";
  if (pathname.startsWith("/threat-intelligence"))
    return "AI-native signatures, synthetic identity signals, model manipulation telemetry.";
  if (pathname.startsWith("/self-healing"))
    return "Autonomous rollback, repair orchestration, trust restoration workflows.";
  if (pathname.startsWith("/architecture"))
    return "Interactive map of your enterprise AI stack and Daifend control plane.";
  if (pathname.startsWith("/simulation"))
    return "Investor-grade live attack simulation across RAG, memory, and agent runtime.";
  return undefined;
}

export function DaifendShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [cmdOpen, setCmdOpen] = React.useState(false);

  React.useEffect(() => {
    let seq = "";
    let seqTimer: number | undefined;

    function clearSeq() {
      seq = "";
      if (seqTimer) window.clearTimeout(seqTimer);
      seqTimer = undefined;
    }

    function onKeyDown(e: KeyboardEvent) {
      const isK = e.key.toLowerCase() === "k";
      if ((e.metaKey || e.ctrlKey) && isK) {
        e.preventDefault();
        setCmdOpen((v) => !v);
        clearSeq();
      }
      if (e.shiftKey && e.key.toLowerCase() === "t") {
        // Handled in palette action; open palette for discoverability.
        setCmdOpen(true);
        clearSeq();
      }

      // Avoid hijacking typing in inputs.
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName?.toLowerCase();
      const isTyping =
        tag === "input" ||
        tag === "textarea" ||
        (target?.getAttribute?.("contenteditable") === "true");
      if (isTyping) return;

      const key = e.key.toLowerCase();
      if (key === "g") {
        seq = "g";
        if (seqTimer) window.clearTimeout(seqTimer);
        seqTimer = window.setTimeout(clearSeq, 900);
        return;
      }

      if (!seq) return;
      // "g" then <key> navigations (Linear-style).
      const map: Record<string, string> = {
        d: "/dashboard",
        m: "/ai-memory-security",
        a: "/agent-runtime",
        t: "/threat-intelligence",
        i: "/incidents",
        h: "/self-healing",
        r: "/research-lab",
        s: "/simulation",
        x: "/architecture",
        p: "/integrations",
        ",": "/settings",
      };
      const dest = map[key];
      if (dest) {
        e.preventDefault();
        router.push(dest);
        clearSeq();
      } else {
        clearSeq();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);

  return (
    <div className="flex min-h-[100svh] w-full">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          title={titleForPath(pathname)}
          subtitle={subtitleForPath(pathname)}
          onOpenCommandPalette={() => setCmdOpen(true)}
        />
        <main className="flex min-w-0 flex-1 flex-col px-4 py-5 md:px-6 md:py-6">
          {children}
        </main>
      </div>
      <CommandPalette open={cmdOpen} onOpenChange={setCmdOpen} />
    </div>
  );
}

