import { useEffect, useState } from 'react'

function getUserInitials(displayName: string, username: string) {
  const source = displayName.trim() || username.trim()

  const parts = source
    .split(/\s+/)
    .filter(Boolean)

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  }

  return source.slice(0, 2).toUpperCase()
}
import { api } from '../../core/api'

type SystemUser = {
  id: string
  identity_id: string
  username: string
  display_name: string
  status: string
  platform_level: string
  password_reset_required: number
  created_at: string
}

export function SystemUsers() {
  const [users, setUsers] = useState<SystemUser[]>([])
  const [selectedUser, setSelectedUser] =
    useState<SystemUser | null>(null)

  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const [showCreate, setShowCreate] = useState(false)

  const [form, setForm] = useState({
    username: '',
    display_name: '',
    password: '',
  })

  async function loadUsers() {
    setLoading(true)
    setError('')

    try {
      const data = await api(
        `/api/v1/system/users?search=${encodeURIComponent(search)}`,
      )

      const items = Array.isArray(data?.items)
        ? data.items
        : []

      setUsers(items)

      if (selectedUser) {
        const refreshed = items.find(
          (item: SystemUser) =>
            item.id === selectedUser.id,
        )

        setSelectedUser(refreshed || null)
      }
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load system users.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadUsers()
    }, 250)

    return () => window.clearTimeout(timer)
  }, [search])

  async function runAction(
    userId: string,
    action: string,
    body?: object,
  ) {
    setSaving(true)
    setError('')

    try {
      await api(
        `/api/v1/system/users/${userId}/${action}`,
        {
          method: 'POST',
          ...(body
            ? {
                body: JSON.stringify(body),
              }
            : {}),
        },
      )

      await loadUsers()
    } catch (actionError) {
      setError(
        actionError instanceof Error
          ? actionError.message
          : 'The requested action could not be completed.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function createUser() {
    if (
      !form.username.trim() ||
      !form.display_name.trim() ||
      !form.password
    ) {
      setError(
        'Username, display name and password are required.',
      )
      return
    }

    setSaving(true)
    setError('')

    try {
      await api(
        '/api/v1/system/users',
        {
          method: 'POST',
          body: JSON.stringify({
            username: form.username.trim(),
            display_name: form.display_name.trim(),
            password: form.password,
          }),
        },
      )

      setForm({
        username: '',
        display_name: '',
        password: '',
      })

      setShowCreate(false)

      await loadUsers()
    } catch (createError) {
      setError(
        createError instanceof Error
          ? createError.message
          : 'Unable to create system user.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function resetPassword() {
    if (!selectedUser) return

    const password = window.prompt(
      'Enter the temporary password. The user will be required to change it:',
    )

    if (!password) return

    await runAction(
      selectedUser.id,
      'reset-password',
      { password },
    )
  }

  async function requireReset() {
    if (!selectedUser) return

    if (
      !window.confirm(
        `Require ${selectedUser.display_name} to change their password?`,
      )
    ) {
      return
    }

    await runAction(
      selectedUser.id,
      'require-password-reset',
    )
  }

  return (
    <main className="companies-page">
      <div className="companies-page-header">
        <div>
          <div className="page-eyebrow">SYSTEM USERS</div>
          <h1>Phoenix system users</h1>
          <p>
            Manage Phoenix administrators and internal
            system users.
          </p>
        </div>

        <button
          type="button"
          className="phoenix-primary-button"
          onClick={() => {
            setError('')
            setShowCreate(true)
          }}
        >
          + Add System User
        </button>
      </div>

      {error && (
        <div className="company-message">
          {error}
        </div>
      )}

      {showCreate && (
        <section className="add-company-panel">
          <div>
            <h2>Add System User</h2>
            <p>
              Create a new Phoenix system administrator.
            </p>
          </div>

          <div className="company-form-grid">
            <label>
              Username
              <input
                value={form.username}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    username: event.target.value,
                  }))
                }
                placeholder="e.g. admin"
              />
            </label>

            <label>
              Display Name
              <input
                value={form.display_name}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    display_name: event.target.value,
                  }))
                }
                placeholder="e.g. Phoenix Administrator"
              />
            </label>

            <label>
              Temporary Password
              <input
                type="password"
                value={form.password}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    password: event.target.value,
                  }))
                }
                placeholder="Temporary password"
              />
            </label>
          </div>

          <div className="company-form-actions">
            <button
              type="button"
              className="phoenix-primary-button"
              onClick={() => void createUser()}
              disabled={saving}
            >
              {saving ? 'Creating...' : 'Create User'}
            </button>

            <button
              type="button"
              className="phoenix-secondary-button"
              onClick={() => setShowCreate(false)}
              disabled={saving}
            >
              Cancel
            </button>
          </div>
        </section>
      )}

      <section className="companies-workspace">
        <div className="companies-list-panel">
          <div className="companies-list-header">
            <div>
              <h2>
                System Administrators ({users.length})
              </h2>
              <span>
                {users.length === 1
                  ? '1 user'
                  : `${users.length} users`}
              </span>
            </div>

            <input
              className="search-input"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search users..."
            />
          </div>

          {loading ? (
            <div className="company-empty-state">
              Loading system users...
            </div>
          ) : users.length === 0 ? (
            <div className="company-empty-state">
              No system users found.
            </div>
          ) : (
            <div className="company-list">
              {users.map((user) => {
                const selected =
                  selectedUser?.id === user.id

                return (
                  <button
                    type="button"
                    key={user.id}
                    className={`company-list-item ${
                      selected ? 'selected' : ''
                    }`}
                    onClick={() =>
                      setSelectedUser(user)
                    }
                  >
                    <span className="company-list-icon user-avatar">
                      {getUserInitials(
                        user.display_name,
                        user.username,
                      )}
                    </span>

                    <span className="company-list-content">
                      <strong>
                        {user.display_name}
                      </strong>
                      <small>
                        @{user.username}
                      </small>
                    </span>

                    <span
                      className={`company-status ${
                        user.status?.toLowerCase()
                      }`}
                    >
                      {user.status}
                    </span>

                    {user.password_reset_required ===
                      1 && (
                      <span className="company-status suspended">
                        RESET
                      </span>
                    )}

                    <span className="company-chevron">
                      ›
                    </span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="company-detail-panel">
          {!selectedUser ? (
            <div className="company-empty-state">
              <strong>Select a system user</strong>
              <span>
                User details and administration actions
                will appear here.
              </span>
            </div>
          ) : (
            <>
              <div className="company-detail-header">
                <div className="company-detail-title">
                  <div className="company-large-icon user-avatar-large">
                    {getUserInitials(
                      selectedUser.display_name,
                      selectedUser.username,
                    )}
                  </div>

                  <div>
                    <div className="company-title-row">
                      <h2>
                        {selectedUser.display_name}
                      </h2>

                      <span
                        className={`company-status ${
                          selectedUser.status?.toLowerCase()
                        }`}
                      >
                        {selectedUser.status}
                      </span>

                      {selectedUser.password_reset_required ===
                        1 && (
                        <span className="company-status reset">
                          RESET
                        </span>
                      )}
                    </div>

                    <p>
                      @{selectedUser.username}
                    </p>
                  </div>
                </div>
              </div>

              <div className="system-user-tabs">
                <button
                  type="button"
                  className="system-user-tab active"
                >
                  Details
                </button>

                <button
                  type="button"
                  className="system-user-tab"
                  disabled
                  title="Session management will be added here."
                >
                  Sessions
                </button>

                <button
                  type="button"
                  className="system-user-tab"
                  disabled
                  title="Audit history will be added here."
                >
                  Audit Log
                </button>
              </div>

              <div className="company-information-card system-user-account-card">
                <h3>Account Information</h3>

                <div className="company-form-grid">
                  <label>
                    Username
                    <input
                      value={selectedUser.username}
                      readOnly
                    />
                  </label>

                  <label>
                    Display Name
                    <input
                      value={selectedUser.display_name}
                      readOnly
                    />
                  </label>

                  <label>
                    Platform Level
                    <input
                      value={selectedUser.platform_level}
                      readOnly
                    />
                  </label>

                  <label>
                    Account Status
                    <input
                      value={selectedUser.status}
                      readOnly
                    />
                  </label>

                  <label>
                    Password State
                    <input
                      value={
                        selectedUser.password_reset_required ===
                        1
                          ? 'RESET REQUIRED'
                          : 'NORMAL'
                      }
                      readOnly
                    />
                  </label>

                  <label>
                    Created
                    <input
                      value={
                        selectedUser.created_at
                          ? new Date(
                              selectedUser.created_at,
                            ).toLocaleDateString()
                          : ''
                      }
                      readOnly
                    />
                  </label>
                </div>
              </div>

              <div className="system-user-action-bar">
                <div className="system-user-action-group">
                  <button
                    type="button"
                    className="system-user-action reset"
                    disabled={saving}
                    onClick={() =>
                      void resetPassword()
                    }
                  >
                    Reset Password
                  </button>

                  {selectedUser.status ===
                  'ACTIVE' ? (
                    <button
                      type="button"
                      className="system-user-action suspend"
                      disabled={saving}
                      onClick={() =>
                        void runAction(
                          selectedUser.id,
                          'suspend',
                        )
                      }
                    >
                      {saving
                        ? 'Working...'
                        : 'Suspend User'}
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="system-user-action reactivate"
                      disabled={saving}
                      onClick={() =>
                        void runAction(
                          selectedUser.id,
                          'reactivate',
                        )
                      }
                    >
                      {saving
                        ? 'Working...'
                        : 'Reactivate User'}
                    </button>
                  )}

                  <button
                    type="button"
                    className="system-user-action require-reset"
                    disabled={saving}
                    onClick={() =>
                      void requireReset()
                    }
                  >
                    Require Password Reset
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </section>
    </main>
  )
}




