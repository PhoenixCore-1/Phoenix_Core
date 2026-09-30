import { StrictMode, useEffect, useState } from 'react'
import * as XLSX from 'xlsx'
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
  | 'imports'
  | 'imports-customer'

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

    if (!context.company) {
      return <Login />
    }

    const companyContext: Context = {
      user: {
        id: context.user.id,
        username: context.user.username,
        display_name: context.user.display_name,
        platform_level: context.user.platform_level,
      },
      company: {
        id: context.company.id,
        code: context.company.code,
        name: context.company.name,
        status: context.company.status ?? 'UNKNOWN',
      },
      modules: context.modules.map((module) => ({
        id: module.id,
        code: module.code,
        name: module.name,
        version: module.version ?? '',
        active: module.active ?? false,
      })),
    }

    return (
      <CompanyShell
        context={companyContext}
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
            Phoenix Core Platform V{__APP_VERSION__}
          </span>

          <b>🔒</b>

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
          CORE V{__APP_VERSION__}
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
                🔒
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
function CompanyNavIcon({
  name,
}: {
  name: string
}) {
  const paths: Record<string, React.ReactNode> = {
    home: (
      <>
        <path d="M3 10.5 12 3l9 7.5" />
        <path d="M5 9.5V21h14V9.5" />
        <path d="M9 21v-7h6v7" />
      </>
    ),
    building: (
      <>
        <path d="M4 21V4h11v17" />
        <path d="M15 9h5v12" />
        <path d="M7 8h2M11 8h1M7 12h2M11 12h1M7 16h2M11 16h1" />
      </>
    ),
    users: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
        <circle cx="9.5" cy="7" r="3.5" />
        <path d="M17 11a3.5 3.5 0 0 0 0-7M21 21v-2a4 4 0 0 0-3-3.87" />
      </>
    ),
    shield: (
      <>
        <path d="M12 3 20 6v6c0 5-3.4 8.2-8 9-4.6-.8-8-4-8-9V6l8-3Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    file: (
      <>
        <path d="M6 3h8l4 4v14H6z" />
        <path d="M14 3v5h5M9 13h6M9 17h6" />
      </>
    ),
    scale: (
      <>
        <path d="M12 3v18M7 6h10M5 21h14" />
        <path d="m7 6-4 7h8L7 6ZM17 6l-4 7h8l-4-7Z" />
      </>
    ),
    activity: (
      <>
        <path d="M3 12h4l2-6 4 12 2-6h6" />
      </>
    ),
    briefcase: (
      <>
        <rect x="3" y="7" width="18" height="13" rx="2" />
        <path d="M8 7V5h8v2M3 12h18M10 12v2h4v-2" />
      </>
    ),
    chart: (
      <>
        <path d="M4 19V5M4 19h17" />
        <path d="m7 15 4-4 3 2 5-6" />
      </>
    ),
    report: (
      <>
        <path d="M5 20V10M12 20V4M19 20v-7" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4M8 8l4-4 4 4" />
        <path d="M5 13v6h14v-6" />
      </>
    ),
    plug: (
      <>
        <path d="M9 7V3M15 7V3M7 7h10v3a5 5 0 0 1-10 0V7ZM12 15v6" />
      </>
    ),
    link: (
      <>
        <path d="m10 13 4-4" />
        <path d="M7 17H6a4 4 0 0 1 0-8h3M17 7h1a4 4 0 0 1 0 8h-3" />
      </>
    ),
  }

  return (
    <svg
      className="company-nav-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] ?? paths.file}
    </svg>
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
  const [customerImportFile, setCustomerImportFile] =
    useState<File | null>(null)

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
    Exclude<
    CompanyView, 
    'home' | 'company' | 'users' | 'imports-customer'
    >,
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
    imports: {
      eyebrow: 'IMPORTS / EXPORTS',
      title: 'Imports / Exports',
      description:
        'Import and export company data while maintaining portable external references.',
    },
  }

  const selectedPlaceholder =
    view !== 'home' &&
    view !== 'company' &&
    view !== 'users' &&
    view !== 'imports-customer'
      ? placeholderTitles[view]
      : null

  const [expandedGroups, setExpandedGroups] =
    useState({
      core: true,
      governance: false,
      operations: false,
      platform: false,
    })

  const toggleGroup = (
    group:
      | 'core'
      | 'governance'
      | 'operations'
      | 'platform',
  ) => {
    setExpandedGroups((current) => ({
      ...current,
      [group]: !current[group],
    }))
  }
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


        <nav className="company-sidebar-nav">

          <div className="company-nav-group">

            <button
              type="button"
              className="company-nav-group-header"
              aria-expanded={expandedGroups.core}
              onClick={() => toggleGroup('core')}
            >
              <span>CORE</span>

              <span className="company-nav-group-chevron">
                {expandedGroups.core ? '−' : '+'}
              </span>
            </button>

            {expandedGroups.core && (
              <div className="company-nav-group-items">

                <button
                  type="button"
                  className={
                    view === 'home'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('home')}
                >
                  <CompanyNavIcon name="home" />
                  Home
                </button>

                <button
                  type="button"
                  className={
                    view === 'company'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('company')}
                >
                  <CompanyNavIcon name="building" />
                  Company Profile
                </button>

                <button
                  type="button"
                  className={
                    view === 'users'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('users')}
                >
                  <CompanyNavIcon name="users" />
                  Users
                </button>

                <button
                  type="button"
                  className={
                    view === 'roles'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('roles')}
                >
                  <CompanyNavIcon name="shield" />
                  Roles
                </button>

              </div>
            )}

          </div>

          <div className="company-nav-group">

            <button
              type="button"
              className="company-nav-group-header"
              aria-expanded={expandedGroups.governance}
              onClick={() => toggleGroup('governance')}
            >
              <span>GOVERNANCE</span>

              <span className="company-nav-group-chevron">
                {expandedGroups.governance ? '−' : '+'}
              </span>
            </button>

            {expandedGroups.governance && (
              <div className="company-nav-group-items">

                <button
                  type="button"
                  className="company-nav-placeholder"
                  disabled
                >
                  <CompanyNavIcon name="file" />
                  Documents
                </button>

                <button
                  type="button"
                  className="company-nav-placeholder"
                  disabled
                >
                  <CompanyNavIcon name="scale" />
                  Legal &amp; Governance
                </button>

                <button
                  type="button"
                  className={
                    view === 'activity'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('activity')}
                >
                  <CompanyNavIcon name="activity" />
                  Activity
                </button>

              </div>
            )}

          </div>

          <div className="company-nav-group">

            <button
              type="button"
              className="company-nav-group-header"
              aria-expanded={expandedGroups.operations}
              onClick={() => toggleGroup('operations')}
            >
              <span>OPERATIONS</span>

              <span className="company-nav-group-chevron">
                {expandedGroups.operations ? '−' : '+'}
              </span>
            </button>

            {expandedGroups.operations && (
              <div className="company-nav-group-items">

                <button
                  type="button"
                  className={
                    view === 'workspace'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('workspace')}
                >
                  <CompanyNavIcon name="briefcase" />
                  Workspace
                </button>

                <button
                  type="button"
                  className={
                    view === 'kpi'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('kpi')}
                >
                  <CompanyNavIcon name="chart" />
                  KPI
                </button>

                <button
                  type="button"
                  className={
                    view === 'reporting'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('reporting')}
                >
                  <CompanyNavIcon name="report" />
                  Reporting
                </button>

              </div>
            )}

          </div>

          <div className="company-nav-group">

            <button
              type="button"
              className="company-nav-group-header"
              aria-expanded={expandedGroups.platform}
              onClick={() => toggleGroup('platform')}
            >
              <span>PLATFORM</span>

              <span className="company-nav-group-chevron">
                {expandedGroups.platform ? '−' : '+'}
              </span>
            </button>

            {expandedGroups.platform && (
              <div className="company-nav-group-items">

                <button
                  type="button"
                  className={
                    view === 'settings'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('settings')}
                >
                  <CompanyNavIcon name="settings" />
                  Company Settings
                </button>

                <button
                  type="button"
                  className={
                    view === 'imports'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('imports')}
                >
                  <CompanyNavIcon name="upload" />
                  Imports / Exports
                </button>

                <button
                  type="button"
                  className="company-nav-placeholder"
                  disabled
                >
                  <CompanyNavIcon name="plug" />
                  API / Integrations
                </button>

                <button
                  type="button"
                  className={
                    view === 'connect'
                      ? 'active'
                      : ''
                  }
                  onClick={() => setView('connect')}
                >
                  <CompanyNavIcon name="link" />
                  Phoenix Connect
                </button>

              </div>
            )}

          </div>

        </nav>

        <div className="side-foot">
          CORE V{__APP_VERSION__}
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
                <svg
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                >
                  <circle
                    cx="11"
                    cy="11"
                    r="6.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />
                  <path
                    d="M16 16l5 5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
              </span>

              <input
                type="search"
                placeholder="Search company..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                aria-label="Search Company Platform"
              />

              {search.trim() && (
                <div className="company-search-results">
                  {[
                    { view: 'home' as CompanyView, label: 'Home' },
                    { view: 'company' as CompanyView, label: 'Company Profile' },
                    { view: 'users' as CompanyView, label: 'Users' },
                    { view: 'roles' as CompanyView, label: 'Roles' },
                    { view: 'activity' as CompanyView, label: 'Activity' },
                    { view: 'workspace' as CompanyView, label: 'Workspace' },
                    { view: 'kpi' as CompanyView, label: 'KPI' },
                    { view: 'reporting' as CompanyView, label: 'Reporting' },
                    { view: 'settings' as CompanyView, label: 'Company Settings' },
                    { view: 'connect' as CompanyView, label: 'Phoenix Connect' },
                  ]
                    .filter((item) =>
                      item.label
                        .toLowerCase()
                        .includes(search.trim().toLowerCase()),
                    )
                    .map((item) => (
                      <button
                        key={item.view}
                        type="button"
                        className="company-search-result"
                        onClick={() => {
                          setView(item.view)
                          setSearch('')
                        }}
                      >
                        {item.label}
                      </button>
                    ))}

                  {[
                    { view: 'home' as CompanyView, label: 'Home' },
                    { view: 'company' as CompanyView, label: 'Company Profile' },
                    { view: 'users' as CompanyView, label: 'Users' },
                    { view: 'roles' as CompanyView, label: 'Roles' },
                    { view: 'activity' as CompanyView, label: 'Activity' },
                    { view: 'workspace' as CompanyView, label: 'Workspace' },
                    { view: 'kpi' as CompanyView, label: 'KPI' },
                    { view: 'reporting' as CompanyView, label: 'Reporting' },
                    { view: 'settings' as CompanyView, label: 'Company Settings' },
                    { view: 'connect' as CompanyView, label: 'Phoenix Connect' },
                  ].filter((item) =>
                    item.label
                      .toLowerCase()
                      .includes(search.trim().toLowerCase()),
                  ).length === 0 && (
                    <div className="company-search-no-results">
                      No Company Platform results
                    </div>
                  )}
                </div>
              )}
            </div>
            <button
              type="button"
              className="company-ai-button"
              title="Phoenix AI"
              onClick={() => {
                setNotificationsOpen(false)
              }}
            >
              <svg
                className="company-ai-icon"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinejoin="round"
                />
                <path
                  d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
              </svg>
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
                      <svg
                        className="company-notification-close-icon"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          d="M6 6l12 12M18 6L6 18"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                        />
                      </svg>
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
                  <span className="company-profile-chevron" aria-hidden="true">                     <svg                       viewBox="0 0 24 24"                       width="16"                       height="16"                     >                       <path                         d={profileOpen ? "M6 14l6-6 6 6" : "M6 10l6 6 6-6"}                         fill="none"                         stroke="currentColor"                         strokeWidth="2"                         strokeLinecap="round"                         strokeLinejoin="round"                       />                     </svg>                   </span>
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
                    <span aria-hidden="true">                       <svg viewBox="0 0 24 24" width="18" height="18">                         <circle cx="12" cy="8" r="3.5" fill="none" stroke="currentColor" strokeWidth="1.8" />                         <path d="M5 20c1.5-4 4-6 7-6s5.5 2 7 6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />                       </svg>                     </span>
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
                    <span aria-hidden="true">                       <svg viewBox="0 0 24 24" width="18" height="18">                         <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" />                         <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />                       </svg>                     </span>
                    Settings
                  </button>

                  <div className="company-profile-menu-divider" />

                  <button
                    type="button"
                    className="company-profile-menu-item signout"
                    onClick={onLogout}
                  >
                    <span aria-hidden="true">                       <svg viewBox="0 0 24 24" width="18" height="18">                         <path d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />                         <path d="M13 8l4 4-4 4M9 12h8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />                       </svg>                     </span>
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
          {view === 'imports-customer' ? (
            <CustomerMasterImport
              file={customerImportFile}
              onFileChange={setCustomerImportFile}
              onBack={() => setView('imports')}
            />
          ) : null}

          {view === 'imports' ? (
            <ImportsExportsLanding
              onImportCustomer={() => setView('imports-customer')}
            />
          ) : (
            selectedPlaceholder && view !== 'roles' && (
              <Placeholder
                eyebrow={selectedPlaceholder.eyebrow}
                title={selectedPlaceholder.title}
                description={
                  selectedPlaceholder.description
                }
              />
            )
          )}
        </section>
      </main>
    </div>
  )
}
type CustomerImportRow = {
  rowNumber: number
  values: unknown[]
  status: 'VALID' | 'INVALID'
  errors: string[]
  warnings: string[]
}

type CustomerImportValidationResult = {
  headers: string[]
  totalRows: number
  validRows: number
  invalidRows: number
  rows: CustomerImportRow[]
  previewRows: CustomerImportRow[]
}

async function parseCustomerMasterFile(
  file: File,
): Promise<CustomerImportValidationResult> {
  const buffer = await file.arrayBuffer()

  const workbook = XLSX.read(buffer, {
    type: 'array',
    cellDates: true,
  })

  if (workbook.SheetNames.length === 0) {
    throw new Error('The file does not contain a worksheet.')
  }

  const sheetName =
    workbook.SheetNames.includes('Customers')
      ? 'Customers'
      : workbook.SheetNames[0]

  const sheet = workbook.Sheets[sheetName]

  if (!sheet) {
    throw new Error('The customer worksheet could not be read.')
  }

  const matrix = XLSX.utils.sheet_to_json<unknown[]>(sheet, {
    header: 1,
    defval: null,
    raw: true,
  })

  if (matrix.length === 0) {
    throw new Error('The selected file contains no rows.')
  }

  const headers = (matrix[0] ?? []).map((value) =>
    String(value ?? '').trim(),
  )

  const customerIdIndex = headers.indexOf('Customer ID')
  const customerNameIndex = headers.indexOf('Customer name')

  const missingColumns: string[] = []

  if (customerIdIndex === -1) {
    missingColumns.push('Customer ID')
  }

  if (customerNameIndex === -1) {
    missingColumns.push('Customer name')
  }

  if (missingColumns.length > 0) {
    throw new Error(
      `Missing required column(s): ${missingColumns.join(', ')}`,
    )
  }

  const sourceRows = matrix.slice(1)
  const customerIds = new Map<string, number>()

  sourceRows.forEach((values, index) => {
    const rawId = values[customerIdIndex]
    const customerId = String(rawId ?? '').trim()

    if (customerId && !customerIds.has(customerId)) {
      customerIds.set(customerId, index + 2)
    }
  })

  const rows: CustomerImportRow[] = sourceRows.map(
    (values, index) => {
      const rowNumber = index + 2
      const errors: string[] = []
      const warnings: string[] = []

      const customerId = String(
        values[customerIdIndex] ?? '',
      ).trim()

      const customerName = String(
        values[customerNameIndex] ?? '',
      ).trim()

      if (!customerId) {
        errors.push('Customer ID is required.')
      } else {
        const firstRow = customerIds.get(customerId)

        if (
          firstRow !== undefined &&
          firstRow !== rowNumber
        ) {
          errors.push(
            `Duplicate Customer ID "${customerId}" also appears on row ${firstRow}.`,
          )
        }
      }

      if (!customerName) {
        errors.push('Customer name is required.')
      }

      return {
        rowNumber,
        values,
        status:
          errors.length === 0
            ? 'VALID'
            : 'INVALID',
        errors,
        warnings,
      }
    },
  )

  const validRows = rows.filter(
    (row) => row.status === 'VALID',
  ).length

  const invalidRows = rows.length - validRows

  return {
    headers,
    totalRows: rows.length,
    validRows,
    invalidRows,
    rows,
    previewRows: rows.slice(0, 25),
  }
}
function CustomerMasterImport({
  file,
  onFileChange,
  onBack,
}: {
  file: File | null
  onFileChange: (file: File | null) => void
  onBack: () => void
}) {
  const [validationResult, setValidationResult] =
    useState<CustomerImportValidationResult | null>(null)
  const [validating, setValidating] = useState(false)
  const [validationError, setValidationError] =
    useState<string | null>(null)
  const [confirmationRequested, setConfirmationRequested] = useState(false)
  const handleFileChange = (nextFile: File | null) => {
    setValidationResult(null)
    setValidationError(null)
    setConfirmationRequested(false)
    onFileChange(nextFile)
  }

  const handleContinue = async () => {
    if (!file) {
      return
    }

    setValidating(true)
    setValidationError(null)
    setValidationResult(null)
    setConfirmationRequested(false)

    try {
      const result = await parseCustomerMasterFile(file)
      setValidationResult(result)
    } catch (error) {
      setValidationError(
        error instanceof Error
          ? error.message
          : 'The Customer Master file could not be validated.',
      )
    } finally {
      setValidating(false)
    }
  }

  return (
    <div className="company-placeholder customer-master-import">
      <div className="company-placeholder-header">
        <div>
          <div className="company-placeholder-eyebrow">CUSTOMER MASTER</div>
          <h2>Import Customer Master</h2>
          <p>
            Select a Customer Master file to begin validation. Nothing is imported until you explicitly confirm the import.
          </p>
        </div>
      </div>

      <div className="imports-section">
        <div className="imports-section-heading">
          <h3>Select file</h3>
          <p>Supported formats: Excel (.xlsx) and CSV (.csv).</p>
        </div>

        <div className="imports-card customer-import-file-card">
          <div>
            <strong>
              {file ? file.name : 'No file selected'}
            </strong>
            <p>
              {file
                ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                : 'Choose a Customer Master file to continue.'}
            </p>
          </div>

          <label className="imports-file-button">
            Choose File
            <input
              type="file"
              accept=".xlsx,.csv"
              onChange={(event) =>
                handleFileChange(event.target.files?.[0] ?? null)
              }
            />
          </label>
        </div>
      </div>

      {validationError ? (
        <div className="imports-card customer-import-validation-error">
          <strong>Validation failed</strong>
          <p>{validationError}</p>
        </div>
      ) : null}

      {validationResult ? (
        <div className="imports-section customer-import-validation">
          <div className="imports-section-heading">
            <h3>Validation result</h3>
            <p>
              {validationResult.invalidRows > 0
                ? 'Import blocked. All rows must pass validation before the import can be confirmed.'
                : 'Validation passed. The file is ready for preview and confirmation.'}
            </p>
          </div>

          <div className="imports-card-grid">
            <div className="imports-card">
              <div>
                <strong>Total rows</strong>
                <p>Customer records detected in the file.</p>
              </div>
              <strong>{validationResult.totalRows}</strong>
            </div>

            <div className="imports-card">
              <div>
                <strong>Valid rows</strong>
                <p>Rows that passed all blocking validation rules.</p>
              </div>
              <strong>{validationResult.validRows}</strong>
            </div>

            <div className="imports-card">
              <div>
                <strong>Invalid rows</strong>
                <p>Rows containing one or more blocking errors.</p>
              </div>
              <strong>{validationResult.invalidRows}</strong>
            </div>
          </div>

          <div className="imports-card">
            <strong>
              {validationResult.invalidRows > 0
                ? 'Import blocked'
                : 'Validation passed'}
            </strong>
            <p>
              {validationResult.invalidRows > 0
                ? 'No customer records will be written until every validation error has been resolved.'
                : 'No customer records have been imported yet. Confirmation remains a separate step.'}
            </p>
          </div>
        </div>
      ) : null}
      {validationResult ? (
        

      <div className="customer-import-preview">
            <div className="imports-section-heading">
              <h3>Preview</h3>
              <p>Showing the first {validationResult.previewRows.length} rows from the validated file.</p>
            </div>

            <div className="customer-import-preview-wrap">
              <table className="customer-import-preview-table">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Status</th>
                    <th>Customer ID</th>
                    <th>Customer name</th>
                    <th>Validation issues</th>
                  </tr>
                </thead>
                <tbody>
                  {validationResult.previewRows.map((row) => {
                    const customerIdIndex =
                      validationResult.headers.indexOf('Customer ID')
                    const customerNameIndex =
                      validationResult.headers.indexOf('Customer name')

                    return (
                      <tr key={row.rowNumber}>
                        <td>{row.rowNumber}</td>
                        <td>
                          <span
                            className={
                              row.status === 'VALID'
                                ? 'customer-import-status valid'
                                : 'customer-import-status invalid'
                            }
                          >
                            {row.status}
                          </span>
                        </td>
                        <td>
                          {String(
                            row.values[customerIdIndex] ?? '',
                          )}
                        </td>
                        <td>
                          {String(
                            row.values[customerNameIndex] ?? '',
                          )}
                        </td>
                        <td>
                          {row.errors.length > 0
                            ? row.errors.join(' ')
                            : row.warnings.length > 0
                              ? row.warnings.join(' ')
                              : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
      ) : null}

          <div className="customer-import-actions">
        <button
          type="button"
          className="secondary-btn"
          onClick={onBack}
        >
          Back
        </button>
        <button
          type="button"
          className="primary-btn"
          disabled={!file || validating}
          onClick={handleContinue}
        >
          {validating ? 'Validating...' : 'Continue'}
        </button>

        {validationResult && validationResult.invalidRows === 0 ? (
          <button
            type="button"
            className="primary-btn customer-import-confirmation"
            onClick={() => setConfirmationRequested(true)}
          >
            Confirm Import
          </button>
        ) : null}
      </div>

      {confirmationRequested ? (
        <div className="customer-import-confirmation-panel">
          <strong>Import confirmation requested</strong>
          <p>
            The file has passed validation. No customer records have been
            written yet. The next step will create an Import Job and perform
            the atomic commit.
          </p>
        </div>
      ) : null}
    </div>
  )
}
function ImportsExportsLanding({
  onImportCustomer,
}: {
  onImportCustomer: () => void
}) {

  return (
    <div className="company-placeholder imports-exports-landing">
      <div className="company-placeholder-header">
        <div>
          <div className="company-placeholder-eyebrow">IMPORTS / EXPORTS</div>
          <h2>Imports / Exports</h2>
          <p>
            Import and export company master data while maintaining portable external references.
          </p>
        </div>
      </div>
      <div className="imports-section">
        <div className="imports-section-heading">
          <h3>Master Data Imports</h3>
          <p>Load reference data used by Phoenix modules and future domain platforms.</p>
        </div>

        <div className="imports-card-grid">
          <div className="imports-card">
            <div>
              <strong>Customer Master</strong>
              <p>Customer reference data for CRM 360.</p>
            </div>
            <button
              type="button"
              onClick={onImportCustomer}
            >
              Import Customer Master
            </button>
            </div>
            <div className="imports-card">
              <div>
                <strong>Product / Item Master</strong>
                <p>Product and item reference data for Inventory 360.</p>
              </div>
              <button type="button" disabled>
                Import Product / Item Master
              </button>
            </div>

          <div className="imports-card">
            <div>
              <strong>Warehouse Master</strong>
              <p>Warehouse reference data for Warehouse 360.</p>
            </div>
            <span className="imports-card-status">Coming with Warehouse 360</span>
          </div>
        </div>
      </div>

      <div className="imports-section">
        <div className="imports-section-heading">
          <h3>Import History</h3>
          <p>Review previous uploads, validation results and import activity.</p>
        </div>

        <div className="imports-card imports-history-card">
          <div>
            <strong>Import History</strong>
            <p>Every confirmed import will retain its validation and processing history.</p>
          </div>
          <button type="button" disabled>
            View Import History
          </button>
        </div>
      </div>
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
                      {module.code} 🔒 v{module.version}
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

  const [companyRoles, setCompanyRoles] =
    useState<any[]>([])

  const [rolesLoading, setRolesLoading] =
    useState(false)

  const [roleChanging, setRoleChanging] =
    useState(false)

  const [selectedRoleId, setSelectedRoleId] =
    useState('')
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

  const loadCompanyRoles = async () => {
    setRolesLoading(true)

    try {
      const data = await api(
        '/api/v1/company/roles',
      )

      const items =
        Array.isArray(data)
          ? data
          : Array.isArray(data.data?.items)
            ? data.data.items
            : Array.isArray(data.items)
              ? data.items
              : []

      setCompanyRoles(
        items.filter(
          (role: any) =>
            role.code !== 'COMPANY.ADMIN' &&
            role.status !== 'DISABLED',
        ),
      )
    } catch (roleError) {
      setMessage(
        roleError instanceof Error
          ? roleError.message
          : 'Unable to load company roles.',
      )
    } finally {
      setRolesLoading(false)
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

  const assignRole = async () => {
    if (!userAccess?.membership?.id || !selectedRoleId) {
      return
    }

    setRoleChanging(true)
    setMessage('')

    try {
      await api(
        `/api/v1/company/memberships/${userAccess.membership.id}/roles/${selectedRoleId}`,
        {
          method: 'POST',
        },
      )

      setSelectedRoleId('')
      setMessage('Role assigned successfully.')

      await loadUserAccess(selectedUserId as string)
    } catch (roleError) {
      setMessage(
        roleError instanceof Error
          ? roleError.message
          : 'Unable to assign role.',
      )
    } finally {
      setRoleChanging(false)
    }
  }

  const removeRole = async (roleId: string) => {
    if (!userAccess?.membership?.id) {
      return
    }

    setRoleChanging(true)
    setMessage('')

    try {
      await api(
        `/api/v1/company/memberships/${userAccess.membership.id}/roles/${roleId}`,
        {
          method: 'DELETE',
        },
      )

      setMessage('Role removed successfully.')

      await loadUserAccess(selectedUserId as string)
    } catch (roleError) {
      setMessage(
        roleError instanceof Error
          ? roleError.message
          : 'Unable to remove role.',
      )
    } finally {
      setRoleChanging(false)
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
                            void loadCompanyRoles()
                            setSelectedRoleId('')
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
                    Manage access through roles
                  </span>
                </div>

                {userAccess.roles?.length ? (
                  <div className="company-detail-grid">
                    {userAccess.roles.map(
                      (role: any) => (
                        <div
                          key={role.id}
                          className="company-access-role-row"
                        >
                           <div className="company-role-content">
                            <span className="field-label">
                              {role.scope}
                            </span>

                             <strong className="company-role-code">
                              {role.code}
                             </strong>

                             <p className="muted company-role-name">
                              {role.name}
                             </p>
                           </div>

                          {role.code !== 'COMPANY.ADMIN' && (
                            <button
                              type="button"
                               className="small-btn company-role-remove"
                              disabled={roleChanging}
                              onClick={() =>
                                void removeRole(role.id)
                              }
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      ),
                    )}
                  </div>
                ) : (
                  <p className="muted">
                    No roles are currently assigned.
                  </p>
                )}

                <div className="company-add-role-row">
                  <select
                    className="company-input"
                    value={selectedRoleId}
                    disabled={
                      rolesLoading ||
                      roleChanging
                    }
                    onChange={(event) =>
                      setSelectedRoleId(
                        event.target.value,
                      )
                    }
                  >
                    <option value="">
                      {rolesLoading
                        ? 'Loading roles...'
                        : 'Select a role to assign'}
                    </option>

                    {companyRoles
                      .filter(
                        (role: any) =>
                          !userAccess.roles?.some(
                            (assignedRole: any) =>
                              assignedRole.id ===
                              role.id,
                          ),
                      )
                      .map((role: any) => (
                        <option
                          key={role.id}
                          value={role.id}
                        >
                          {role.name} ({role.code})
                        </option>
                      ))}
                  </select>

                  <button
                    type="button"
                    className="company-primary-action"
                    disabled={
                      !selectedRoleId ||
                      rolesLoading ||
                      roleChanging
                    }
                    onClick={() =>
                      void assignRole()
                    }
                  >
                    {roleChanging
                      ? 'Saving...'
                      : 'Add Role'}
                  </button>
                </div>
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
                🔒
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
          CORE V{__APP_VERSION__}
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
              onClick={onLogout}
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














