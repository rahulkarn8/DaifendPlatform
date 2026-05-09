import { PageHeader } from "@/components/page/PageHeader";
import { ThreatTicker } from "@/components/dashboard/widgets/ThreatTicker";
import { Card } from "@/components/ui/card";

export default function ThreatIntelligencePage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="AI Threat Intelligence"
        title="AI-native signatures, model manipulation signals, and synthetic identity telemetry"
        description="Track evolving attack techniques targeting RAG, memory, agent runtimes, and reasoning systems. Correlate signals into incidents and response playbooks."
      />

      <div className="grid gap-4 md:grid-cols-12">
        <div className="md:col-span-7">
          <ThreatTicker />
        </div>
        <Card className="md:col-span-5 border-border bg-card/70 backdrop-blur">
          <div className="p-5">
            <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Attack evolution graph
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              (Next) Show signature families and mutation paths over time, with
              explainable detection logic and recommended mitigations.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

