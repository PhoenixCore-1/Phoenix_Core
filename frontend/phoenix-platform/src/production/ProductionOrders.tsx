import { useEffect, useState } from 'react'
import {
  createProductionOrder,
  getProductionOperationalSnapshot,
  releaseProductionOrder,
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

  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null)
  const [releasing, setReleasing] = useState(false)
  const [releaseError, setReleaseError] = useState<string | null>(null)
  const [releaseSuccess, setReleaseSuccess] = useState<string | null>(null)

  const [orderNumber, setOrderNumber] = useState('')
  const [purpose, setPurpose] = useState('Customer production')
  const [productRef, setProductRef] = useState('')
  const [productDescription, setProductDescription] = useState('')
  const [quantity, setQuantity] = useState('')
  const [priority, setPriority] = useState('Normal')
  const [requiredDate, setRequiredDate] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createSuccess, setCreateSuccess] = useState<string | null>(null)

  const selectedOrder =
    orders.find(
      (order) => order.production_order_id === selectedOrderId,
    ) ?? null

  async function loadOrders() {
    setLoading(true)
    setError(null)

    try {
      const snapshot = await getProductionOperationalSnapshot()
      setOrders(snapshot.orders)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load production orders.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateOrder(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setCreating(true)
    setCreateError(null)
    setCreateSuccess(null)

    try {
      const created = await createProductionOrder({
        order_number: orderNumber.trim(),
        purpose: purpose.trim(),
        product_ref: productRef.trim(),
        product_description:
          productDescription.trim() || undefined,
        quantity_ordered: Number(quantity),
        priority,
        required_date: requiredDate || undefined,
      })

      setCreateSuccess(
        `Production order ${created.order_number} created successfully.`,
      )

      setOrderNumber('')
      setProductRef('')
      setProductDescription('')
      setQuantity('')
      setRequiredDate('')

      await loadOrders()
    } catch (err) {
      setCreateError(
        err instanceof Error
          ? err.message
          : 'Unable to create production order.',
      )
    } finally {
      setCreating(false)
    }
  }

  async function handleReleaseOrder() {
    if (!selectedOrder) {
      return
    }

    if (selectedOrder.status !== 'PLANNED') {
      setReleaseError(
        `Order ${selectedOrder.order_number} cannot be released from status ${selectedOrder.status}.`,
      )
      return
    }

    setReleasing(true)
    setReleaseError(null)
    setReleaseSuccess(null)

    try {
      const released = await releaseProductionOrder(
        selectedOrder.production_order_id,
      )

      setReleaseSuccess(
        `Production order ${selectedOrder.order_number} released successfully.`,
      )

      setOrders((currentOrders) =>
        currentOrders.map((order) =>
          order.production_order_id === released.production_order_id
            ? {
                ...order,
                status: released.status,
              }
            : order,
        ),
      )
    } catch (err) {
      setReleaseError(
        err instanceof Error
          ? err.message
          : 'Unable to release production order.',
      )
    } finally {
      setReleasing(false)
    }
  }

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

        <div className="production-order-create">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">NEW PRODUCTION ORDER</span>
              <h3>Create Production Order</h3>
            </div>
          </div>

          <form onSubmit={handleCreateOrder} className="production-order-form">
            <div className="form-grid">

              <label>
                <span>Purpose</span>
                <input
                  value={purpose}
                  onChange={(event) => setPurpose(event.target.value)}
                  required
                />
              </label>

              <label>
                <span>Product / Item</span>
                <input
                  value={productRef}
                  onChange={(event) => setProductRef(event.target.value)}
                  placeholder="PRODUCT-001"
                  required
                />
              </label>

              <label>
                <span>Product Description</span>
                <input
                  value={productDescription}
                  onChange={(event) =>
                    setProductDescription(event.target.value)
                  }
                />
              </label>

              <label>
                <span>Quantity</span>
                <input
                  type="number"
                  min="0.01"
                  step="any"
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value)}
                  required
                />
              </label>

              <label>
                <span>Priority</span>
                <select
                  value={priority}
                  onChange={(event) => setPriority(event.target.value)}
                >
                  <option value="Normal">Normal</option>
                  <option value="High">High</option>
                  <option value="Urgent">Urgent</option>
                </select>
              </label>

              <label>
                <span>Required Date</span>
                <input
                  type="date"
                  value={requiredDate}
                  onChange={(event) => setRequiredDate(event.target.value)}
                />
              </label>
            </div>

            {createError ? (
              <p className="form-error">{createError}</p>
            ) : null}

            {createSuccess ? (
              <p className="form-success">{createSuccess}</p>
            ) : null}

            <button
              type="submit"
              className="button button-primary"
              disabled={creating}
            >
              {creating ? 'Creating...' : 'Create Production Order'}
            </button>
          </form>
        </div>

        {selectedOrder ? (
          <div className="production-order-details">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">ORDER DETAILS</span>
                <h3>{selectedOrder.order_number}</h3>
              </div>

              <span className="production-order-status">
                {selectedOrder.status}
              </span>
            </div>

            <div className="production-order-detail-grid">
              <div>
                <span>Planned Quantity</span>
                <strong>
                  {formatQuantity(selectedOrder.planned_quantity)}
                </strong>
              </div>

              <div>
                <span>Required Date</span>
                <strong>
                  {formatDate(selectedOrder.required_date)}
                </strong>
              </div>

              <div>
                <span>Planned ETA</span>
                <strong>
                  {formatDate(selectedOrder.eta.planned_eta)}
                </strong>
              </div>

              <div>
                <span>Current ETA</span>
                <strong>
                  {formatDate(selectedOrder.eta.current_eta)}
                </strong>
              </div>

              <div>
                <span>Risk</span>
                <strong>
                  {riskLabel(
                    selectedOrder.eta.schedule_risk ??
                      selectedOrder.eta.required_date_risk,
                  )}
                </strong>
              </div>

              <div>
                <span>Active Holds</span>
                <strong>
                  {selectedOrder.active_hold_count}
                </strong>
              </div>
            </div>

            {selectedOrder.eta.summary ? (
              <div className="production-order-detail-summary">
                <span>ETA Summary</span>
                <p>{selectedOrder.eta.summary}</p>
              </div>
            ) : null}

            {selectedOrder.eta.decision ? (
              <div className="production-order-detail-summary">
                <span>Decision</span>
                <p>{selectedOrder.eta.decision}</p>
              </div>
            ) : null}

            {releaseError ? (
              <p className="form-error">{releaseError}</p>
            ) : null}

            {releaseSuccess ? (
              <p className="form-success">{releaseSuccess}</p>
            ) : null}

            <div className="production-order-detail-actions">
              {selectedOrder.status === 'PLANNED' ? (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={handleReleaseOrder}
                  disabled={releasing}
                >
                  {releasing ? 'Releasing...' : 'Release Order'}
                </button>
              ) : null}
            </div>
          </div>
        ) : null}

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

              return (
                <div
                  className={`data-table-row ${
                    selectedOrderId === order.production_order_id
                      ? 'production-order-row-selected'
                      : ''
                  }`}
                  key={order.production_order_id}
                  role="button"
                  tabIndex={0}
                  aria-label={`View details for ${order.order_number}`}
                  onClick={() => {
                    setSelectedOrderId(order.production_order_id)
                    setReleaseError(null)
                    setReleaseSuccess(null)
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      setSelectedOrderId(order.production_order_id)
                      setReleaseError(null)
                      setReleaseSuccess(null)
                    }
                  }}
                >
                  <span>
                    <strong>
                      {order.order_number}
                    </strong>



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



