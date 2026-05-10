"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  fetchMemoryFeed,
  fetchMemoryReports,
  startMemoryScan,
  type MemoryReport,
} from "@/lib/memory-integrity-api";

function devToken(): string {
  if (typeof window === "undefined") return "";
  return (
    process.env.NEXT_PUBLIC_DAIFEND_DEV_JWT ??
    localStorage.getItem("daifend_dev_jwt") ??
    ""
  );
}

export function MemoryIntegrityClient() {
  const [tenant, setTenant] = React.useState("default");
  const [token, setToken] = React.useState("");
  const [reports, setReports] = React.useState<MemoryReport[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [collection, setCollection] = React.useState("documents");
  const [lastEvents, setLastEvents] = React.useState<
    Array<Record<string, unknown>>
  >([]);

  React.useEffect(() => {
    setToken(devToken());
  }, []);

  const load = React.useCallback(async () => {
    const t = token || devToken();
    if (!t) {
      setError(
        "Set NEXT_PUBLIC_DAIFEND_DEV_JWT or localStorage daifend_dev_jwt (HS256 JWT with tenant_id claim, or use X-Internal-Token flow via gateway).",
      );
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const [rep, feed] = await Promise.all([
        fetchMemoryReports(tenant, t, 15),
        fetchMemoryFeed(tenant, t).catch(() => ({ events: [] })),
      ]);
      setReports(rep);
      setLastEvents((feed.events ?? []).slice(-12));
    } catch (e) {
      setError(e instanceof Error ? e.message : "load failed");
    } finally {
      setLoading(false);
    }
  }, [tenant, token]);

  React.useEffect(() => {
    void load();
    const id = setInterval(() => void load(), 12_000);
    return () => clearInterval(id);
  }, [load]);

  const latest = reports[0];

  const runScan = async () => {
    const t = token || devToken();
    if (!t) return;
    setLoading(true);
    try {
      await startMemoryScan(tenant, t, {
        vectorBackend: "qdrant",
        collection,
        limit: 256,
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "scan failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3 rounded-2xl border border-border bg-card/50 p-4">
        <div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Tenant
          </div>
          <Input
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            className="mt-1 h-9 w-40"
          />
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Qdrant collection
          </div>
          <Input
            value={collection}
            onChange={(e) => setCollection(e.target.value)}
            className="mt-1 h-9 w-48"
          />
        </div>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          disabled={loading}
          onClick={() => void load()}
        >
          Refresh reports
        </Button>
        <Button type="button" size="sm" disabled={loading} onClick={() => void runScan()}>
          Run vector scan
        </Button>
        {loading ? (
          <Badge variant="outline" className="text-[10px]">
            Loading…
          </Badge>
        ) : null}
      </div>

      {error ? (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {latest ? (
        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Trust" value={latest.trustScore.toFixed(2)} />
          <Metric label="Integrity" value={latest.integrityScore.toFixed(2)} />
          <Metric
            label="Poisoning P"
            value={latest.poisoningProbability.toFixed(4)}
          />
          <Metric label="Semantic drift" value={latest.semanticDrift.toFixed(4)} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          No reports yet. Run a scan from the engine or gateway after migrations
          and vector data exist.
        </p>
      )}

      {lastEvents.length > 0 ? (
        <div className="rounded-2xl border border-border bg-card/40 p-4">
          <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Live feed (gateway → engine)
          </div>
          <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto font-mono text-[11px] text-muted-foreground">
            {lastEvents.map((ev, i) => (
              <li key={i}>{JSON.stringify(ev)}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
      <div className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-[var(--font-display)] text-2xl tracking-tight">
        {value}
      </div>
    </div>
  );
}
