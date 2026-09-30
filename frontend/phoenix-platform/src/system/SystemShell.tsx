import { NavLink, Outlet } from 'react-router'

import { usePlatformContext } from '../core/platform/PlatformContext'

export function SystemShell() {
  const {
    context,
    logout,
  } = usePlatformContext()

  if (!context) {
    return null
  }

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
          SYSTEM PLATFORM
        </div>

        <nav>
          <NavLink
            to="/system"
            end
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            Home
          </NavLink>

          <NavLink
            to="/system/companies"
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            Companies
          </NavLink>

          <NavLink
            to="/system/companies-users"
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            Companies User
          </NavLink>

          <NavLink
            to="/system/users"
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            System Users
          </NavLink>

          <NavLink
            to="/system/modules"
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            Business Modules
          </NavLink>

          <NavLink
            to="/system/governance"
            className={({ isActive }) =>
              isActive ? 'active' : ''
            }
          >
            Legal Governance
          </NavLink>
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

                <button
                  type="button"
                  onClick={() => undefined}
                >
                  User Settings
                </button>

                <button
                  type="button"
                  onClick={logout}
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

