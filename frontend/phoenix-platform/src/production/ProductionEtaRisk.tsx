import { useEffect, useState } from 'react'
import {
  getProductionOperationalSnapshot,
  type ProductionOrder,
} from './api/production'

function formatDate(value: string | null): string {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString()
}

function formatRisk(value: string | null): string {
  if (!value) return 'None'
  return value.replace(/_/g, ' ')
}

function riskClass(value: string | null): string {
  if (!value) return 'risk-none'

  const normalized = value.toLowerCase()

  if (
    normalized.includes('critical') ||
    normalized.includes('high') ||
    normalized.includes('late')
  ) {
    return 'risk-high'
  }

  if (
    normalized.includes('medium') ||
    normalized.includes('warning') ||
    normalized.includes('at_risk')
  ) {
    return 'risk-medium'
  }

  return 'risk-low'
}

function EtaRiskRow({ order }: { order: ProductionOrder }) {
  const { eta } = order

  return (
    <div className="data-table-row">
      <span>
        <strong>{order.production_order_id}</strong>
        {eta.action_required ? (
          <small>Action required</small>
        ) : null}
      </span>

      <span>{formatDate(eta.planned_eta)}</span>

      <span>{formatDate(eta.current_eta)}</span>

      <span>{formatDate(eta.required_date)}</span>

      <span className={riskClass(eta.schedule_risk)}>
        {formatRisk(eta.schedule_risk)}
      </span>

      <span className={riskClass(eta.required_date_risk)}>
        {formatRisk(eta.required_date_risk)}
      </span>

      <span>{eta.decision ?? '-'}</span>
    </div>
  )
}

export function ProductionEtaRisk() {
  const [orders, setOrders] = useState<ProductionOrder[]>([])
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
          setOrders(snapshot.orders)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load ETA and risk data.',
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
          <p className="muted">Loading ETA and risk data...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="dashboard-sections">
        <div className="panel">
          <strong>ETA and risk data unavailable</strong>
          <p className="muted">{error}</p>
        </div>
      </section>
    )
  }

  const attentionCount = orders.filter(
    (order) =>
      order.eta.action_required ||
      Boolean(order.eta.schedule_risk) ||
      Boolean(order.eta.required_date_risk),
  ).length

  return (
    <section className="dashboard-sections">
      <article className="panel dashboard-panel-wide">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">ETA &amp; RISK</span>
            <h3>Production delivery risk</h3>
          </div>

          <strong>{attentionCount}</strong>
        </div>

        {orders.length === 0 ? (
          <p className="muted">
            No production orders are available for ETA assessment.
          </p>
        ) : (
          <>
            <div className="data-table">
              <div className="data-table-row data-table-header">
                <span>Order</span>
                <span>Planned ETA</span>
                <span>Current ETA</span>
                <span>Required Date</span>
                <span>Schedule Risk</span>
                <span>Date Risk</span>
                <span>Decision</span>
              </div>

              {orders.map((order) => (
                <EtaRiskRow
                  key={order.production_order_id}
                  order={order}
                />
              ))}
            </div>

            <div className="dashboard-panel" style={{ marginTop: '1rem' }}>
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">DECISION CONTEXT</span>
                  <h3>Operational summaries</h3>
                </div>
              </div>

              {orders.map((order) => (
                <div
                  className="status-row"
                  key={`summary-${order.production_order_id}`}
                >
                  <span>
                    <strong>
                      Order {order.production_order_id}
                    </strong>
                    <br />
                    {order.eta.summary ?? 'No operational summary available.'}
                  </span>

                  <strong>
                    {order.eta.action_required
                      ? 'Action required'
                      : 'Monitor'}
                  </strong>
                </div>
              ))}
            </div>
          </>
        )}
      </article>
    </section>
  )
}
