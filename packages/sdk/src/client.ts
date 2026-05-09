import type {
  AgentActionValidateRequest,
  AgentActionValidateResponse,
  MemoryIntegrityAnalyzeRequest,
  MemoryIntegrityAnalyzeResponse,
  RagDocumentScanRequest,
  RagDocumentScanResponse,
  SelfHealingWorkflowRequest,
  SelfHealingWorkflowResponse,
} from "@daifend/types";

export type DaifendClientOptions = {
  baseUrl: string;
  getAccessToken?: () => string | undefined;
  /** Dev / service mesh: bypass JWT when matching gateway INTERNAL_SERVICE_TOKEN */
  internalServiceToken?: string;
  tenantId?: string;
};

export class DaifendGatewayClient {
  constructor(private readonly opts: DaifendClientOptions) {}

  private async request<T>(
    path: string,
    init?: RequestInit,
  ): Promise<T> {
    const headers = new Headers(init?.headers);
    headers.set("Content-Type", "application/json");
    const token = this.opts.getAccessToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (this.opts.internalServiceToken) {
      headers.set("X-Internal-Token", this.opts.internalServiceToken);
    }
    if (this.opts.tenantId) headers.set("X-Tenant-Id", this.opts.tenantId);

    const res = await fetch(`${this.opts.baseUrl.replace(/\/$/, "")}${path}`, {
      ...init,
      headers,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Daifend API ${res.status}: ${text}`);
    }
    return (await res.json()) as T;
  }

  health() {
    return this.request<{ status: string }>("/health");
  }

  issueToken(body: {
    grantType?: string;
    clientId?: string;
    clientSecret?: string;
    tenantId: string;
  }) {
    return this.request<{
      accessToken: string;
      tokenType: string;
      expiresIn: number;
    }>("/v1/oauth/token", {
      method: "POST",
      body: JSON.stringify({
        grantType: body.grantType ?? "client_credentials",
        clientId: body.clientId,
        clientSecret: body.clientSecret,
        tenantId: body.tenantId,
      }),
    });
  }

  analyzeMemory(body: MemoryIntegrityAnalyzeRequest) {
    return this.request<MemoryIntegrityAnalyzeResponse>(
      "/v1/memory-integrity/analyze",
      { method: "POST", body: JSON.stringify(body) },
    );
  }

  validateAgentAction(body: AgentActionValidateRequest) {
    return this.request<AgentActionValidateResponse>(
      "/v1/agent-runtime/validate-action",
      { method: "POST", body: JSON.stringify(body) },
    );
  }

  scanRagDocument(body: RagDocumentScanRequest) {
    return this.request<RagDocumentScanResponse>("/v1/rag/scan-document", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  startSelfHealing(body: SelfHealingWorkflowRequest) {
    return this.request<SelfHealingWorkflowResponse>(
      "/v1/self-healing/workflows",
      { method: "POST", body: JSON.stringify(body) },
    );
  }
}
