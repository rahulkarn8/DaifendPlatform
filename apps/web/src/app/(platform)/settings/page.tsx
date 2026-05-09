import { PageHeader } from "@/components/page/PageHeader";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";

export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Settings"
        title="Platform configuration"
        description="Runtime policies, telemetry endpoints, and workspace preferences."
      />

      <Card className="border-border bg-card/70 backdrop-blur">
        <div className="p-5">
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            Workspace
          </div>

          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-sm">Strict containment mode</div>
                <div className="text-xs text-muted-foreground">
                  Enforce high-sensitivity policies for agent tools and memory
                  writes.
                </div>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator className="opacity-60" />
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-sm">Adaptive UI theme</div>
                <div className="text-xs text-muted-foreground">
                  Allow system theme switching (dark recommended).
                </div>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

