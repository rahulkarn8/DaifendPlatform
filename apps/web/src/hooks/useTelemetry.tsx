"use client";

import * as React from "react";
import { useTelemetryStore } from "@/store/telemetryStore";

export function useTelemetry() {
  const status = useTelemetryStore((s) => s.status);
  const derived = useTelemetryStore((s) => s.derived);
  const connect = useTelemetryStore((s) => s.connect);

  React.useEffect(() => {
    connect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { status, derived };
}

