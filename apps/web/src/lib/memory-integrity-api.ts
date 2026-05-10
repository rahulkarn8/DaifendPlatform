const GATEWAY =
  process.env.NEXT_PUBLIC_DAIFEND_GATEWAY ?? "http://127.0.0.1:8080";

export type MemoryReport = {
  id: string;
  trustScore: number;
  integrityScore: number;
  poisoningProbability: number;
  semanticDrift: number;
  fingerprint: string;
  detail: Record<string, unknown>;
  createdAt: string | null;
};

function headers(tenantId: string, token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "X-Tenant-Id": tenantId,
    "Content-Type": "application/json",
  };
}

export async function fetchMemoryReports(
  tenantId: string,
  token: string,
  limit = 10,
): Promise<MemoryReport[]> {
  const r = await fetch(
    `${GATEWAY}/v1/memory-integrity/reports?limit=${limit}`,
    { headers: headers(tenantId, token), cache: "no-store" },
  );
  if (!r.ok) throw new Error(`reports ${r.status}`);
  const data = (await r.json()) as { reports: MemoryReport[] };
  return data.reports ?? [];
}

export async function fetchMemoryFeed(
  tenantId: string,
  token: string,
  since?: number,
): Promise<{ events: Array<Record<string, unknown> & { ts?: number }> }> {
  const q = since != null ? `?since=${since}` : "";
  const r = await fetch(`${GATEWAY}/v1/memory-integrity/feed${q}`, {
    headers: headers(tenantId, token),
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`feed ${r.status}`);
  return r.json();
}

export async function startMemoryScan(
  tenantId: string,
  token: string,
  body: {
    vectorBackend: string;
    collection: string;
    limit?: number;
    namespace?: string;
    baselineSnapshotId?: string;
    persistBaseline?: boolean;
  },
): Promise<{ scanId: string; status: string }> {
  const r = await fetch(`${GATEWAY}/v1/memory-integrity/scan/start`, {
    method: "POST",
    headers: headers(tenantId, token),
    body: JSON.stringify({
      tenantId,
      vectorBackend: body.vectorBackend,
      collection: body.collection,
      limit: body.limit ?? 256,
      namespace: body.namespace,
      baselineSnapshotId: body.baselineSnapshotId,
      persistBaseline: body.persistBaseline ?? false,
    }),
  });
  if (!r.ok) throw new Error(`scan start ${r.status}`);
  return r.json();
}
