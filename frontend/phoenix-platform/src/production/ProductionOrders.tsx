import { useEffect, useState } from 'react'
import {
  getProductionOperationalSnapshot,
  type ProductionOrder,
} from './api/production'

function formatQuantity(value: string): string {
  return new Intl.NumberFormat().format(Number(value))
}

function formatDate(value: string | null): string {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString()
}

function riskLabel(value: string | null): string {
  if (!value) return 'None'
  return value.replace(/_/g, ' ')
}

export function ProductionOrders() {
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
              : 'Unable to load production orders.',
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
          <p className="muted">Loading production orders...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="dashboard-sections">
        <div className="panel">
          <strong>Orders unavailable</strong>
          <p className="muted">{error}</p>
        </div>
      </section>
    )
  }

  return (
    <section className="dashboard-sections">
      <article className="panel dashboard-panel-wide">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">PRODUCTION ORDERS</span>
            <h3>Operational order list</h3>
          </div>

          <strong>{orders.length}</strong>
        </div>

        {orders.length === 0 ? (
          <p className="muted">
            No production orders are available for the selected period.
          </p>
        ) : (
          <div className="data-table">
            <div className="data-table-row data-table-header">
              <span>Order</span>
              <span>Status</span>
              <span>Planned</span>
              <span>Required</span>
              <span>Current ETA</span>
              <span>Risk</span>
              <span>Holds</span>
            </div>

            {orders.map((order) => {
              const actionRequired =
                order.eta.action_required ||
                Boolean(order.eta.schedule_risk) ||
                Boolean(order.eta.required_date_risk) ||
                order.active_hold_count > 0

              return (
                <div
                  className="data-table-row"
                  key={order.production_order_id}
                >
                  <span>
                    <strong>
                      {order.production_order_id}
                    </strong>

                    {actionRequired ? (
                      <small>Action required</small>
                    ) : null}
                  </span>

                  <span>{order.status}</span>

                  <span>
                    {formatQuantity(order.planned_quantity)}
                  </span>

                  <span>
                    {formatDate(order.required_date)}
                  </span>

                  <span>
                    {formatDate(order.eta.current_eta)}
                  </span>

                  <span>
                    {riskLabel(
                      order.eta.schedule_risk ??
                        order.eta.required_date_risk,
                    )}
                  </span>

                  <span>
                    {order.active_hold_count}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </article>
    </section>
  )
}
