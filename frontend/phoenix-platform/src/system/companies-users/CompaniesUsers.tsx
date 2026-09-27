import { useEffect, useState } from 'react'
import { api } from '../../core/api'

type Company = {
  id: string
  code: string
  name: string
  status: string
}

type CompanyAdminAccess = {
  company: Company
  admin: CompanyAdmin | null
  role: {
    id: string
    code: string
    name: string
    scope: string
    status: string
  } | null
  permissions: Array<{
    id: string
    code: string
    name: string
  }>
}
type CompanyAdmin = {
  id: string
  identity_id: string
  username: string
  display_name: string
  status: string
  platform_level: string
  password_reset_required: number
  created_at: string
  membership_id: string
  membership_status: string
}

function generateTemporaryPassword() {
  const chars =
    'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%'

  const values = new Uint32Array(16)
  crypto.getRandomValues(values)

  return Array.from(
    values,
    (value) => chars[value % chars.length],
  ).join('')
}

export function CompaniesUsers() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [companyId, setCompanyId] = useState('')
  const [admin, setAdmin] = useState<CompanyAdmin | null>(null)
  const [adminAccess, setAdminAccess] =
    useState<CompanyAdminAccess | null>(null)

  const [viewingAdmin, setViewingAdmin] = useState(false)
  const [accessLoading, setAccessLoading] = useState(false)

  const [loading, setLoading] = useState(true)
  const [adminLoading, setAdminLoading] = useState(false)
  const [resetting, setResetting] = useState(false)

  const [resetMode, setResetMode] =
    useState<'generate' | 'manual'>('generate')

  const [resetPassword, setResetPassword] = useState('')
  const [revealedPassword, setRevealedPassword] = useState('')
  const [passwordCopied, setPasswordCopied] = useState(false)
  const [message, setMessage] = useState('')

  async function loadCompanies() {
    setLoading(true)
    setMessage('')

    try {
      const response = await api('/api/v1/system/companies')

      const items = Array.isArray(response?.items)
        ? response.items as Company[]
        : []

      setCompanies(items)

      if (!companyId && items.length > 0) {
        const activeCompany = items.find(
          (company) => company.status === 'ACTIVE',
        )

        setCompanyId(activeCompany?.id ?? items[0].id)
      }
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to load companies.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function loadCompanyAdmin(
    selectedCompanyId: string,
  ) {
    if (!selectedCompanyId) {
      setAdmin(null)
      return
    }

    setAdminLoading(true)
    setMessage('')

    try {
      const response = await api(
        `/api/v1/system/companies/${selectedCompanyId}/admin`,
      )

      setAdmin(response?.admin ?? null)
    } catch (error) {
      setAdmin(null)

      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to load Company Administrator.',
      )
    } finally {
      setAdminLoading(false)
    }
  }

  useEffect(() => {
    void loadCompanies()
  }, [])

  useEffect(() => {
    if (companyId) {
      void loadCompanyAdmin(companyId)
    }
  }, [companyId])

  async function viewAdminAccess() {
    if (!companyId || !admin) {
      return
    }

    setAccessLoading(true)
    setMessage('')

    try {
      const response = await api(
        `/api/v1/system/companies/${companyId}/admin/access`,
      )

      setAdminAccess(response as CompanyAdminAccess)
      setViewingAdmin(true)
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to load Company Administrator access.',
      )
    } finally {
      setAccessLoading(false)
    }
  }
  async function copyPassword() {
    if (!revealedPassword) {
      return
    }

    try {
      await navigator.clipboard.writeText(revealedPassword)
      setPasswordCopied(true)
    } catch {
      setMessage('Unable to copy password automatically.')
    }
  }

  async function resetAdminPassword() {
    if (!companyId || !admin) {
      setMessage(
        'Please select a company with a Company Administrator.',
      )
      return
    }

    let newPassword = resetPassword

    if (resetMode === 'generate') {
      newPassword = generateTemporaryPassword()
    }

    if (newPassword.length < 12) {
      setMessage('Password must be at least 12 characters.')
      return
    }

    setResetting(true)
    setMessage('')

    try {
      await api(
        `/api/v1/system/users/${admin.id}/reset-password`,
        {
          method: 'POST',
          body: JSON.stringify({
            organisation_id: companyId,
            password: newPassword,
          }),
        },
      )

      setResetPassword('')
      setRevealedPassword(newPassword)
      setPasswordCopied(false)
      setMessage('')

      await loadCompanyAdmin(companyId)
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to reset Company Administrator password.',
      )
    } finally {
      setResetting(false)
    }
  }

  return (
    <section className="page companies-users-page">
      <div className="page-header">
        <div>
          <h1>Companies User</h1>
          <p>
            Manage the Company Administrator created for each
            Phoenix company.
          </p>
        </div>
      </div>

      {message && (
        <div className="notice">
          {message}
        </div>
      )}

      {adminAccess && viewingAdmin && (
        <div className="password-reset-modal-backdrop">
          <div className="password-reset-modal">
            <div className="password-reset-modal-header">
              <div>
                <span className="eyebrow">ACCESS</span>
                <h3>Company Administrator Access</h3>
              </div>
            </div>

            <div className="company-admin-summary">
              <div className="company-admin-summary-item">
                <span>User</span>
                <strong>
                  {adminAccess.admin?.display_name}
                </strong>
              </div>

              <div className="company-admin-summary-item">
                <span>Username</span>
                <strong>
                  {adminAccess.admin?.username}
                </strong>
              </div>

              <div className="company-admin-summary-item">
                <span>Role</span>
                <strong>
                  {adminAccess.role?.name ?? 'No role assigned'}
                </strong>
              </div>

              <div className="company-admin-summary-item">
                <span>Role Code</span>
                <strong>
                  {adminAccess.role?.code ?? '—'}
                </strong>
              </div>

              <div className="company-admin-summary-item">
                <span>Scope</span>
                <strong>
                  {adminAccess.role?.scope ?? '—'}
                </strong>
              </div>
            </div>

            <div className="password-security-section">
              <div className="password-security-heading">
                <span className="eyebrow">
                  EFFECTIVE PERMISSIONS
                </span>
                <h3>
                  Permissions inherited from role
                </h3>
              </div>

              {adminAccess.permissions.length === 0 ? (
                <p className="muted">
                  No permissions are assigned.
                </p>
              ) : (
                <div className="company-admin-permissions">
                  {adminAccess.permissions.map((permission) => (
                    <div
                      key={permission.id}
                      className="company-admin-permission"
                    >
                      <strong>{permission.name}</strong>
                      <span>{permission.code}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="password-reset-modal-actions">
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setViewingAdmin(false)
                  setAdminAccess(null)
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
      {revealedPassword && (
        <div className="password-reset-modal-backdrop">
          <div className="password-reset-modal">
            <div className="password-reset-modal-header">
              <div>
                <span className="eyebrow">PASSWORD RESET</span>
                <h3>Password Reset Successful</h3>
              </div>
            </div>

            <p className="muted">
              A new password has been set for {admin?.username}.
            </p>

            <label className="password-reset-modal-label">
              <span>New Password</span>
              <input
                type="text"
                value={revealedPassword}
                readOnly
                autoFocus
              />
            </label>

            <p className="muted">
              This password will be required at next login.
            </p>

            <div className="password-reset-modal-actions">
              <button
                type="button"
                className="primary"
                onClick={() => void copyPassword()}
              >
                {passwordCopied ? 'Password Copied' : 'Copy Password'}
              </button>

              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setRevealedPassword('')
                  setPasswordCopied(false)
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="panel-header">
          <div>
            <h2>Company</h2>
            <p>
              Select a company to manage its Company
              Administrator.
            </p>
          </div>
        </div>

        {loading ? (
          <p>Loading companies...</p>
        ) : (
          <div className="companies-users-form-grid">
            <label>
              <span>Company</span>

              <select
                value={companyId}
                onChange={(event) =>
                  setCompanyId(event.target.value)
                }
                disabled={resetting}
              >
                <option value="">Select company</option>

                {companies
                  .filter(
                    (company) => company.status === 'ACTIVE',
                  )
                  .map((company) => (
                    <option
                      key={company.id}
                      value={company.id}
                    >
                      {company.name} ({company.code})
                    </option>
                  ))}
              </select>
            </label>
          </div>
        )}
      </div>

      {companyId && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2>Company Administrator</h2>
              <p>
                System Administrators can manage the Company
                Administrator only. Company users are managed
                from the Company Platform.
              </p>
            </div>
          </div>

          {adminLoading ? (
            <p>Loading Company Administrator...</p>
          ) : !admin ? (
            <p className="muted">
              No Company Administrator exists for this company.
            </p>
          ) : (
            <>
              <div className="company-admin-actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => void viewAdminAccess()}
                  disabled={accessLoading}
                >
                  {accessLoading ? 'Loading...' : 'View'}
                </button>
              </div>
              <div className="company-admin-summary">
                <div className="company-admin-summary-item">
                  <span>Display Name</span>
                  <strong>{admin.display_name}</strong>
                </div>

                <div className="company-admin-summary-item">
                  <span>Username</span>
                  <strong>{admin.username}</strong>
                </div>

                <div className="company-admin-summary-item">
                  <span>Account Status</span>
                  <strong>{admin.status}</strong>
                </div>

                <div className="company-admin-summary-item">
                  <span>Password Reset Required</span>
                  <strong>
                    {admin.password_reset_required ? 'YES' : 'NO'}
                  </strong>
                </div>
              </div>

              <div className="password-security-section">
                <div className="password-security-heading">
                  <span className="eyebrow">ACCOUNT SECURITY</span>
                  <h3>Password</h3>
                </div>

                <div className="password-security-grid">
                <label>
                  <span>Password Reset Method</span>

                  <select
                    value={resetMode}
                    onChange={(event) =>
                      setResetMode(
                        event.target.value as 'generate' | 'manual',
                      )
                    }
                    disabled={resetting}
                  >
                    <option value="generate">
                      Generate Temporary Password
                    </option>

                    <option value="manual">
                      Enter Password Manually
                    </option>
                  </select>
                </label>

                {resetMode === 'manual' && (
                  <label>
                    <span>New Password</span>

                    <input
                      type="password"
                      value={resetPassword}
                      onChange={(event) =>
                        setResetPassword(event.target.value)
                      }
                      disabled={resetting}
                      autoComplete="new-password"
                      placeholder="Minimum 12 characters"
                    />
                  </label>
                )}
                </div>

                <div className="password-security-actions">
                  <button
                    type="button"
                    onClick={() => void resetAdminPassword()}
                    disabled={resetting}
                  >
                    {resetting ? 'Resetting...' : 'Reset Password'}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  )
}





