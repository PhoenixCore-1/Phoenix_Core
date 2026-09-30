import { NavLink, Outlet } from 'react-router'
import { usePlatformContext } from '../core/platform/PlatformContext'

export function UserShell() {
  const { context, logout } = usePlatformContext()

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

  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <img
            src="/phoenix.png"
            alt="Phoenix"
          />
          <strong>PHOENIX</strong>
        </div>

        <div className="platform-title">
          USER PLATFORM
        </div>

        <nav>
          <NavLink
            to="/user"
            end
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            Home
          </NavLink>

          {canUseProduction && (
            <NavLink
              to="/user/production"
              className={({ isActive }) =>
                isActive ? 'active' : ''
              }
            >
              Production 360
            </NavLink>
          )}
        </nav>

        <div className="side-foot">
          CORE V{__APP_VERSION__}
        </div>
      </aside>

      <main>
        <header>
          <div className="global-search">
            <button
              type="button"
              className="search-button"
              onClick={() => undefined}
            >
              <span>Search Phoenix...</span>
              <span className="search-hint">
                Ctrl K
              </span>
            </button>
          </div>

          <div className="global-actions">
            <button
              type="button"
              className="top-action"
              onClick={() => undefined}
              title="Phoenix AI"
            >
              ✦ AI
            </button>

            <button
              type="button"
              className="top-action notification-button"
              onClick={() => undefined}
              title="Notifications"
            >
              🔔
            </button>

            <details className="user-menu">
              <summary>
                <span className="user-name">
                  {context.user.display_name}
                </span>
                <span className="user-chevron">
                  ▾
                </span>
              </summary>

              <div className="user-menu-panel">
                <div className="user-menu-heading">
                  {context.user.display_name}
                </div>

                <div className="user-menu-level">
                  {context.user.platform_level}
                </div>

                {context.company && (
                  <div className="user-menu-level">
                    {context.company.name}
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => undefined}
                >
                  User Settings
                </button>

                <button
                  type="button"
                  onClick={() => void logout()}
                >
                  Logout
                </button>
              </div>
            </details>
          </div>
        </header>

        <section className="content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}
