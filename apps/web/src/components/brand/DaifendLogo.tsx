"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "symbol" | "lockup";

export function DaifendLogo({
  variant = "lockup",
  className,
  title = "Daifend",
}: {
  variant?: Variant;
  className?: string;
  title?: string;
}) {
  // Uses the provided SVG geometry; background is transparent so it inherits the UI surface.
  if (variant === "symbol") {
    return (
      <svg
        viewBox="0 0 120 120"
        width="32"
        height="32"
        role="img"
        aria-label={title}
        className={cn("shrink-0", className)}
      >
        <g transform="translate(10,10)">
          <path
            d="M20 10V100"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <path
            d="M20 10C75 10 100 35 100 55C100 75 75 100 20 100"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <rect x="42" y="42" width="12" height="12" rx="2" fill="#9FB4FF" />
          <line
            x1="100"
            y1="55"
            x2="82"
            y2="55"
            stroke="var(--background)"
            strokeWidth="8"
          />
        </g>
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 720 180"
      role="img"
      aria-label={title}
      className={cn("w-[220px] max-w-full", className)}
    >
      <g transform="translate(40,35)">
        <path
          d="M20 10V100"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <path
          d="M20 10C75 10 100 35 100 55C100 75 75 100 20 100"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <rect x="42" y="42" width="12" height="12" rx="2" fill="#9FB4FF" />
        <line
          x1="100"
          y1="55"
          x2="82"
          y2="55"
          stroke="var(--background)"
          strokeWidth="8"
        />
      </g>

      <g fill="currentColor">
        <text
          x="180"
          y="82"
          fontFamily="var(--font-sans), Inter, Helvetica, Arial, sans-serif"
          fontSize="56"
          letterSpacing="10"
          fontWeight="300"
        >
          DAIFEND
        </text>
      </g>
      <text
        x="182"
        y="122"
        fontFamily="var(--font-sans), Inter, Helvetica, Arial, sans-serif"
        fontSize="18"
        letterSpacing="6"
        fill="rgba(160,174,192,0.9)"
        fontWeight="300"
      >
        SECURING THE AI RUNTIME
      </text>
    </svg>
  );
}

