import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../../core/api'
import { usePlatformContext } from '../../core/platform/PlatformContext'
import { KpiCard, getGreeting } from '../shared/helpers'

export function SystemHome() {
  const { context } = usePlatformContext()
  const navigate = useNavigate()

  const [companies, setCompanies] =
    useState<Company[]>([])

  const [modules, setModules] =
    useState<Module[]>([])

  const [users, setUsers] =
    useState<SystemUser[]>([])

  const [loading, setLoading] =
    useState(true)

  const [loadError, setLoadError] =
    useState('')

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setLoadError('')

        const [
          companyData,
          moduleData,
          userData,
        ] = await Promise.all([
          api(
            '/api/v1/system/companies',
          ),
          api(
            '/api/v1/system/modules',
          ),
          api(
            '/api/v1/system/users',
          ),
        ])

        setCompanies(
          companyData.items || [],
        )

        setModules(
          moduleData.items || [],
        )

        setUsers(
          userData.items || [],
        )
      } catch (error) {
        setLoadError(
          error instanceof Error
            ? error.message
            : 'Unable to load dashboard data.',
        )
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const totalCompanies =
    companies.length

  const activeCompanies =
    companies.filter(
      (company) =>
        company.status.toLowerCase() ===
        'active',
    ).length

  const totalUsers =
    users.length

  const activeUsers =
    users.filter(
      (user) =>
        user.status.toLowerCase() ===
        'active',
    ).length

  const activeBusinessModules =
    new Set(
      modules
        .filter(
          (module) =>
            module.status.toUpperCase() ===
            'ENABLED',
        )
        .map(
          (module) =>
            module.code,
        ),
    ).size

  const recentCompanies =
    [...companies]
      .slice(-5)
      .reverse()

  return (
    <>
      <div className="dashboard-heading">
        <span className="eyebrow">
          SYSTEM PLATFORM
        </span>

        <h1>
          {getGreeting(
            context.user.display_name,
          )}
        </h1>

        <p className="muted">
          Welcome back to Phoenix Core.
          Here's what's happening across
          your platform.
        </p>
      </div>

      {loadError && (
        <div className="error">
          {loadError}
        </div>
      )}

      <div className="kpi-grid">
        <KpiCard
          value={loading ? '...' : totalCompanies}
          label="Total Companies"
          secondary={
            loading
              ? 'Loading...'
              : `${totalCompanies} registered`
          }
          onClick={() => navigate('/system/companies')}
          disabled={loading}
        />

        <KpiCard
          value={loading ? '...' : activeCompanies}
          label="Active Companies"
          secondary={
            loading
              ? 'Loading...'
              : `${activeCompanies} currently active`
          }
          onClick={() => navigate('/system/companies')}
          disabled={loading}
        />

        <KpiCard
          value={loading ? '...' : totalUsers}
          label="System Users"
          secondary={
            loading
              ? 'Loading...'
              : `${activeUsers} currently active`
          }
          onClick={() => navigate('/system/users')}
          disabled={loading}
        />

        <KpiCard
          value={loading ? '...' : activeBusinessModules}
          label="Active Business Modules"
          secondary={
            loading
              ? 'Loading...'
              : `${activeBusinessModules} active across platform`
          }
          onClick={() => navigate('/system/modules')}
          disabled={loading}
        />
      </div>

      <div className="dashboard-sections">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                PLATFORM STATUS
              </span>

              <h3>
                Phoenix Core
              </h3>
            </div>

            <span className="status-badge">
              ONLINE
            </span>
          </div>

          <div className="status-row">
            <span>
              Core version
            </span>

            <strong>
              V1.0.0
            </strong>
          </div>

          <div className="status-row">
            <span>
              Business modules
            </span>

            <strong>
              {loading
                ? '∩┐╜'
                : `${activeBusinessModules} active`}
            </strong>
          </div>

          <div className="status-row">
            <span>
              Platform access
            </span>

            <strong>
              Operational
            </strong>
          </div>
        </div>

        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                RECENT COMPANIES
              </span>

              <h3>
                Latest registered companies
              </h3>
            </div>

            <button
              type="button"
              className="text-button"
              onClick={() =>
                navigate('/system/companies')
              }
            >
              View all ?
            </button>
          </div>

          {loading && (
            <p className="muted">
              Loading companies...
            </p>
          )}

          {!loading &&
            recentCompanies.length ===
              0 && (
              <p className="muted">
                No companies registered
                yet.
              </p>
            )}

          {!loading &&
            recentCompanies.map(
              (company) => (
                <div
                  className="activity-row"
                  key={company.id}
                >
                  <div>
                    <strong>
                      {company.name}
                    </strong>

                    <span>
                      {company.code}
                    </span>
                  </div>

                  <span
                    className={
                      company.status
                        .toLowerCase() ===
                      'active'
                        ? 'status-badge'
                        : 'status-badge neutral'
                    }
                  >
                    {company.status}
                  </span>
                </div>
              ),
            )}
        </div>

        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                RECENT ACTIVITY
              </span>

              <h3>
                System activity
              </h3>
            </div>
          </div>

          <div className="empty-state">
            <strong>
              Activity tracking is coming
              next.
            </strong>

            <p className="muted">
              This area will show important
              Phoenix system events once
              platform activity logging is
              connected.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

/* -------------------------------------------------------------------------- */
/* SYSTEM COMPANIES                                                           */
/* -------------------------------------------------------------------------- */






