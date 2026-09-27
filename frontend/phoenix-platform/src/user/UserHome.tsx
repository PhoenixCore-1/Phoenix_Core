import { usePlatformContext } from '../core/platform/PlatformContext'

export function UserHome() {
  const { context } = usePlatformContext()

  if (!context) {
    return null
  }

  const availableModules = context.modules.filter(
    (module) =>
      module.active === true &&
      context.entitlements?.includes(module.code) === true,
  )

  return (
    <>
      <div className="dashboard-heading">
        <span className="eyebrow">
          USER PLATFORM
        </span>

        <h1>
          Welcome, {context.user.display_name}
        </h1>

        <p className="muted">
          Your Phoenix Core workspace and available business modules.
        </p>
      </div>

      <div className="dashboard-sections">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                USER
              </span>

              <h3>
                {context.user.display_name}
              </h3>
            </div>
          </div>

          <div className="status-row">
            <span>Platform level</span>
            <strong>{context.user.platform_level}</strong>
          </div>

          {context.company && (
            <div className="status-row">
              <span>Organisation</span>
              <strong>{context.company.name}</strong>
            </div>
          )}
        </div>

        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                AVAILABLE MODULES
              </span>

              <h3>
                Your business modules
              </h3>
            </div>
          </div>

          {availableModules.length === 0 ? (
            <div className="empty-state">
              <strong>No business modules are currently available.</strong>
              <p className="muted">
                Your Core administrator can enable modules for your organisation.
              </p>
            </div>
          ) : (
            availableModules.map((module) => (
              <div
                className="activity-row"
                key={module.id}
              >
                <div>
                  <strong>{module.name}</strong>
                  <span>{module.code}</span>
                </div>

                {module.code === 'production' &&
                  context.permissions?.includes('production.view') === true && (
                    <a
                      className="primary-button"
                      href="/user/production"
                    >
                      Open
                    </a>
                  )}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}
