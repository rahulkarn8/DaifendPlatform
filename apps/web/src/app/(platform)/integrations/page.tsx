import { PageHeader } from "@/components/page/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const integrations = [
  { name: "OpenAI", kind: "LLM", status: "connected" },
  { name: "Azure AI / Azure OpenAI", kind: "LLM", status: "available" },
  { name: "AWS Bedrock", kind: "LLM", status: "available" },
  { name: "Anthropic", kind: "LLM", status: "available" },
  { name: "Pinecone", kind: "Vector DB", status: "available" },
  { name: "Weaviate", kind: "Vector DB", status: "available" },
  { name: "LangChain", kind: "RAG", status: "available" },
  { name: "Kubernetes", kind: "Runtime", status: "available" },
  { name: "CrowdStrike", kind: "EDR", status: "available" },
  { name: "Microsoft Sentinel", kind: "SIEM", status: "available" },
];

export default function IntegrationsPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="API Integrations"
        title="Connect your AI stack"
        description="Mock connectors for model providers, vector databases, orchestration layers, and SOC destinations. These integrations will power Architecture flows and incident enrichment."
      />

      <div className="grid gap-4 md:grid-cols-12">
        {integrations.map((i) => (
          <Card
            key={i.name}
            className="md:col-span-4 border-border bg-card/70 backdrop-blur"
          >
            <div className="p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="font-[var(--font-display)] text-sm tracking-[-0.02em]">
                  {i.name}
                </div>
                <Badge className="border border-border bg-[rgba(255,255,255,0.02)] text-muted-foreground">
                  {i.kind}
                </Badge>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="text-xs text-muted-foreground">status</div>
                <span className="rounded-full border border-[rgba(159,180,255,0.20)] bg-[rgba(159,180,255,0.10)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-foreground/90">
                  {i.status.toUpperCase()}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

