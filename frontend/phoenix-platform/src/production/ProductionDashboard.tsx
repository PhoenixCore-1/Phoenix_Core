import { useEffect, useState } from 'react'
import {
  getProductionOperationalSnapshot,
  type ProductionOperationalSnapshot,
} from './api/production'

function formatNumber(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat().format(Number(value))
}

function formatPercent(value: string | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return `${(Number(value) * 100).toFixed(1)}%`
}

function formatSeconds(value: string | null | undefined): string {
  if (value === null || value === undefined) return '-'

  const minutes = Math.round(Number(value) / 60)

  if (minutes < 60) {
    return `${minutes} min`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  return remainingMinutes
    ? `${hours}h ${remainingMinutes}m`
    : `${hours}h`
}

export function ProductionDashboard() {
  const [snapshot, setSnapshot] =
    useState<ProductionOperationalSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setLoading(true)
        setError(null)

        const result = await getProductionOperationalSnapshot()

        if (!cancelled) {
          setSnapshot(result)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load production data.',
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
      <section className="production-dashboard">
        <p>Loading production operations...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className="production-dashboard">
        <div className="production-error">
          <strong>Production data unavailable</strong>
          <p>{error}</p>
        </div>
      </section>
    )
  }

  if (!snapshot) {
    return (
      <section className="production-dashboard">
        <p>No production operational data is available.</p>
      </section>
    )
  }

  const { performance, orders } = snapshot

  const attentionOrders = orders.filter(
    (order) =>
      order.eta.action_required ||
      Boolean(order.eta.schedule_risk) ||
      Boolean(order.eta.required_date_risk) ||
      order.active_hold_count > 0,
  )

  return (
    <section className="production-dashboard">
      <div className="production-kpi-grid">
        <article className="production-kpi-card">
          <span>Orders</span>
          <strong>{formatNumber(performance.order_count)}</strong>
        </article>

        <article className="production-kpi-card">
          <span>Completion</span>
          <strong>{formatPercent(performance.completion_ratio)}</strong>
        </article>

        <article className="production-kpi-card">
          <span>Planned Quantity</span>
          <strong>{formatNumber(performance.planned_quantity)}</strong>
        </article>

        <article className="production-kpi-card">
          <span>Actual Quantity</span>
          <strong>{formatNumber(performance.actual_quantity)}</strong>
        </article>
      </div>

      <div className="production-panel-grid">
        <article className="production-panel">
          <div className="production-panel-header">
            <div>
              <span className="production-eyebrow">Performance</span>
              <h2>Production performance</h2>
            </div>
          </div>

          <dl className="production-stat-list">
            <div>
              <dt>Open orders</dt>
              <dd>{formatNumber(performance.open_order_count)}</dd>
            </div>

            <div>
              <dt>Completed orders</dt>
              <dd>{formatNumber(performance.completed_order_count)}</dd>
            </div>

            <div>
              <dt>Average production time</dt>
              <dd>
                {formatSeconds(performance.average_production_seconds)}
              </dd>
            </div>

            <div>
              <dt>Average actual rate</dt>
              <dd>{formatNumber(performance.average_actual_rate)}</dd>
            </div>
          </dl>
        </article>

        <article className="production-panel">
          <div className="production-panel-header">
            <div>
              <span className="production-eyebrow">Attention</span>
              <h2>Orders requiring action</h2>
            </div>

            <strong>{attentionOrders.length}</strong>
          </div>

          {attentionOrders.length === 0 ? (
            <p className="production-empty">
              No orders currently require attention.
            </p>
          ) : (
            <div className="production-order-list">
              {attentionOrders.slice(0, 8).map((order) => (
                <div
                  className="production-order-row"
                  key={order.production_order_id}
                >
                  <div>
                    <strong>
                      Order {order.production_order_id}
                    </strong>

                    <span>
                      {order.eta.summary ??
                        'Operational attention required'}
                    </span>
                  </div>

                  <div className="production-order-meta">
                    {order.active_hold_count > 0
                      ? `${order.active_hold_count} hold${order.active_hold_count === 1 ? '' : 's'}`
                      : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  )
}
