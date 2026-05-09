"use client";

import * as React from "react";
import { ThemeProvider } from "next-themes";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: false },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
    >
      <TooltipProvider delay={120}>
        {children}
      </TooltipProvider>
      <Toaster
        theme="dark"
        toastOptions={{
          style: {
            background: "rgba(14, 17, 23, 0.9)",
            border: "1px solid rgba(255,255,255,0.10)",
            color: "#F5F7FA",
          },
        }}
      />
    </ThemeProvider>
    </QueryClientProvider>
  );
}

