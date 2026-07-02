interface StatTileProps {
  label: string;
  value: string | number;
  note?: string;
}

export function StatTile({ label, value, note }: StatTileProps) {
  return (
    <article className="stat-tile">
      <div className="stat-tile__label">{label}</div>
      <div className="stat-tile__value">{value}</div>
      {note ? <div className="stat-tile__note">{note}</div> : null}
    </article>
  );
}
