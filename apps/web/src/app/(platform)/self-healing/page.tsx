import { PageHeader } from "@/components/page/PageHeader";
import { SelfHealingActions } from "@/components/dashboard/widgets/SelfHealingActions";
import { Card } from "@/components/ui/card";

export default function SelfHealingPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Self-Healing Engine"
        title="Autonomous isolation, rollback, and trust restoration"
        description="When memory or runtime corruption is detected, Daifend isolates the blast radius, rolls back trusted state, and restores integrity with auditable orchestration."
      />

      <div className="grid gap-4 md:grid-cols-12">
        <div className="md:col-span-7">
          <SelfHealingActions />
        </div>
        <Card className="md:col-span-5 border-border bg-card/70 backdrop-blur">
          <div className="p-5">
            <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Repair workflow visualization
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              (Next) Visualize step-by-step repair plans: isolate → snapshot →
              rollback → validate → reintroduce, with confidence gates and policy
              constraints.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

