import { api } from '../../core/api/client'

export interface ProductionPerformance {
  organisation_id: string
  order_count: number
  open_order_count: number
  completed_order_count: number
  planned_quantity: string
  actual_quantity: string
  completion_ratio: string
  total_production_seconds: string
  average_production_seconds: string | null
  average_actual_rate: string | null
}

export interface ProductionEtaSnapshot {
  production_order_id: number
  planned_eta: string | null
  current_eta: string | null
  required_date: string | null
  schedule_risk: string | null
  required_date_risk: string | null
  decision: string | null
  action_required: boolean
  summary: string | null
}

export interface ProductionOrder {
  production_order_id: number
  status: string
  planned_quantity: string
  required_date: string | null
  eta: ProductionEtaSnapshot
  active_hold_count: number
}

export interface ProductionOperationalSnapshot {
  organisation_id: string
  performance: ProductionPerformance
  orders: ProductionOrder[]
  order_count: number
}

export async function getProductionOperationalSnapshot(
  startAt?: string,
  endAt?: string,
): Promise<ProductionOperationalSnapshot> {
  const params = new URLSearchParams()

  if (startAt) params.set('start_at', startAt)
  if (endAt) params.set('end_at', endAt)

  const query = params.toString()
  const path = `/api/v1/production/operational-snapshot${query ? `?${query}` : ''}`

  return api<ProductionOperationalSnapshot>(path)
}

