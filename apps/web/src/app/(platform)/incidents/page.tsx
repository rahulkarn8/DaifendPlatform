import { PageHeader } from "@/components/page/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function IncidentsPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Incidents"
        title="Correlated AI-native events with containment + repair playback"
        description="Incidents unify memory integrity violations, RAG injection attempts, and agent runtime policy breaches into a single narrative with response actions."
        right={
          <Badge className="border border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground">
            Playback: enabled
          </Badge>
        }
      />

      <Card className="border-border bg-card/70 backdrop-blur">
        <div className="p-5">
          <div className="text-sm text-muted-foreground">
            (Next) Incident list with filters (surface, severity, agent session,
            vector namespace), plus “incident playback” timeline driven by live
            telemetry and simulation output.
          </div>
        </div>
      </Card>
    </div>
  );
}

