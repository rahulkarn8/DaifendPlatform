import {
  Activity,
  Aperture,
  Atom,
  Cpu,
  FlaskConical,
  Layers3,
  Link2,
  Plug,
  Settings,
  ShieldAlert,
  Wrench,
} from "lucide-react";

export type NavItem = {
  key: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  section:
    | "Core"
    | "Integrity"
    | "Runtime"
    | "Response"
    | "Research"
    | "Platform";
};

export const navItems: NavItem[] = [
  { key: "dashboard", label: "Dashboard", href: "/dashboard", icon: Activity, section: "Core" },
  {
    key: "memory",
    label: "AI Memory Security",
    href: "/ai-memory-security",
    icon: Layers3,
    section: "Integrity",
  },
  {
    key: "agent-runtime",
    label: "Agent Runtime",
    href: "/agent-runtime",
    icon: Cpu,
    section: "Runtime",
  },
  {
    key: "threat-intel",
    label: "Threat Intelligence",
    href: "/threat-intelligence",
    icon: ShieldAlert,
    section: "Integrity",
  },
  { key: "incidents", label: "Incidents", href: "/incidents", icon: Aperture, section: "Response" },
  {
    key: "self-healing",
    label: "Self-Healing",
    href: "/self-healing",
    icon: Wrench,
    section: "Response",
  },
  { key: "research-lab", label: "Research Lab", href: "/research-lab", icon: FlaskConical, section: "Research" },
  { key: "simulation", label: "Attack Simulation", href: "/simulation", icon: Atom, section: "Research" },
  { key: "architecture", label: "Architecture", href: "/architecture", icon: Link2, section: "Platform" },
  { key: "integrations", label: "API Integrations", href: "/integrations", icon: Plug, section: "Platform" },
  { key: "settings", label: "Settings", href: "/settings", icon: Settings, section: "Platform" },
];

export const navSections: Array<NavItem["section"]> = [
  "Core",
  "Integrity",
  "Runtime",
  "Response",
  "Research",
  "Platform",
];

