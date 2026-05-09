import { PageHeader } from "@/components/page/PageHeader";
import { RuntimePosture } from "@/components/dashboard/widgets/RuntimePosture";
import { Card } from "@/components/ui/card";

export default function AgentRuntimePage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="AI Agent Security Runtime"
        title="Containment, policies, and reasoning-chain auditability"
        description="Observe autonomous sessions, permissions, tool usage, and unsafe execution attempts. Enforce runtime policies and isolate compromised behaviors."
      />

      <div className="grid gap-4 md:grid-cols-12">
        <div className="md:col-span-7">
          <RuntimePosture />
        </div>
        <Card className="md:col-span-5 border-border bg-card/70 backdrop-blur">
          <div className="p-5">
            <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Reasoning flow graph
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              (Next) Render live reasoning chains and inter-agent communication
              as a navigable graph, with redaction-aware audit trails and policy
              violations.
            </div>
          </div>
        </Card>

        <Card className="md:col-span-12 border-border bg-card/70 backdrop-blur">
          <div className="p-5">
            <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Execution audit trails
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              (Next) Per-session tool calls, permission grants, containment
              actions, and rollback decisions with immutable provenance.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

