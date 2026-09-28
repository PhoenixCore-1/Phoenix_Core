import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { NavLink, Outlet } from 'react-router'
import './styles.css'
import { AppRoutes } from './app/AppRoutes'
import { SystemHome } from './system/home/SystemHome'
import Roles from './company/roles/Roles'
import { api as coreApi } from './core/api'
import {
  PlatformProvider,
  usePlatformContext,
} from './core/platform/PlatformContext'

type PlatformLevel =
  | 'SYSTEM_ADMIN'
  | 'COMPANY_ADMIN'
  | 'COMPANY_USER'

type SystemView =
  | 'home'
  | 'companies'
  | 'system-users'
  | 'business-modules'
  | 'billing'
  | 'quotes'
  | 'platform-reporting'
  | 'admin'
  | 'notifications'

type CompanyView =
  | 'home'
  | 'company'
  | 'users'
  | 'roles'
  | 'workspace'
  | 'kpi'
  | 'reporting'
  | 'activity'
  | 'settings'
  | 'connect'

type UserView =
  | 'home'
  | 'modules'

type Module = {
  id: string
  code: string
  name: string
  version: string
  active: boolean
}

type Company = {
  id: string
  code: string
  name: string
  status: string
}

type Context = {
  user: {
    id: string
    username: string
    display_name: string
    platform_level: PlatformLevel
  }
  company: Company | null
  modules: Module[]
}

type ApiOptions = RequestInit & {
  headers?: Record<string, string>
}

async function api(
  path: string,
  options: ApiOptions = {},
): Promise<any> {
  return coreApi(path, options)

  /*
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  const body = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      body.message ||
        body.detail ||
        body.error?.message ||
        'Phoenix Core request failed',
    )
  }

  return body.data
  */
}

function App() {
  const {
    context,
    isAuthenticated,
    loading,
    mustChangePassword,
    logout,
  } = usePlatformContext()

  if (loading && !isAuthenticated) {
    return (
      <div className="center">
        Loading Phoenix...
      </div>
    )
  }

  if (!isAuthenticated || !context) {
    return <Login />
  }

  if (mustChangePassword) {
    return <ChangePassword />
  }

  if (context.user.platform_level === 'COMPANY_ADMIN') {
    if (window.location.pathname !== '/company') {
      window.history.replaceState(null, '', '/company')
    }

    return (
      <CompanyShell
        context={context}
        onLogout={() => void logout()}
      />
    )
  }

  return <AppRoutes />
}
function ChangePassword() {
  const {
    changePassword,
    logout,
  } = usePlatformContext()

  const [currentPassword, setCurrentPassword] =
    useState('')
  const [newPassword, setNewPassword] =
    useState('')
  const [confirmPassword, setConfirmPassword] =
    useState('')
  const [showCurrentPassword, setShowCurrentPassword] =
    useState(false)
  const [showNewPassword, setShowNewPassword] =
    useState(false)
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()
    setError('')

    if (newPassword.length < 12) {
      setError(
        'Your new password must be at least 12 characters.',
      )
      return
    }

    if (newPassword !== confirmPassword) {
      setError('The new passwords do not match.')
      return
    }

    setSaving(true)

    try {
      await changePassword(
        currentPassword,
        newPassword,
      )
    } catch (changeError) {
      setError(
        changeError instanceof Error
          ? changeError.message
          : 'Unable to change password.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card-new">
        <div className="login-header-brand">
          <img
            src="/phoenix.png"
            alt="Phoenix"
          />

          <div className="brand-divider"></div>

          <div className="brand-title">
            PHOENIX CORE
            <span>PLATFORM</span>
          </div>
        </div>

        <div className="login-heading">
          <h1>Change your password</h1>

          <p>
            Your administrator provided a temporary
            password. You must choose a new password
            before continuing.
          </p>
        </div>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        <form
          className="login-form-new"
          onSubmit={submit}
        >
          <label>
            Temporary password

            <div className="password-input-wrapper">
              <input
                type={showCurrentPassword ? 'text' : 'password'}
                value={currentPassword}
                onChange={(event) =>
                  setCurrentPassword(
                    event.target.value,
                  )
                }
                autoComplete="current-password"
                required
              />

              <button
                type="button"
                className="password-visibility-button"
                onClick={() =>
                  setShowCurrentPassword(
                    (visible) => !visible,
                  )
                }
                aria-label={
                  showCurrentPassword
                    ? 'Hide temporary password'
                    : 'Show temporary password'
                }
              >
                {showCurrentPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </label>

          <label>
            New password

            <div className="password-input-wrapper">
              <input
                type={showNewPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(event) =>
                  setNewPassword(
                    event.target.value,
                  )
                }
                autoComplete="new-password"
                minLength={12}
                required
              />

              <button
                type="button"
                className="password-visibility-button"
                onClick={() =>
                  setShowNewPassword(
                    (visible) => !visible,
                  )
                }
                aria-label={
                  showNewPassword
                    ? 'Hide new password'
                    : 'Show new password'
                }
              >
                {showNewPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </label>

          <label>
            Confirm new password

            <div className="password-input-wrapper">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value,
                  )
                }
                autoComplete="new-password"
                minLength={12}
                required
              />

              <button
                type="button"
                className="password-visibility-button"
                onClick={() =>
                  setShowConfirmPassword(
                    (visible) => !visible,
                  )
                }
                aria-label={
                  showConfirmPassword
                    ? 'Hide confirmed password'
                    : 'Show confirmed password'
                }
              >
                {showConfirmPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </label>

          <button
            type="submit"
            className="login-submit-new"
            disabled={saving}
          >
            {saving
              ? 'Updating password...'
              : 'Set new password'}
          </button>
        </form>

        <button
          type="button"
          className="login-secondary-button"
          onClick={() => void logout()}
          disabled={saving}
        >
          Sign out
        </button>
      </div>
    </div>
  )
}
function Login() {
  const {
    login,
    error,
    loading,
  } = usePlatformContext()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] =
    useState(false)

  const [remember, setRemember] = useState(true)

  const submit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    try {
      await login(username, password)
    } catch {
      // PlatformContext exposes the normalized login error.
    }
  }
  return (
    <div className="login-page">
      <div className="login-card-new">
        <div className="login-header-brand">
          <img
            src="/phoenix.png"
            alt="Phoenix"
          />

          <div className="brand-divider"></div>

          <div className="brand-title">
            PHOENIX CORE
            <span>PLATFORM</span>
          </div>
        </div>

        <div className="login-heading">
          <h1>Welcome back</h1>

          <p>
            Sign in to continue to Phoenix.
          </p>
        </div>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        <form
          className="login-form-new"
          onSubmit={submit}
        >
          <label>
            Username

            <input
              type="text"
              value={username}
              onChange={(event) =>
                setUsername(
                  event.target.value,
                )
              }
              autoComplete="username"
              required
            />
          </label>

          <label>
            Password

            <div className="password-field">
              <input
                type={
                  showPassword
                    ? 'text'
                    : 'password'
                }
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value,
                  )
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword(
                    !showPassword,
                  )
                }
              >
                {showPassword
                  ? 'Hide'
                  : 'Show'}
              </button>
            </div>
          </label>

          <label className="remember-new">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) =>
                setRemember(
                  event.target.checked,
                )
              }
            />

            <span>
              Remember me
            </span>
          </label>

          <button
            className="login-submit-new"
            type="submit"
            disabled={loading}
          >
            {loading
              ? 'Signing in...'
              : 'Sign in'}
          </button>
        </form>

        <div className="login-footer-new">
          <span>
            Phoenix Core Platform V1.0.0
          </span>

          <b>ï¿½</b>

          <span>
            Secure access
          </span>
        </div>
      </div>
    </div>
  )
}

function Shell({
  context,
  onLogout,
}: {
  context: Context
  onLogout: () => void
}) {
  if (
    context.user.platform_level ===
    'SYSTEM_ADMIN'
  ) {
    return (
      <SystemShell />
    )
  }

  if (
    context.user.platform_level ===
    'COMPANY_ADMIN'
  ) {
    return (
      <CompanyShell
        context={context}
        onLogout={onLogout}
      />
    )
  }

  return (
    <UserShell
      context={context}
      onLogout={onLogout}
    />
  )
}

/* -------------------------------------------------------------------------- */
/* SYSTEM PLATFORM                                                            */
/* -------------------------------------------------------------------------- */

function SystemShell() {
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
          CORE V1.0.0
        </div>
      </aside>

      <main>
        <header>
          <div>
            <span className="eyebrow">
              PHOENIX
            </span>

            <h2>
              System Platform
            </h2>
          </div>

          <div className="account">
            <span>
              {context.user.display_name}
            </span>

            <button
              type="button"
              onClick={logout}
            >
              Sign out
            </button>
          </div>
        </header>

        <section className="content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* SYSTEM USERS                                                               */
/* -------------------------------------------------------------------------- */

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

function SystemUsers() {
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

  const loadUsers = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await api(
        `/api/v1/system/users?search=${encodeURIComponent(search)}`,
      )

      const items =
        Array.isArray(data)
          ? data
          : Array.isArray(data.data?.items)
            ? data.data.items
            : Array.isArray(data.items)
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
    const timer = window.setTimeout(
      () => {
        loadUsers()
      },
      250,
    )

    return () => window.clearTimeout(timer)
  }, [search])

  const runAction = async (
    userId: string,
    action: string,
    body?: object,
  ) => {
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

  const createUser = async () => {
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
          body: JSON.stringify(form),
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

  const resetPassword = async () => {
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

  const requireReset = async () => {
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
    <div className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">
            SYSTEM USERS
          </span>
          <h1>Phoenix system users</h1>
          <p>
            Manage Phoenix administrators and internal
            system users.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={() => {
            setError('')
            setShowCreate(true)
          }}
        >
          Add system user
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="system-users-layout">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>System administrators</h3>
              <span>
                {users.length} user
                {users.length === 1 ? '' : 's'}
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
            <div className="empty-state">
              Loading system users...
            </div>
          ) : users.length === 0 ? (
            <div className="empty-state">
              No system users found.
            </div>
          ) : (
            <div className="user-table">
              {users.map((user) => (
                <button
                  type="button"
                  key={user.id}
                  className={`user-row ${
                    selectedUser?.id === user.id
                      ? 'selected'
                      : ''
                  }`}
                  onClick={() =>
                    setSelectedUser(user)
                  }
                >
                  <div className="user-row-main">
                    <strong>
                      {user.display_name}
                    </strong>
                    <span>
                      @{user.username}
                    </span>
                  </div>

                  <div className="user-row-meta">
                    <span
                      className={`status-pill ${
                        user.status === 'ACTIVE'
                          ? 'active'
                          : 'suspended'
                      }`}
                    >
                      {user.status}
                    </span>

                    {user.password_reset_required ===
                      1 && (
                      <span className="status-pill reset">
                        PASSWORD RESET REQUIRED
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          {!selectedUser ? (
            <div className="empty-state detail-empty">
              <strong>Select a system user</strong>
              <span>
                User details and administration actions
                will appear here.
              </span>
            </div>
          ) : (
            <>
              <div className="detail-header">
                <div>
                  <span className="eyebrow">
                    SYSTEM USER
                  </span>
                  <h2>
                    {selectedUser.display_name}
                  </h2>
                  <span>
                    @{selectedUser.username}
                  </span>
                </div>

                <span
                  className={`status-pill ${
                    selectedUser.status === 'ACTIVE'
                      ? 'active'
                      : 'suspended'
                  }`}
                >
                  {selectedUser.status}
                </span>
              </div>

              <div className="detail-grid">
                <div>
                  <span>Username</span>
                  <strong>
                    {selectedUser.username}
                  </strong>
                </div>

                <div>
                  <span>Platform level</span>
                  <strong>
                    {selectedUser.platform_level}
                  </strong>
                </div>

                <div>
                  <span>Account status</span>
                  <strong>
                    {selectedUser.status}
                  </strong>
                </div>

                <div>
                  <span>Password state</span>
                  <strong>
                    {selectedUser.password_reset_required ===
                    1
                      ? 'RESET REQUIRED'
                      : 'NORMAL'}
                  </strong>
                </div>
              </div>

              <div className="action-group">
                <h3>Account actions</h3>

                <div className="action-buttons">
                  {selectedUser.status ===
                  'ACTIVE' ? (
                    <button
                      type="button"
                      className="danger-button"
                      disabled={saving}
                      onClick={() =>
                        runAction(
                          selectedUser.id,
                          'suspend',
                        )
                      }
                    >
                      Suspend user
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="primary-button"
                      disabled={saving}
                      onClick={() =>
                        runAction(
                          selectedUser.id,
                          'reactivate',
                        )
                      }
                    >
                      Reactivate user
                    </button>
                  )}

                  <button
                    type="button"
                    className="secondary-button"
                    disabled={saving}
                    onClick={resetPassword}
                  >
                    Reset password
                  </button>

                  <button
                    type="button"
                    className="secondary-button"
                    disabled={
                      saving ||
                      selectedUser.password_reset_required ===
                        1
                    }
                    onClick={requireReset}
                  >
                    Require password reset
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </div>

      {showCreate && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="detail-header">
              <div>
                <span className="eyebrow">
                  NEW SYSTEM USER
                </span>
                <h2>Add system user</h2>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setShowCreate(false)
                }
              >
                ï¿½
              </button>
            </div>

            <div className="form-stack">
              <label>
                Display name
                <input
                  value={form.display_name}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      display_name:
                        event.target.value,
                    })
                  }
                  placeholder="System Administrator"
                />
              </label>

              <label>
                Username
                <input
                  value={form.username}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      username:
                        event.target.value,
                    })
                  }
                  placeholder="system.admin"
                />
              </label>

              <label>
                Temporary password
                <input
                  type="password"
                  value={form.password}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      password:
                        event.target.value,
                    })
                  }
                  placeholder="Minimum 12 characters"
                />
              </label>
            </div>

            <div className="action-buttons modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setShowCreate(false)
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                disabled={saving}
                onClick={createUser}
              >
                Create system user
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* SYSTEM HOME                                                                */
/* -------------------------------------------------------------------------- */

function SystemCompanies() {
  const [companies, setCompanies] =
    useState<any[]>([])

  const [selectedCompanyId, setSelectedCompanyId] =
    useState<string | null>(null)

  const [companyDetail, setCompanyDetail] =
    useState<any | null>(null)

  const [message, setMessage] =
    useState('')

  const [code, setCode] =
    useState('')

  const [name, setName] =
    useState('')

  const loadCompanies = async () => {
    const data =
      await api('/api/v1/system/companies')

    setCompanies(data.items || [])
  }

  const loadCompanyDetail = async (
    companyId: string,
  ) => {
    const data =
      await api(
        `/api/v1/system/companies/${companyId}`,
      )

    setCompanyDetail(data)
    setSelectedCompanyId(companyId)
  }

  useEffect(() => {
    loadCompanies().catch((loadError) => {
      setMessage(
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load companies.',
      )
    })
  }, [])

  const create = async () => {
    if (
      !code.trim() ||
      !name.trim()
    ) {
      setMessage(
        'Company code and name are required.',
      )

      return
    }

    try {
      await api(
        '/api/v1/system/companies',
        {
          method: 'POST',
          body: JSON.stringify({
            code,
            name,
          }),
        },
      )

      setCode('')
      setName('')
      setMessage('Company created.')

      await loadCompanies()
    } catch (createError) {
      setMessage(
        createError instanceof Error
          ? createError.message
          : 'Unable to create company.',
      )
    }
  }

  const changeCompanyStatus = async (
    companyId: string,
    action: 'activate' | 'suspend',
  ) => {
    try {
      await api(
        `/api/v1/system/companies/${companyId}/${action}`,
        {
          method: 'POST',
        },
      )

      setMessage(
        action === 'activate'
          ? 'Company activated.'
          : 'Company suspended.',
      )

      await loadCompanyDetail(companyId)
      await loadCompanies()
    } catch (companyError) {
      setMessage(
        companyError instanceof Error
          ? companyError.message
          : 'Unable to update company status.',
      )
    }
  }

  const changeModuleStatus = async (
    companyId: string,
    moduleCode: string,
    moduleName: string,
    action: 'activate' | 'suspend',
  ) => {
    try {
      await api(
        `/api/v1/system/companies/${companyId}/modules/${moduleCode}/${action}`,
        {
          method: 'POST',
        },
      )

      setMessage(
        action === 'activate'
          ? `${moduleName} activated.`
          : `${moduleName} suspended.`,
      )

      await loadCompanyDetail(companyId)
    } catch (moduleError) {
      setMessage(
        moduleError instanceof Error
          ? moduleError.message
          : 'Unable to update module status.',
      )
    }
  }

  if (selectedCompanyId && companyDetail) {
    const company =
      companyDetail.company

    return (
      <>
        <div className="hero">
          <button
            type="button"
            className="small-btn"
            onClick={() => {
              setSelectedCompanyId(null)
              setCompanyDetail(null)
              setMessage('')
            }}
          >
            ? Back to Companies
          </button>

          <span className="eyebrow">
            COMPANY DETAIL
          </span>

          <h1>
            {company.name}
          </h1>

          <p className="muted">
            {company.code}
          </p>

          <div className="company-status-row">
            <div className="company-status-block">
              <span className="eyebrow">
                COMPANY STATUS
              </span>

              <strong className="company-status-value">
                {company.status}
              </strong>
            </div>

            <div className="company-status-action">
              {company.status === 'ACTIVE' && (
              <button
                type="button"
                className="small-btn"
                onClick={() =>
                  changeCompanyStatus(
                    company.id,
                    'suspend',
                  )
                }
              >
                Suspend Company
              </button>
            )}

            {company.status === 'SUSPENDED' && (
              <button
                type="button"
                className="small-btn"
                onClick={() =>
                  changeCompanyStatus(
                    company.id,
                    'activate',
                  )
                }
              >
                Activate Company
              </button>
            )}
            </div>
          </div>
        </div>

        {message && (
          <div className="panel">
            <p>{message}</p>
          </div>
        )}

        <div className="panel company-overview-panel">
          <div className="section-heading">
            <span className="eyebrow">
              COMPANY
            </span>

            <h3>
              Company Overview
            </h3>
          </div>

          <div className="company-overview-grid">
            <div>
              <span className="field-label">
                Company Name
              </span>

              <strong>
                {company.name}
              </strong>
            </div>

            <div>
              <span className="field-label">
                Company Code
              </span>

              <strong>
                {company.code}
              </strong>
            </div>
          </div>
        </div>

        <div className="panel business-modules-panel">
          <div className="section-heading">
            <span className="eyebrow">
              PHOENIX CAPABILITIES
            </span>

            <h3>
              Business Modules
            </h3>

            <p className="muted">
              Control which Phoenix modules this company can use.
            </p>
          </div>

          {companyDetail.modules.length === 0 && (
            <p className="muted">
              No business modules are available.
            </p>
          )}

          {companyDetail.modules.map(
            (module: any) => (
              <div
                className="module-row"
                key={module.code}
              >
                <strong>
                  {module.name}
                </strong>

                <span>
                  Version {module.version}
                </span>

                <span>
                  {module.status}
                </span>

                <div>
                  {module.status === 'ACTIVE' && (
                    <button
                      type="button"
                      className="small-btn"
                      onClick={() =>
                        changeModuleStatus(
                          company.id,
                          module.code,
                          module.name,
                          'suspend',
                        )
                      }
                    >
                      Suspend
                    </button>
                  )}

                  {(module.status === 'SUSPENDED' ||
                    module.status === 'NOT_ACTIVATED') && (
                    <button
                      type="button"
                      className="small-btn"
                      onClick={() =>
                        changeModuleStatus(
                          company.id,
                          module.code,
                          module.name,
                          'activate',
                        )
                      }
                    >
                      Activate
                    </button>
                  )}
                </div>
              </div>
            ),
          )}
        </div>
      </>
    )
  }

  return (
    <>
      <div className="hero">
        <span className="eyebrow">
          COMPANIES
        </span>

        <h1>
          Companies using Phoenix
        </h1>

        <p className="muted">
          Create and manage companies
          using the Phoenix Company
          Platform.
        </p>
      </div>

      <div className="panel">
        <h3>
          Create company
        </h3>

        <div className="row">
          <input
            placeholder="Company code"
            value={code}
            onChange={(event) =>
              setCode(event.target.value)
            }
          />

          <input
            placeholder="Company name"
            value={name}
            onChange={(event) =>
              setName(event.target.value)
            }
          />

          <button
            type="button"
            onClick={create}
          >
            Create
          </button>
        </div>

        {message && (
          <p>{message}</p>
        )}
      </div>

      <div className="panel">
        <h3>
          Companies
        </h3>

        {companies.length === 0 && (
          <p className="muted">
            No companies found.
          </p>
        )}

        {companies.map((company) => (
          <div
            className="list"
            key={company.id}
          >
            <strong>
              {company.name}
            </strong>

            <span>
              {company.code}
            </span>

            <span>
              {company.status}
            </span>

            <button
              type="button"
              className="small-btn"
              onClick={() =>
                loadCompanyDetail(company.id)
              }
            >
              Open Company
            </button>
          </div>
        ))}
      </div>
    </>
  )
}
function CompanyShell({
  context,
  onLogout,
}: {
  context: Context
  onLogout: () => void
}) {
  const [view, setView] =
    useState<CompanyView>('home')

  const [notificationsOpen, setNotificationsOpen] =
    useState(false)

  const [profileOpen, setProfileOpen] =
    useState(false)


  const [search, setSearch] =
    useState('')

  const navigation: {
    view: CompanyView
    label: string
    icon: string
  }[] = [
    { view: 'company', label: 'Company Profile', icon: '?' },
    { view: 'users', label: 'Users', icon: '?' },
    { view: 'roles', label: 'Roles', icon: '?' },
    { view: 'workspace', label: 'Workspace', icon: '?' },
    { view: 'kpi', label: 'KPI', icon: '?' },
    { view: 'reporting', label: 'Reporting', icon: '?' },
    { view: 'activity', label: 'Activity', icon: '?' },
    { view: 'settings', label: 'Company Settings', icon: '?' },
    { view: 'connect', label: 'Phoenix Connect', icon: '?' },
  ]

  const placeholderTitles: Record<
    Exclude<CompanyView, 'home' | 'company' | 'users'>,
    {
      eyebrow: string
      title: string
      description: string
    }
  > = {
    roles: {
      eyebrow: 'COMPANY ROLES',
      title: 'Roles',
      description:
        'Create company roles and control what users can see and access.',
    },
    workspace: {
      eyebrow: 'WORKSPACE',
      title: 'Workspace',
      description:
        'Connect ERP and existing software through APIs and import CSV data for Phoenix modules.',
    },
    kpi: {
      eyebrow: 'COMPANY KPI',
      title: 'KPI',
      description:
        'Role-based KPI visibility for users across the company.',
    },
    reporting: {
      eyebrow: 'COMPANY REPORTING',
      title: 'Reporting',
      description:
        'Company-wide reports filtered by the permissions of the current user.',
    },
    activity: {
      eyebrow: 'COMPANY ACTIVITY',
      title: 'Activity',
      description:
        'Company-wide audit and activity history.',
    },
    settings: {
      eyebrow: 'COMPANY SETTINGS',
      title: 'Company Settings',
      description:
        'Configure settings for the current company.',
    },
    connect: {
      eyebrow: 'PHOENIX CONNECT',
      title: 'Phoenix Connect',
      description:
        'Company communication and integration services.',
    },
  }

  const selectedPlaceholder =
    view !== 'home' &&
    view !== 'company' &&
    view !== 'users'
      ? placeholderTitles[view]
      : null

  return (
    <div className="shell company-platform-shell">
      <aside>
        <div className="brand">
          <img
            src="/phoenix.png"
            alt="Phoenix"
          />

          <strong>PHOENIX</strong>
        </div>

        <div className="platform-title">
          COMPANY PLATFORM
        </div>

        <nav>
          <button
            type="button"
            className={
              view === 'home'
                ? 'active'
                : ''
            }
            onClick={() =>
              setView('home')
            }
          >
            <span className="company-nav-icon">ï¿½</span>
            Home
          </button>

          {navigation.map((item) => (
            <button
              key={item.view}
              type="button"
              className={
                view === item.view
                  ? 'active'
                  : ''
              }
              onClick={() => {
                setNotificationsOpen(false)
                setView(item.view)
              }}
            >
              <span className="company-nav-icon">
                {item.icon}
              </span>

              {item.label}
            </button>
          ))}
        </nav>

        <div className="side-foot">
          CORE V1.0.0
        </div>
      </aside>

      <main>
        <header className="company-topbar">
          <div className="company-topbar-heading">
            <span className="eyebrow">
              PHOENIX
            </span>

            <h2>
              Company Platform
            </h2>
          </div>

          <div className="company-topbar-actions">
            <div className="company-search">
              <span
                className="company-search-icon"
                aria-hidden="true"
              >
                ?
              </span>

              <input
                type="search"
                placeholder="Search company..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>

            <button
              type="button"
              className="company-ai-button"
              title="Phoenix AI"
              onClick={() => {
                setNotificationsOpen(false)
              }}
            >
              <span>?</span>
              AI
            </button>

            <div className="company-notification-wrap">
              <button
                type="button"
                className={
                  notificationsOpen
                    ? 'company-icon-button active'
                    : 'company-icon-button'
                }
                title="Company notifications"
                aria-label="Company notifications"
                onClick={() =>
                  setNotificationsOpen(
                    !notificationsOpen,
                  )
                }
              >
                <svg
                  className="company-bell-icon"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"
                  />
                  <path
                    d="M10 21h4"
                  />
                </svg>

                <span className="company-notification-dot" />
              </button>

              {notificationsOpen && (
                <div className="company-notification-panel">
                  <div className="company-notification-header">
                    <div>
                      <span className="eyebrow">
                        COMPANY
                      </span>

                      <strong>
                        Notifications
                      </strong>
                    </div>

                    <button
                      type="button"
                      className="company-notification-close"
                      onClick={() =>
                        setNotificationsOpen(false)
                      }
                    >
                      ï¿½
                    </button>
                  </div>

                  <div className="company-notification-empty">
                    <div className="company-notification-empty-icon">
                      ?
                    </div>

                    <strong>
                      No new notifications
                    </strong>

                    <span>
                      Company notifications will appear
                      here.
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="company-profile-wrap">
              <button
                type="button"
                className={
                  profileOpen
                    ? 'company-profile-button active'
                    : 'company-profile-button'
                }
                onClick={() => {
                  setNotificationsOpen(false)
                  setProfileOpen(!profileOpen)
                }}
                aria-label="User profile"
                aria-expanded={profileOpen}
              >
                <span className="company-profile-avatar">
                  {String(
                    context.user.display_name || '?',
                  )
                    .trim()
                    .charAt(0)
                    .toUpperCase()}
                </span>

                <span className="company-profile-name">
                  {context.user.display_name}
                </span>

                <span className="company-profile-chevron">
                  {profileOpen ? '^' : '?'}
                </span>
              </button>

              {profileOpen && (
                <div className="company-profile-menu">
                  <div className="company-profile-menu-header">
                    <span className="company-profile-avatar large">
                      {String(
                        context.user.display_name || '?',
                      )
                        .trim()
                        .charAt(0)
                        .toUpperCase()}
                    </span>

                    <div>
                      <strong>
                        {context.user.display_name}
                      </strong>

                      <span>
                        Company Administrator
                      </span>
                    </div>
                  </div>

                  <div className="company-profile-menu-divider" />

                  <button
                    type="button"
                    className="company-profile-menu-item"
                    onClick={() => {
                      setProfileOpen(false)
                    }}
                  >
                    <span>?</span>
                    Profile
                  </button>

                  <button
                    type="button"
                    className="company-profile-menu-item"
                    onClick={() => {
                      setProfileOpen(false)
                      setView('settings')
                    }}
                  >
                    <span>?</span>
                    Settings
                  </button>

                  <div className="company-profile-menu-divider" />

                  <button
                    type="button"
                    className="company-profile-menu-item signout"
                    onClick={onLogout}
                  >
                    <span>?</span>
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <section className="content">
          {view === 'home' && (
            <CompanyHome
              context={context}
            />
          )}

          {view === 'company' && (
            <CompanyDetails
              context={context}
            />
          )}

          {view === 'users' && (
            <CompanyUsers />
          )}

          {view === 'roles' && (
            <Roles />
          )}
          {selectedPlaceholder && view !== 'roles' && (
            <Placeholder
              eyebrow={selectedPlaceholder.eyebrow}
              title={selectedPlaceholder.title}
              description={
                selectedPlaceholder.description
              }
            />
          )}
        </section>
      </main>
    </div>
  )
}
function CompanyHome({
  context,
}: {
  context: Context
}) {
  const activeModules =
    context.modules.filter(
      (module) => module.active,
    )

  return (
    <>
      <div className="company-home-heading">
        <div>
          <span className="eyebrow">
            COMPANY OVERVIEW
          </span>

          <h1>
            Welcome, {context.user.display_name}
          </h1>

          <p className="muted">
            Read-only operational visibility for
            your company and your permitted KPIs.
          </p>
        </div>
      </div>

      <div className="company-home-grid">
        <div className="panel company-home-kpi-panel">
          <div className="company-home-panel-heading">
            <div>
              <span className="eyebrow">KPI</span>
              <h3>Your operational KPIs</h3>
            </div>

            <span className="company-readonly-badge">
              VIEW ONLY
            </span>
          </div>

          <div className="company-kpi-empty">
            <div className="company-kpi-symbol">?</div>

            <strong>Role-based KPIs</strong>

            <span>
              KPIs assigned to your company role
              will appear here.
            </span>
          </div>
        </div>

        <div className="panel company-home-status-panel">
          <div className="company-home-panel-heading">
            <div>
              <span className="eyebrow">
                COMPANY STATUS
              </span>
              <h3>Operational status</h3>
            </div>
          </div>

          <div className="company-status-list">
            <div className="company-status-item">
              <span>Company</span>
              <strong>
                {context.company?.name || 'Current company'}
              </strong>
            </div>

            <div className="company-status-item">
              <span>Company status</span>
              <strong>
                {context.company?.status || 'UNKNOWN'}
              </strong>
            </div>

            <div className="company-status-item">
              <span>Active modules</span>
              <strong>{activeModules.length}</strong>
            </div>

            <div className="company-status-item">
              <span>Access mode</span>
              <strong>READ ONLY</strong>
            </div>
          </div>
        </div>

        <div className="panel company-home-modules-panel">
          <div className="company-home-panel-heading">
            <div>
              <span className="eyebrow">
                ACTIVE MODULES
              </span>
              <h3>Available to your company</h3>
            </div>

            <span className="company-count-badge">
              {activeModules.length}
            </span>
          </div>

          {activeModules.length === 0 ? (
            <div className="company-kpi-empty compact">
              <strong>No active modules</strong>
              <span>
                Activated Phoenix modules will
                appear here.
              </span>
            </div>
          ) : (
            <div className="company-module-list">
              {activeModules.map((module) => (
                <div
                  className="company-module-status-row"
                  key={module.id}
                >
                  <div>
                    <strong>{module.name}</strong>
                    <span>
                      {module.code} ï¿½ v{module.version}
                    </span>
                  </div>

                  <span className="company-status-pill active">
                    ACTIVE
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel company-home-integration-panel">
          <div className="company-home-panel-heading">
            <div>
              <span className="eyebrow">
                WORKSPACE / API
              </span>
              <h3>Integration status</h3>
            </div>
          </div>

          <div className="company-integration-grid">
            <div>
              <span className="field-label">
                API connection
              </span>

              <strong>Not connected</strong>

              <span className="company-info-note">
                Workspace integration is not yet
                configured.
              </span>
            </div>

            <div>
              <span className="field-label">
                Last company sync
              </span>

              <strong>Not available</strong>

              <span className="company-info-note">
                A real timestamp will appear once
                Workspace sync is configured.
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="company-readonly-notice">
        <span>?</span>

        <div>
          <strong>
            Company Platform is view only
          </strong>

          <span>
            Business transactions and operational
            actions are performed in the User
            Platform according to the user's role
            and permissions.
          </span>
        </div>
      </div>
    </>
  )
}
function CompanyDetails({
  context,
}: {
  context: Context
}) {
  return (
    <div className="panel">
      <h3>
        Company details
      </h3>

      <div className="list">
        <strong>
          {context.company?.name}
        </strong>

        <span>
          Code: {context.company?.code}
        </span>

        <span>
          Status: {context.company?.status}
        </span>
      </div>
    </div>
  )
}

function CompanyUsers() {
  const [users, setUsers] =
    useState<any[]>([])

  const [selectedUserId, setSelectedUserId] =
    useState<string | null>(null)
  const [showUserDetail, setShowUserDetail] =
    useState(false)

  const [userAccess, setUserAccess] =
    useState<any | null>(null)
const [accessLoading, setAccessLoading] =
    useState(false)
  const [passwordResetting, setPasswordResetting] =
    useState(false)

  const [passwordMode, setPasswordMode] =
    useState<'generated' | 'manual'>('generated')

  const [resetPassword, setResetPassword] =
    useState('')

  const [showResetPassword, setShowResetPassword] =
    useState(false)

  const [copiedPassword, setCopiedPassword] =
    useState(false)

  const generateTemporaryPassword = () => {
    const chars =
      'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%'

    const values = new Uint32Array(16)
    crypto.getRandomValues(values)

    return Array.from(
      values,
      (value) => chars[value % chars.length],
    ).join('')
  }

  const prepareGeneratedPassword = () => {
    setResetPassword(generateTemporaryPassword())
    setShowResetPassword(true)
    setCopiedPassword(false)
    setMessage('')
  }

  const resetUserPassword = async () => {
    if (!selectedUserId) {
      return
    }

    if (!resetPassword || resetPassword.length < 12) {
      setMessage('Password must be at least 12 characters.')
      return
    }

    setPasswordResetting(true)
    setMessage('')
    setCopiedPassword(false)

    try {
      await api(
        `/api/v1/company/users/${selectedUserId}/reset-password`,
        {
          method: 'POST',
          body: JSON.stringify({
            password: resetPassword,
          }),
        },
      )

      setMessage(
        'Password reset successfully. The user must change it at next sign-in.',
      )
    } catch (passwordError) {
      setMessage(
        passwordError instanceof Error
          ? passwordError.message
          : 'Unable to reset the user password.',
      )
    } finally {
      setPasswordResetting(false)
    }
  }

  const copyResetPassword = async () => {
    if (!resetPassword) {
      return
    }

    try {
      await navigator.clipboard.writeText(resetPassword)
      setCopiedPassword(true)
      setMessage('Password copied to clipboard.')
    } catch {
      setMessage('Unable to copy the password.')
    }
  }

  const loadUserAccess = async (
    userId: string,
  ) => {
    setAccessLoading(true)
    setMessage('')

    try {
      const data = await api(
        `/api/v1/company/users/${userId}/access`,
      )

      setUserAccess(
        data.data || data,
      )
    } catch (accessError) {
      setMessage(
        accessError instanceof Error
          ? accessError.message
          : 'Unable to load user access.',
      )
    } finally {
      setAccessLoading(false)
    }
  }
  const [search, setSearch] =
    useState('')

  const [showAdd, setShowAdd] =
    useState(false)
  const [form, setForm] =
    useState({
      username: '',
      display_name: '',
      password: '',
    })

  const [message, setMessage] =
    useState('')

  const load = async () => {
    try {
      const data =
        await api(
          '/api/v1/company/users',
        )

      const items =
        Array.isArray(data)
          ? data
          : Array.isArray(data.data?.items)
            ? data.data.items
            : Array.isArray(data.items)
              ? data.items
              : []

      setUsers(items)

    } catch (loadError) {
      setMessage(
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load users.',
      )
    }
  }



  useEffect(() => {
    void load()
  }, [])

  const add = async () => {
    if (
      !form.username.trim() ||
      !form.display_name.trim() ||
      !form.password
    ) {
      setMessage(
        'Username, display name and password are required.',
      )

      return
    }

    try {
      await api(
        '/api/v1/company/users',
        {
          method: 'POST',
          body: JSON.stringify(form),
        },
      )

      setForm({
        username: '',
        display_name: '',
        password: '',
      })

      setMessage('User created.')

      setShowAdd(false)

      await load()
    } catch (addError) {
      setMessage(
        addError instanceof Error
          ? addError.message
          : 'Unable to create user.',
      )
    }
  }

  const filteredUsers =
    users.filter((user) => {
      const term =
        search.trim().toLowerCase()

      if (!term) {
        return true
      }

      return (
        String(user.display_name || '')
          .toLowerCase()
          .includes(term) ||
        String(user.username || '')
          .toLowerCase()
          .includes(term)
      )
    })

  const selectedUser =
    users.find(
      (user) =>
        user.id === selectedUserId,
    ) || null

  return (
    <>
      <div className="company-page-heading">
        <div>
          <span className="eyebrow">
            COMPANY USERS
          </span>

          <h1>Users</h1>

          <p className="muted">
            Manage users belonging to
            this company.
          </p>
        </div>

        <button
          type="button"
          className="company-primary-action"
          onClick={() => {
            setMessage('')
            setShowAdd(true)
          }}
        >
          + Add User
        </button>
      </div>

      {message && (
        <div className="company-feedback">
          {message}
        </div>
      )}

      {!showUserDetail ? (
        <div className="panel company-users-table-panel">
          <div className="company-users-list-header">
            <div>
              <span className="eyebrow">
                COMPANY USERS
              </span>

              <h2>
                Users
              </h2>
            </div>

            <div className="company-user-search">
              <input
                type="search"
                placeholder="Search users..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>
          </div>

          <div className="company-users-table-wrap">
            <table className="company-users-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Username</th>
                  <th>Account Status</th>
                  <th>Membership</th>
                  <th>Platform Level</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="company-users-empty"
                    >
                      No users found.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <div className="company-user-table-name">
                          <span className="company-user-avatar">
                            {String(
                              user.display_name ||
                                user.username ||
                                '?',
                            )
                              .trim()
                              .charAt(0)
                              .toUpperCase()}
                          </span>

                          <strong>
                            {user.display_name ||
                              user.username}
                          </strong>
                        </div>
                      </td>

                      <td>
                        @{user.username}
                      </td>

                      <td>
                        <span className="status-pill">
                          {user.user_status}
                        </span>
                      </td>

                      <td>
                        {user.membership_status}
                      </td>

                      <td>
                        {user.platform_level}
                      </td>

                      <td>
                        <button
                          type="button"
                          className="small-btn"
                          onClick={() => {
                            setSelectedUserId(user.id)
                            setShowUserDetail(true)
                            setUserAccess(null)
                            setPasswordMode('generated')
                            setResetPassword(
                              generateTemporaryPassword(),
                            )
                            setShowResetPassword(false)
                            setCopiedPassword(false)
                            void loadUserAccess(user.id)
                            setMessage('')
                          }}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : selectedUser ? (
        <div className="panel company-user-detail-view">
          <div className="company-user-detail-header">
            <button
              type="button"
              className="small-btn"
              onClick={() => {
                setShowUserDetail(false)
                setMessage('')
              }}
            >
              ? Back to Users
            </button>

            <div className="company-user-detail-profile">
              <span className="company-user-avatar">
                {String(
                  selectedUser.display_name ||
                    selectedUser.username ||
                    '?',
                )
                  .trim()
                  .charAt(0)
                  .toUpperCase()}
              </span>

              <div>
                <span className="eyebrow">
                  USER DETAILS
                </span>

                <h2>
                  {selectedUser.display_name}
                </h2>

                <p>
                  @{selectedUser.username}
                </p>
              </div>
            </div>
          </div>

          <div className="company-user-status-strip">
            <div>
              <span className="field-label">
                Account status
              </span>

              <strong>
                {selectedUser.user_status}
              </strong>
            </div>

            <div>
              <span className="field-label">
                Company membership
              </span>

              <strong>
                {selectedUser.membership_status}
              </strong>
            </div>

            <div>
              <span className="field-label">
                Platform level
              </span>

              <strong>
                {selectedUser.platform_level}
              </strong>
            </div>
          </div>

          <div className="company-user-detail-section">
            <span className="eyebrow">
              ACCOUNT
            </span>

            <div className="company-detail-grid">
              <div>
                <span className="field-label">
                  Username
                </span>

                <strong>
                  {selectedUser.username}
                </strong>
              </div>

              <div>
                <span className="field-label">
                  Display name
                </span>

                <strong>
                  {selectedUser.display_name}
                </strong>
              </div>
            </div>
          </div>

          {accessLoading && (
            <div className="company-feedback">
              Loading user access...
            </div>
          )}

          {userAccess && (
            <>
              <div className="company-user-detail-section">
                <div className="section-heading-row">
                  <span className="eyebrow">
                    ASSIGNED ROLES
                  </span>

                  <span className="muted">
                    Read-only
                  </span>
                </div>

                {userAccess.roles?.length ? (
                  <div className="company-detail-grid">
                    {userAccess.roles.map(
                      (role: any) => (
                        <div key={role.id}>
                          <span className="field-label">
                            {role.scope}
                          </span>

                          <strong>
                            {role.code}
                          </strong>

                          <p className="muted">
                            {role.name}
                          </p>
                        </div>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="muted">
                    No roles are currently assigned.
                  </p>
                )}
              </div>

              <div className="company-user-detail-section">
                <div className="section-heading-row">
                  <span className="eyebrow">
                    EFFECTIVE PERMISSIONS
                  </span>

                  <span className="muted">
                    Read-only
                  </span>
                </div>

                {userAccess.permissions?.length ? (
                  <div className="company-permission-grid">
                    {userAccess.permissions.map(
                      (permission: any) => (
                        <div
                          key={permission.id}
                          className="company-permission-item"
                        >
                          <strong>
                            {permission.code}
                          </strong>

                          <span>
                            {permission.name}
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="muted">
                    No effective permissions are currently assigned.
                  </p>
                )}
              </div>

              <div className="company-user-detail-section">
                <span className="eyebrow">
                  PASSWORD MANAGEMENT
                </span>

                <div className="company-access-role-row">
                  <select
                    className="company-input"
                    value={passwordMode}
                    onChange={(event) => {
                      const mode =
                        event.target.value as
                          | 'generated'
                          | 'manual'

                      setPasswordMode(mode)
                      setCopiedPassword(false)
                      setMessage('')

                      if (mode === 'generated') {
                        setResetPassword(
                          generateTemporaryPassword(),
                        )
                        setShowResetPassword(true)
                      } else {
                        setResetPassword('')
                        setShowResetPassword(false)
                      }
                    }}
                    disabled={passwordResetting}
                  >
                    <option value="generated">
                      Generate Temporary Password
                    </option>

                    <option value="manual">
                      Enter Password Manually
                    </option>
                  </select>

                  {passwordMode === 'generated' && (
                    <button
                      type="button"
                      className="small-btn"
                      onClick={prepareGeneratedPassword}
                      disabled={passwordResetting}
                    >
                      Generate
                    </button>
                  )}
                </div>

                <div className="company-user-password-row">
                  <input
                    className="company-input"
                    type={
                      showResetPassword
                        ? 'text'
                        : 'password'
                    }
                    value={resetPassword}
                    onChange={(event) => {
                      setResetPassword(event.target.value)
                      setCopiedPassword(false)
                    }}
                    placeholder="Minimum 12 characters"
                    disabled={passwordResetting}
                  />

                  <button
                    type="button"
                    className="small-btn"
                    onClick={() =>
                      setShowResetPassword(
                        (current) => !current,
                      )
                    }
                    disabled={!resetPassword}
                  >
                    {showResetPassword
                      ? 'Hide'
                      : 'Show'}
                  </button>

                  <button
                    type="button"
                    className="small-btn"
                    onClick={copyResetPassword}
                    disabled={!resetPassword}
                  >
                    {copiedPassword
                      ? 'Copied'
                      : 'Copy'}
                  </button>
                </div>

                <div className="company-password-actions">
                  <button
                    type="button"
                    className="company-primary-action"
                    onClick={resetUserPassword}
                    disabled={
                      passwordResetting ||
                      !resetPassword ||
                      resetPassword.length < 12
                    }
                  >
                    {passwordResetting
                      ? 'Resetting...'
                      : 'Reset Password'}
                  </button>
                </div>

                <p className="muted company-password-help">
                  Resetting the password revokes the user's
                  active sessions and requires a password
                  change at the next sign-in.
                </p>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="panel company-user-detail-view">
          <button
            type="button"
            className="small-btn"
            onClick={() => setShowUserDetail(false)}
          >
            ? Back to Users
          </button>
        </div>
      )}
      {showAdd && (
        <div
          className="company-modal-backdrop"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              setShowAdd(false)
            }
          }}
        >
          <div className="company-modal">
            <div className="company-modal-header">
              <div>
                <span className="eyebrow">
                  COMPANY USERS
                </span>

                <h2>
                  Add User
                </h2>
              </div>

              <button
                type="button"
                className="company-modal-close"
                onClick={() =>
                  setShowAdd(false)
                }
              >
                ï¿½
              </button>
            </div>

            <div className="company-modal-body">
              <label>
                Username

                <input
                  value={form.username}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      username:
                        event.target.value,
                    })
                  }
                  placeholder="username"
                />
              </label>

              <label>
                Display name

                <input
                  value={form.display_name}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      display_name:
                        event.target.value,
                    })
                  }
                  placeholder="Full name"
                />
              </label>

              <label>
                Temporary password

                <input
                  type="password"
                  value={form.password}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      password:
                        event.target.value,
                    })
                  }
                  placeholder="Minimum 12 characters"
                />
              </label>
            </div>

            <div className="company-modal-footer">
              <button
                type="button"
                className="company-secondary-action"
                onClick={() =>
                  setShowAdd(false)
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className="company-primary-action"
                onClick={add}
              >
                Create User
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
function CompanyModules({
  context,
}: {
  context: Context
}) {
  const activeModules =
    context.modules.filter(
      (module) => module.active,
    )

  return (
    <>
      <div className="hero">
        <span className="eyebrow">
          BUSINESS MODULES
        </span>

        <h1>
          Activated modules
        </h1>

        <p className="muted">
          Modules made available to
          this company by Phoenix.
        </p>
      </div>

      <div className="grid">
        {activeModules.length > 0 ? (
          activeModules.map(
            (module) => (
              <div
                className="module"
                key={module.code}
              >
                <span>
                  ACTIVE
                </span>

                <h3>
                  {module.name}
                </h3>

                <p>
                  Version{' '}
                  {module.version}
                </p>
              </div>
            ),
          )
        ) : (
          <div className="panel">
            No active modules.
          </div>
        )}
      </div>
    </>
  )
}

/* -------------------------------------------------------------------------- */
/* USER PLATFORM                                                              */
/* -------------------------------------------------------------------------- */

function UserShell({
  context,
  onLogout,
}: {
  context: Context
  onLogout: () => void
}) {
  const [view, setView] =
    useState<UserView>('home')

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
          <button
            type="button"
            className={
              view === 'home'
                ? 'active'
                : ''
            }
            onClick={() =>
              setView('home')
            }
          >
            Home
          </button>

          <button
            type="button"
            className={
              view === 'modules'
                ? 'active'
                : ''
            }
            onClick={() =>
              setView('modules')
            }
          >
            My Modules
          </button>
        </nav>

        <div className="side-foot">
          CORE V1.0.0
        </div>
      </aside>

      <main>
        <header>
          <div>
            <span className="eyebrow">
              PHOENIX
            </span>

            <h2>
              User Platform
            </h2>
          </div>

          <div className="account">
            <span>
              {context.user.display_name}
            </span>

            <button
              type="button"
              onClick={logout}
            >
              Sign out
            </button>
          </div>
        </header>

        <section className="content">
          {view === 'home' && (
            <UserHome
              context={context}
            />
          )}

          {view === 'modules' && (
            <UserModules
              context={context}
            />
          )}
        </section>
      </main>
    </div>
  )
}

function UserHome({
  context,
}: {
  context: Context
}) {
  return (
    <div className="hero">
      <span className="eyebrow">
        USER PLATFORM
      </span>

      <h1>
        Welcome,{' '}
        {context.user.display_name}
      </h1>

      <p className="muted">
        Access the Phoenix business
        modules available to you.
      </p>
    </div>
  )
}

function UserModules({
  context,
}: {
  context: Context
}) {
  const activeModules =
    context.modules.filter(
      (module) => module.active,
    )

  const openModule = (
    module: Module,
  ) => {
    alert(
      `${module.name} is ready to be integrated as a business module.`,
    )
  }

  return (
    <>
      <div className="hero">
        <span className="eyebrow">
          MY MODULES
        </span>

        <h1>
          Available modules
        </h1>

        <p className="muted">
          Select a module activated
          for your company.
        </p>
      </div>

      <div className="grid">
        {activeModules.length > 0 ? (
          activeModules.map(
            (module) => (
              <button
                type="button"
                className="module clickable"
                key={module.code}
                onClick={() =>
                  openModule(module)
                }
              >
                <span>
                  OPEN MODULE
                </span>

                <h3>
                  {module.name}
                </h3>

                <p>
                  Launch workspace ?
                </p>
              </button>
            ),
          )
        ) : (
          <div className="panel">
            No active modules are
            assigned to this company.
          </div>
        )}
      </div>
    </>
  )
}

/* -------------------------------------------------------------------------- */
/* PLACEHOLDER                                                                */
/* -------------------------------------------------------------------------- */

function Placeholder({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description: string
}) {
  return (
    <div className="hero">
      <span className="eyebrow">
        {eyebrow}
      </span>

      <h1>
        {title}
      </h1>

      <p className="muted">
        {description}
      </p>

      <div className="panel">
        <p>
          This section is part of the
          Phoenix Beta platform structure.
        </p>

        <p className="muted">
          Functionality will be
          implemented incrementally on
          top of Phoenix Core.
        </p>
      </div>
    </div>
  )
}

const rootElement =
  document.getElementById('root')

if (!rootElement) {
  throw new Error(
    'Phoenix application root element was not found.',
  )
}

createRoot(rootElement).render(
  <StrictMode>
    <PlatformProvider>
      <App />
    </PlatformProvider>
  </StrictMode>,
)
