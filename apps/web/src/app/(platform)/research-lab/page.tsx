import { PageHeader } from "@/components/page/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const tracks = [
  {
    title: "AI Memory Poisoning Research",
    desc: "Attack patterns for embedding corruption, semantic drift, and long-term memory manipulation.",
    tag: "Integrity",
  },
  {
    title: "Autonomous AI Threats",
    desc: "Agent-to-agent escalation, tool misuse, stealth reasoning pivots, and policy evasion.",
    tag: "Runtime",
  },
  {
    title: "Semantic Manipulation Analysis",
    desc: "Persuasion and context steering detection across multi-turn instruction hierarchies.",
    tag: "Cognitive",
  },
  {
    title: "AI Malware DNA Sequencing",
    desc: "Signature families and mutation trees for AI-native payloads and prompt-borne malware.",
    tag: "Threat Intel",
  },
  {
    title: "Synthetic Identity Detection",
    desc: "Session spoofing, identity drift, and synthetic persona correlation within agent runtimes.",
    tag: "Identity",
  },
];

export default function ResearchLabPage() {
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Research Lab"
        title="R&D for AI-native security threats"
        description="Futuristic, technical research surfaces: whitepapers, simulations, and signature timelines that feed detection + response."
        right={
          <Badge className="border border-[rgba(159,180,255,0.25)] bg-[rgba(159,180,255,0.10)] text-foreground/90">
            Lab: active
          </Badge>
        }
      />

      <div className="grid gap-4 md:grid-cols-12">
        {tracks.map((t, i) => (
          <Card
            key={t.title}
            className="md:col-span-4 border-border bg-card/70 backdrop-blur"
          >
            <div className="p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="font-[var(--font-display)] text-sm tracking-[-0.02em]">
                  {t.title}
                </div>
                <span className="rounded-full border border-border bg-[rgba(255,255,255,0.02)] px-2 py-0.5 text-[10px] tracking-[0.14em] text-muted-foreground">
                  {t.tag.toUpperCase()}
                </span>
              </div>
              <div className="mt-2 text-sm text-muted-foreground">{t.desc}</div>
              <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
                <div
                  className="h-full rounded-full bg-[linear-gradient(90deg,rgba(159,180,255,0.20),rgba(159,180,255,0.65),rgba(93,214,161,0.35))]"
                  style={{ width: `${65 + ((i * 13) % 26)}%` }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

