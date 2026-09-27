import { Navigate } from 'react-router'
import { usePlatformContext } from '../core/platform/PlatformContext'
import { ProductionDashboard } from './ProductionDashboard'

export function Production360Entry() {
  const { context } = usePlatformContext()

  if (!context) {
    return null
  }

  const productionModule = context.modules.find(
    (module) =>
      module.code === 'production' &&
      module.active === true,
  )

  const canUseProduction =
    productionModule !== undefined &&
    context.entitlements?.includes('production') === true &&
    context.permissions?.includes('production.view') === true

  if (!canUseProduction) {
    return <Navigate to="/user" replace />
  }

  return (
    <>
      <div className="dashboard-heading">
        <span className="eyebrow">
          PRODUCTION MODULE
        </span>

        <h1>
          Production 360
        </h1>

        <p className="muted">
          Production operations and performance workspace.
        </p>
      </div>

      <ProductionDashboard />
    </>
  )
}
