export interface Stat {
  label: string
  value: number | string | null
  hint?: string
}

export function DashboardStats({ stats }: { stats: Stat[] }) {
  return (
    <dl className="stats">
      {stats.map((s) => (
        <div key={s.label} className="stat">
          <dt className="stat__label">{s.label}</dt>
          <dd className="stat__value">{s.value ?? '—'}</dd>
          {s.hint && <dd className="stat__hint">{s.hint}</dd>}
        </div>
      ))}
    </dl>
  )
}
