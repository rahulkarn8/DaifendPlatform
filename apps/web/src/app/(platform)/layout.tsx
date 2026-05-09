import * as React from "react";
import { DaifendShell } from "@/components/shell/DaifendShell";
import { SubtleField3D } from "@/components/visual/SubtleField3D";

export default function PlatformLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SubtleField3D />
      <DaifendShell>{children}</DaifendShell>
    </>
  );
}

