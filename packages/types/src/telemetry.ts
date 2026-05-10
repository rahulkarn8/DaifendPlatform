export type Severity = "low" | "medium" | "high" | "critical";
export type ThreatSurface = "rag" | "memory" | "agent" | "model" | "identity";

export type DaifendRuntimeMode = "demo" | "live";

export type TelemetryEvent =
  | {
      type: "memory.trust";
      ts: number;
      trustScore: number;
      driftScore: number;
      poisonedVectors: number;
    }
  | {
      type: "rag.integrity";
      ts: number;
      integrityScore: number;
      injectionAttempts: number;
      maliciousDocsQuarantined: number;
    }
  | {
      type: "agent.runtime";
      ts: number;
      activeAgents: number;
      unsafeToolAttempts: number;
      containmentActions: number;
    }
  | {
      type: "threat.attempt";
      ts: number;
      signature: string;
      severity: Severity;
      surface: ThreatSurface;
    }
  | {
      type: "healing.action";
      ts: number;
      action:
        | "isolate_vector_segment"
        | "rollback_memory"
        | "invalidate_embeddings"
        | "rotate_agent_session"
        | "restore_trust_baseline";
      incidentId: string;
      progress: number;
    }
  | {
      type: "memory.integrity.report";
      ts: number;
      trustScore: number;
      driftScore: number;
      poisonedVectors: number;
      reportId?: string;
    };

export type TelemetryHello = {
  serverTime: number;
  streams: string[];
  mode: "mock" | "live" | "demo" | "enterprise";
  tenantId?: string;
};

export type TelemetryDerived = {
  memoryTrustScore: number;
  semanticDriftScore: number;
  poisonedVectors: number;
  ragIntegrityScore: number;
  injectionAttempts: number;
  maliciousDocsQuarantined: number;
  activeAgents: number;
  unsafeToolAttempts: number;
  containmentActions: number;
  attackAttempts: number;
  lastThreat?: {
    ts: number;
    signature: string;
    severity: Severity;
    surface: ThreatSurface;
  };
  lastHealing?: {
    ts: number;
    action: Extract<TelemetryEvent, { type: "healing.action" }>;
  };
};
