import {
  NavLink,
  Navigate,
  Outlet,
} from 'react-router'

import { usePlatformContext } from '../core/platform/PlatformContext'

export function ProductionShell() {
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
    <section className="production-shell">
      <div className="production-module-header">
        <div>
          <span className="eyebrow">
            PRODUCTION MODULE
          </span>

          <h1>Production 360</h1>

          <p className="muted">
            Production operations and performance workspace.
          </p>
        </div>

        <NavLink
          className="button secondary"
          to="/user"
        >
          Back to User Platform
        </NavLink>
      </div>

      <nav className="production-module-nav" aria-label="Production navigation">
        <NavLink end to="/user/production">
          Overview
        </NavLink>

        <NavLink to="/user/production/performance">
          Performance
        </NavLink>

        <NavLink to="/user/production/orders">
          Orders
        </NavLink>

        <NavLink to="/user/production/eta-risk">
          ETA &amp; Risk
        </NavLink>

        <NavLink to="/user/production/holds">
          Holds
        </NavLink>
      </nav>

      <Outlet />
    </section>
  )
}
