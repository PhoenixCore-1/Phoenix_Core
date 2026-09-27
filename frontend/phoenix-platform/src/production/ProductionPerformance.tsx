import { useEffect, useState } from 'react'
import {
  getProductionOperationalSnapshot,
  type ProductionPerformance,
} from './api/production'

function formatNumber(value: string | number | null): string {
  if (value === null) return '-'

  return new Intl.NumberFormat().format(Number(value))
}

function formatPercent(value: string): string {
  return `${(Number(value) * 100).toFixed(1)}%`
}

function formatDuration(seconds: string | null): string {
  if (seconds === null) return '-'

  const minutes = Math.round(Number(seconds) / 60)

  if (minutes < 60) {
    return `${minutes} min`
  }

  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60

  return remaining
    ? `${hours}h ${remaining}m`
    : `${hours}h`
}

export function ProductionPerformance() {
  const [performance, setPerformance] =
    useState<ProductionPerformance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setLoading(true)
        setError(null)

        const snapshot = await getProductionOperationalSnapshot()

        if (!cancelled) {
          setPerformance(snapshot.performance)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load production performance.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <section className="dashboard-sections">
        <div className="panel">
          <p className="muted">Loading production performance...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="dashboard-sections">
        <div className="panel">
          <strong>Performance data unavailable</strong>
          <p className="muted">{error}</p>
        </div>
      </section>
    )
  }

  if (!performance) {
    return (
      <section className="dashboard-sections">
        <div className="panel">
          <p className="muted">
            No production performance data is available.
          </p>
        </div>
      </section>
    )
  }

  return (
    <>
      <div className="kpi-grid">
        <article className="kpi-card">
          <span className="kpi-label">TOTAL ORDERS</span>
          <strong className="kpi-value">
            {formatNumber(performance.order_count)}
          </strong>
          <span className="kpi-secondary">
            All production orders
          </span>
        </article>

        <article className="kpi-card">
          <span className="kpi-label">OPEN ORDERS</span>
          <strong className="kpi-value">
            {formatNumber(performance.open_order_count)}
          </strong>
          <span className="kpi-secondary">
            Currently outstanding
          </span>
        </article>

        <article className="kpi-card">
          <span className="kpi-label">COMPLETED ORDERS</span>
          <strong className="kpi-value">
            {formatNumber(performance.completed_order_count)}
          </strong>
          <span className="kpi-secondary">
            Production completed
          </span>
        </article>

        <article className="kpi-card">
          <span className="kpi-label">COMPLETION</span>
          <strong className="kpi-value">
            {formatPercent(performance.completion_ratio)}
          </strong>
          <span className="kpi-secondary">
            Actual vs planned quantity
          </span>
        </article>
      </div>

      <section className="dashboard-sections">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">QUANTITY</span>
              <h3>Planned vs actual</h3>
            </div>
          </div>

          <div className="status-row">
            <span>Planned quantity</span>
            <strong>
              {formatNumber(performance.planned_quantity)}
            </strong>
          </div>

          <div className="status-row">
            <span>Actual quantity</span>
            <strong>
              {formatNumber(performance.actual_quantity)}
            </strong>
          </div>

          <div className="status-row">
            <span>Completion ratio</span>
            <strong>
              {formatPercent(performance.completion_ratio)}
            </strong>
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">THROUGHPUT</span>
              <h3>Production timing</h3>
            </div>
          </div>

          <div className="status-row">
            <span>Total production time</span>
            <strong>
              {formatDuration(performance.total_production_seconds)}
            </strong>
          </div>

          <div className="status-row">
            <span>Average production time</span>
            <strong>
              {formatDuration(performance.average_production_seconds)}
            </strong>
          </div>

          <div className="status-row">
            <span>Average actual rate</span>
            <strong>
              {formatNumber(performance.average_actual_rate)}
            </strong>
          </div>
        </article>
      </section>
    </>
  )
}
