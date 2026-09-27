import { useCallback, useEffect, useState } from 'react'

import { api } from '../../core/api/client'

type Module = {
  id: string
  code: string
  name: string
  version: string
  status: 'REGISTERED' | 'ENABLED' | 'DISABLED' | 'RETIRED'
  created_at: string
}

async function getModules(): Promise<Module[]> {
  const result = await api<{ items: Module[] }>(
    '/api/v1/system/modules',
  )

  return result.items
}

async function changeModuleStatus(
  moduleId: string,
  action: 'enable' | 'disable' | 'retire',
): Promise<void> {
  await api<unknown>(
    `/api/v1/system/modules/${moduleId}/${action}`,
    {
      method: 'POST',
    },
  )
}

function statusClass(status: Module['status']): string {
  return `module-status module-status-${status.toLowerCase()}`
}

function statusLabel(status: Module['status']): string {
  return status.charAt(0) + status.slice(1).toLowerCase()
}

export function BusinessModules() {
  const [modules, setModules] = useState<Module[]>([])
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [retireTarget, setRetireTarget] = useState<Module | null>(null)

  const loadModules = useCallback(async () => {
    setError('')

    try {
      setModules(await getModules())
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load business modules.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadModules()
  }, [loadModules])

  async function executeAction(
    module: Module,
    action: 'enable' | 'disable' | 'retire',
  ) {
    const actionLabel =
      action === 'enable'
        ? 'enable'
        : action === 'disable'
          ? 'disable'
          : 'retire'

    setSavingId(module.id)
    setError('')

    try {
      await changeModuleStatus(module.id, action)
      await loadModules()
    } catch (actionError) {
      setError(
        actionError instanceof Error
          ? actionError.message
          : `Unable to ${actionLabel} module.`,
      )
    } finally {
      setSavingId(null)
    }
  }

  async function handleAction(
    module: Module,
    action: 'enable' | 'disable' | 'retire',
  ) {
    if (action === 'retire') {
      setRetireTarget(module)
      return
    }

    const actionLabel =
      action === 'enable' ? 'enable' : 'disable'

    if (
      !window.confirm(
        `Are you sure you want to ${actionLabel} "${module.name}"?`,
      )
    ) {
      return
    }

    await executeAction(module, action)
  }

  async function confirmRetire() {
    if (!retireTarget) {
      return
    }

    const module = retireTarget

    setRetireTarget(null)

    await executeAction(module, 'retire')
  }

  return (
    <section className="page business-modules-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">System Platform</p>
          <h1>Business Modules</h1>
          <p className="page-description">
            Manage the lifecycle of Phoenix business modules.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={() => void loadModules()}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      <div className="panel">
        {loading ? (
          <div className="empty-state">
            Loading business modules...
          </div>
        ) : modules.length === 0 ? (
          <div className="empty-state">
            No business modules are registered.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Module</th>
                  <th>Code</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {modules.map((module) => (
                  <tr key={module.id}>
                    <td>
                      <strong>{module.name}</strong>
                    </td>

                    <td>
                      <code>{module.code}</code>
                    </td>

                    <td>{module.version}</td>

                    <td>
                      <span className={statusClass(module.status)}>
                        {statusLabel(module.status)}
                      </span>
                    </td>

                    <td>
                      <div className="module-actions">
                        {module.status === 'REGISTERED' && (
                          <>
                            <button
                              className="primary-button"
                              type="button"
                              disabled={savingId === module.id}
                              onClick={() =>
                                void handleAction(module, 'enable')
                              }
                            >
                              Enable
                            </button>

                            <button
                              className="secondary-button"
                              type="button"
                              disabled={savingId === module.id}
                              onClick={() =>
                                void handleAction(module, 'disable')
                              }
                            >
                              Disable
                            </button>
                          </>
                        )}

                        {module.status === 'ENABLED' && (
                          <button
                            className="secondary-button"
                            type="button"
                            disabled={savingId === module.id}
                            onClick={() =>
                              void handleAction(module, 'disable')
                            }
                          >
                            Disable
                          </button>
                        )}

                        {module.status === 'DISABLED' && (
                          <button
                            className="primary-button"
                            type="button"
                            disabled={savingId === module.id}
                            onClick={() =>
                              void handleAction(module, 'enable')
                            }
                          >
                            Enable
                          </button>
                        )}

                        {module.status !== 'RETIRED' && (
                          <button
                            className="danger-button"
                            type="button"
                            disabled={savingId === module.id}
                            onClick={() =>
                              void handleAction(module, 'retire')
                            }
                          >
                            Retire
                          </button>
                        )}

                        {module.status === 'RETIRED' && (
                          <span className="module-no-actions">
                            No actions available
                          </span>
                        )}

                        {savingId === module.id && (
                          <span className="action-saving">
                            Saving...
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {retireTarget && (
        <div
          className="module-modal-backdrop"
          role="presentation"
          onClick={() => setRetireTarget(null)}
        >
          <div
            className="module-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="retire-module-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="module-modal-icon">!</div>

            <p className="eyebrow">Permanent Action</p>

            <h2 id="retire-module-title">
              Retire {retireTarget.name}?
            </h2>

            <p>
              This will permanently remove this module from the
              Phoenix module catalogue.
            </p>

            <p className="module-modal-warning">
              It cannot be enabled again after retirement.
            </p>

            <div className="module-modal-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => setRetireTarget(null)}
              >
                Cancel
              </button>

              <button
                className="danger-button"
                type="button"
                onClick={() => void confirmRetire()}
              >
                Retire Module
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}