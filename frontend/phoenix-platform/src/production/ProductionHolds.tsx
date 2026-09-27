import { useEffect, useState } from 'react'
import {
  getProductionOperationalSnapshot,
  type ProductionOrder,
} from './api/production'

export function ProductionHolds() {
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
              : 'Unable to load production holds.',
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
          <p className="muted">Loading production holds...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="dashboard-sections">
        <div className="panel">
          <strong>Hold data unavailable</strong>
          <p className="muted">{error}</p>
        </div>
      </section>
    )
  }

  const heldOrders = orders.filter(
    (order) => order.active_hold_count > 0,
  )

  const totalHolds = heldOrders.reduce(
    (total, order) => total + order.active_hold_count,
    0,
  )

  return (
    <section className="dashboard-sections">
      <article className="panel dashboard-panel-wide">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">PRODUCTION HOLDS</span>
            <h3>Active production holds</h3>
          </div>

          <strong>{totalHolds}</strong>
        </div>

        {heldOrders.length === 0 ? (
          <p className="muted">
            No active production holds are currently reported.
          </p>
        ) : (
          <>
            <div className="data-table">
              <div className="data-table-row data-table-header">
                <span>Order</span>
                <span>Status</span>
                <span>Active Holds</span>
                <span>Required Date</span>
                <span>Current ETA</span>
                <span>ETA Decision</span>
              </div>

              {heldOrders.map((order) => (
                <div
                  className="data-table-row"
                  key={order.production_order_id}
                >
                  <span>
                    <strong>{order.production_order_id}</strong>
                    <small>Operational hold</small>
                  </span>

                  <span>{order.status}</span>

                  <span>{order.active_hold_count}</span>

                  <span>
                    {order.required_date
                      ? new Date(
                          order.required_date,
                        ).toLocaleDateString()
                      : '-'}
                  </span>

                  <span>
                    {order.eta.current_eta
                      ? new Date(
                          order.eta.current_eta,
                        ).toLocaleDateString()
                      : '-'}
                  </span>

                  <span>
                    {order.eta.decision ?? '-'}
                  </span>
                </div>
              ))}
            </div>

            <div className="dashboard-panel" style={{ marginTop: '1rem' }}>
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">OPERATIONAL CONTEXT</span>
                  <h3>Held order context</h3>
                </div>
              </div>

              {heldOrders.map((order) => (
                <div
                  className="status-row"
                  key={`hold-context-${order.production_order_id}`}
                >
                  <span>
                    <strong>
                      Order {order.production_order_id}
                    </strong>
                    <br />
                    {order.eta.summary ??
                      'No additional operational summary available.'}
                  </span>

                  <strong>
                    {order.active_hold_count} hold
                    {order.active_hold_count === 1 ? '' : 's'}
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
