/** API contract types shared with OpenAPI / SDK */

export type TenantContext = {
  tenantId: string;
  orgId: string;
};

export type MemoryIntegrityAnalyzeRequest = {
  tenantId: string;
  embeddings: number[][];
  baselineCentroid?: number[] | null;
  textSamples?: string[];
  collectionId?: string;
};

export type MemoryIntegrityAnalyzeResponse = {
  trustScore: number;
  semanticDrift: number;
  poisonedClusterRisk: number;
  anomalousIndices: number[];
  promptInjectionSignals: Array<{ sampleIndex: number; score: number; reasons: string[] }>;
  fingerprint: string;
  recommendedActions: string[];
};

export type AgentActionValidateRequest = {
  tenantId: string;
  agentId: string;
  toolName: string;
  arguments: Record<string, unknown>;
  reasoningStep?: string;
};

export type AgentActionValidateResponse = {
  allowed: boolean;
  violations: string[];
  containment: "none" | "soft_block" | "hard_block" | "session_rotate";
};

export type RagDocumentScanRequest = {
  tenantId: string;
  documentId: string;
  chunks: string[];
  embeddingDim?: number;
};

export type RagDocumentScanResponse = {
  integrityScore: number;
  poisoningLikelihood: number;
  unsafeContexts: Array<{ chunkIndex: number; reason: string }>;
};

export type SelfHealingWorkflowRequest = {
  tenantId: string;
  incidentId: string;
  actions: Array<
    | "rollback_memory"
    | "invalidate_embeddings"
    | "restore_trust_baseline"
    | "rotate_agent_session"
  >;
};

export type SelfHealingWorkflowResponse = {
  workflowId: string;
  status: "queued" | "running" | "completed" | "failed";
  steps: Array<{ name: string; status: string }>;
};
