import { z } from "zod";

export const webPublicEnvSchema = z.object({
  NEXT_PUBLIC_DAIFEND_MODE: z.enum(["demo", "live"]).default("demo"),
  NEXT_PUBLIC_API_GATEWAY_URL: z.string().url().optional(),
  NEXT_PUBLIC_TELEMETRY_URL: z.string().url().optional(),
});

export type WebPublicEnv = z.infer<typeof webPublicEnvSchema>;

export function parseWebPublicEnv(
  env: Record<string, string | undefined>,
): WebPublicEnv {
  return webPublicEnvSchema.parse({
    NEXT_PUBLIC_DAIFEND_MODE: env.NEXT_PUBLIC_DAIFEND_MODE,
    NEXT_PUBLIC_API_GATEWAY_URL: env.NEXT_PUBLIC_API_GATEWAY_URL,
    NEXT_PUBLIC_TELEMETRY_URL: env.NEXT_PUBLIC_TELEMETRY_URL,
  });
}
