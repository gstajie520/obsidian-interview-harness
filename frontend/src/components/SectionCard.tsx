import type { ReactNode } from "react";

import { cn } from "../lib/format";

interface SectionCardProps {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  tone?: "default" | "ink" | "signal";
  children: ReactNode;
}

export function SectionCard({
  eyebrow,
  title,
  description,
  action,
  tone = "default",
  children,
}: SectionCardProps) {
  return (
    <section className={cn("section-card", `section-card--${tone}`)}>
      <header className="section-card__header">
        <div>
          {eyebrow ? <div className="section-card__eyebrow">{eyebrow}</div> : null}
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
        {action ? <div className="section-card__action">{action}</div> : null}
      </header>
      {children}
    </section>
  );
}
