import { PageHeader } from "@/components/page/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrustTimeline } from "@/components/dashboard/widgets/TrustTimeline";
import { SemanticDriftMatrix } from "@/components/dashboard/widgets/SemanticDriftMatrix";

export default function AiMemorySecurityPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="AI Memory Integrity Center"
        title="Vector memory trust, lineage, and poisoning detection"
        description="Monitor embedding trust, detect semantic drift, isolate suspicious memory injections, and orchestrate rollback to verified baselines."
        right={
          <Badge className="border border-[rgba(159,180,255,0.25)] bg-[rgba(159,180,255,0.12)] text-foreground/90">
            Integrity Mode: Enforced
          </Badge>
        }
      />

      <div className="grid gap-4 md:grid-cols-12">
        <div className="md:col-span-8">
          <TrustTimeline />
        </div>
        <div className="md:col-span-4">
          <SemanticDriftMatrix />
        </div>

        <Card className="md:col-span-12 border-border bg-card/70 backdrop-blur">
          <div className="grid gap-4 p-5 md:grid-cols-3">
            <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Memory lineage explorer
              </div>
              <div className="mt-2 text-sm text-muted-foreground">
                Trace every persisted embedding from ingestion → chunking → scoring
                → retrieval. Identify suspicious injection points and correlate to
                agent sessions.
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Embedding trust scoring
              </div>
              <div className="mt-2 text-sm text-muted-foreground">
                Per-namespace trust baselines, entropy checks, semantic
                consistency windows, and poisoning signatures.
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-[rgba(255,255,255,0.02)] p-4">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Rollback & restore
              </div>
              <div className="mt-2 text-sm text-muted-foreground">
                Snapshot memory segments, quarantine suspect vectors, and
                automatically restore integrity with auditable change sets.
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

