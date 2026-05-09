/** Agent runtime policy contracts (mirrors engine JSON schema). */

export type ToolPolicy = {
  name: string;
  allowed: boolean;
  maxArgsBytes?: number;
  requiredScopes?: string[];
};

export type AgentPolicyDocument = {
  version: 1;
  agentId: string;
  tools: ToolPolicy[];
  denyPatterns?: string[];
};
