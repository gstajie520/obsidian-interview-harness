interface ProgressBarProps {
  value: number;
  label: string;
}

export function ProgressBar({ value, label }: ProgressBarProps) {
  const safeValue = Math.max(0, Math.min(100, value));

  return (
    <div className="progress">
      <div className="progress__head">
        <span>{label}</span>
        <strong>{safeValue}%</strong>
      </div>
      <div className="progress__track" aria-hidden="true">
        <span className="progress__fill" style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}
