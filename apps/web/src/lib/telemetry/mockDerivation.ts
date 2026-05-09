import type { TelemetryDerived, TelemetryEvent } from "@/types/telemetry";

export function initialDerived(): TelemetryDerived {
  return {
    memoryTrustScore: 94.1,
    semanticDriftScore: 0.08,
    poisonedVectors: 0,
    ragIntegrityScore: 96.4,
    injectionAttempts: 0,
    maliciousDocsQuarantined: 0,
    activeAgents: 7,
    unsafeToolAttempts: 0,
    containmentActions: 0,
    attackAttempts: 0,
  };
}

export function deriveFromBatch(
  prev: TelemetryDerived,
  batch: TelemetryEvent[],
): TelemetryDerived {
  const next = { ...prev };
  for (const evt of batch) {
    switch (evt.type) {
      case "memory.trust":
        next.memoryTrustScore = evt.trustScore;
        next.semanticDriftScore = evt.driftScore;
        next.poisonedVectors = evt.poisonedVectors;
        break;
      case "rag.integrity":
        next.ragIntegrityScore = evt.integrityScore;
        next.injectionAttempts = evt.injectionAttempts;
        next.maliciousDocsQuarantined = evt.maliciousDocsQuarantined;
        break;
      case "agent.runtime":
        next.activeAgents = evt.activeAgents;
        next.unsafeToolAttempts = evt.unsafeToolAttempts;
        next.containmentActions = evt.containmentActions;
        break;
      case "threat.attempt":
        next.attackAttempts += 1;
        next.lastThreat = {
          ts: evt.ts,
          signature: evt.signature,
          severity: evt.severity,
          surface: evt.surface,
        };
        break;
      case "healing.action":
        next.lastHealing = { ts: evt.ts, action: evt };
        break;
    }
  }
  return next;
}

