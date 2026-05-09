"use client";

import { useTelemetry } from "@/hooks/useTelemetry";
import { DashboardGrid } from "@/components/dashboard/DashboardGrid";

export function DashboardClient() {
  useTelemetry();

  return (
    <DashboardGrid />
  );
}

