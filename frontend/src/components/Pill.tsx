import type { ReactNode } from "react";

import { cn } from "../lib/format";

interface PillProps {
  tone?: "neutral" | "ok" | "warn" | "bad";
  children: ReactNode;
}

export function Pill({ tone = "neutral", children }: PillProps) {
  return <span className={cn("pill", `pill--${tone}`)}>{children}</span>;
}
