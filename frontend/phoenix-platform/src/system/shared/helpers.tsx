export type KpiCardProps = {
  value: string | number
  label: string
  secondary?: string
  onClick: () => void
  disabled?: boolean
}

export function KpiCard({
  value,
  label,
  secondary,
  onClick,
  disabled = false,
}: KpiCardProps) {
  return (
    <button
      type="button"
      className={`kpi-card ${disabled ? 'disabled' : ''}`}
      onClick={onClick}
      disabled={disabled}
    >
      <span className="kpi-label">
        {label}
      </span>

      <strong className="kpi-value">
        {value}
      </strong>

      {secondary && (
        <span className="kpi-secondary">
          {secondary}
        </span>
      )}

      {!disabled && (
        <span className="kpi-drill">
          View details ?
        </span>
      )}
    </button>
  )
}

export function getGreeting(displayName: string) {
  const hour = new Date().getHours()

  if (hour < 12) {
    return `Good morning, ${displayName}`
  }

  if (hour < 18) {
    return `Good afternoon, ${displayName}`
  }

  return `Good evening, ${displayName}`
}
