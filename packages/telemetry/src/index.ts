/** NATS / internal subject conventions — keep in sync with Python publishers */

export const TELEMETRY_SUBJECT_PREFIX = "daifend.telemetry";

export function telemetrySubject(stream: string): string {
  return `${TELEMETRY_SUBJECT_PREFIX}.${stream}`;
}

export const TELEMETRY_STREAMS = {
  raw: "raw",
  memory: "memory",
  agent: "agent",
  rag: "rag",
  threat: "threat",
  healing: "healing",
} as const;
