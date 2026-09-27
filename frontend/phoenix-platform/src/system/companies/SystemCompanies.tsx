import { useEffect, useMemo, useState } from 'react'
import { api } from '../../core/api'

type Company = {
  id: string
  code: string
  name: string
  status: string
  created_at?: string
  legal_name?: string
  trading_name?: string
  registration_number?: string
  tax_number?: string
  primary_email?: string
  telephone?: string
  website?: string
  address_line_1?: string
  address_line_2?: string
  city?: string
  province?: string
  postal_code?: string
  country?: string
  industry?: string
  company_type?: string
}

export function SystemCompanies() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const [showAddCompany, setShowAddCompany] = useState(false)
  const [statusAction, setStatusAction] = useState<'activate' | 'suspend' | null>(null)

  const [newCode, setNewCode] = useState('')
  const [newName, setNewName] = useState('')

  const [editName, setEditName] = useState('')
  const [editCode, setEditCode] = useState('')
  const [editLegalName, setEditLegalName] = useState('')
  const [editTradingName, setEditTradingName] = useState('')
  const [editCompanyType, setEditCompanyType] = useState('')
  const [editRegistrationNumber, setEditRegistrationNumber] = useState('')
  const [editTaxNumber, setEditTaxNumber] = useState('')
  const [editIndustry, setEditIndustry] = useState('')
  const [editWebsite, setEditWebsite] = useState('')
  const [editPrimaryEmail, setEditPrimaryEmail] = useState('')
  const [editTelephone, setEditTelephone] = useState('')
  const [editAddressLine1, setEditAddressLine1] = useState('')
  const [editAddressLine2, setEditAddressLine2] = useState('')
  const [editCity, setEditCity] = useState('')
  const [editProvince, setEditProvince] = useState('')
  const [editPostalCode, setEditPostalCode] = useState('')
  const [editCountry, setEditCountry] = useState('')

  async function loadCompanies() {
    setLoading(true)
    setMessage('')

    try {
      const response = await api('/api/v1/system/companies')
      const data = response?.items ?? []

      setCompanies(Array.isArray(data) ? data : [])

      if (!selectedCompanyId && Array.isArray(data) && data.length > 0) {
        setSelectedCompanyId(data[0].id)
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

  async function loadCompany(companyId: string) {
    setSelectedCompanyId(companyId)
    setDetailLoading(true)
    setMessage('')

    try {
      const response = await api(
        `/api/v1/system/companies/${companyId}`,
      )

      const company = response?.company as Company | undefined

      setSelectedCompany(company ?? null)

      setEditName(company?.name ?? '')
      setEditCode(company?.code ?? '')
      setEditLegalName(company?.legal_name ?? '')
      setEditTradingName(company?.trading_name ?? '')
      setEditCompanyType(company?.company_type ?? '')
      setEditRegistrationNumber(company?.registration_number ?? '')
      setEditTaxNumber(company?.tax_number ?? '')
      setEditIndustry(company?.industry ?? '')
      setEditWebsite(company?.website ?? '')
      setEditPrimaryEmail(company?.primary_email ?? '')
      setEditTelephone(company?.telephone ?? '')
      setEditAddressLine1(company?.address_line_1 ?? '')
      setEditAddressLine2(company?.address_line_2 ?? '')
      setEditCity(company?.city ?? '')
      setEditProvince(company?.province ?? '')
      setEditPostalCode(company?.postal_code ?? '')
      setEditCountry(company?.country ?? '')
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to load company.',
      )
    } finally {
      setDetailLoading(false)
    }
  }

  async function createCompany() {
    if (!newCode.trim() || !newName.trim()) {
      setMessage('Company code and company name are required.')
      return
    }

    setSaving(true)
    setMessage('')

    try {
      await api('/api/v1/system/companies', {
        method: 'POST',
        body: JSON.stringify({
          code: newCode.trim(),
          name: newName.trim(),
        }),
      })

      setNewCode('')
      setNewName('')
      setShowAddCompany(false)
      setMessage('Company created successfully.')

      await loadCompanies()
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to create company.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function changeCompanyStatus(
    action: 'activate' | 'suspend',
  ) {
    if (!selectedCompanyId) return

    setSaving(true)
    setMessage('')

    try {
      const endpoint =
        action === 'activate'
          ? 'activate'
          : 'suspend'

      await api(
        `/api/v1/system/companies/${selectedCompanyId}/${endpoint}`,
        {
          method: 'POST',
        },
      )

      setStatusAction(null)

      await loadCompanies()
      await loadCompany(selectedCompanyId)

      setMessage(
        action === 'activate'
          ? 'Company activated successfully.'
          : 'Company suspended successfully.',
      )
    } catch (error) {
      setStatusAction(null)
      setMessage(
        error instanceof Error
          ? error.message
          : action === 'activate'
            ? 'Unable to activate company.'
            : 'Unable to suspend company.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function saveCompany() {
    if (!selectedCompanyId) return

    if (!editName.trim() || !editCode.trim()) {
      setMessage('Company name and company code are required.')
      return
    }

    setSaving(true)
    setMessage('')

    try {
      await api(`/api/v1/system/companies/${selectedCompanyId}`, {
        method: 'PUT',
        body: JSON.stringify({
          code: editCode.trim(),
          name: editName.trim(),
          legal_name: editLegalName.trim(),
          trading_name: editTradingName.trim(),
          company_type: editCompanyType.trim(),
          registration_number: editRegistrationNumber.trim(),
          tax_number: editTaxNumber.trim(),
          industry: editIndustry.trim(),
          website: editWebsite.trim(),
          primary_email: editPrimaryEmail.trim(),
          telephone: editTelephone.trim(),
          address_line_1: editAddressLine1.trim(),
          address_line_2: editAddressLine2.trim(),
          city: editCity.trim(),
          province: editProvince.trim(),
          postal_code: editPostalCode.trim(),
          country: editCountry.trim(),
        }),
      })

      setMessage('Company changes saved successfully.')

      await loadCompanies()
      await loadCompany(selectedCompanyId)
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to save company.',
      )
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    void loadCompanies()
  }, [])

  useEffect(() => {
    if (selectedCompanyId) {
      void loadCompany(selectedCompanyId)
    }
  }, [selectedCompanyId])

  const filteredCompanies = useMemo(() => {
    const value = search.trim().toLowerCase()

    return companies.filter((company) => {
      const matchesSearch =
        !value ||
        company.name?.toLowerCase().includes(value) ||
        company.code?.toLowerCase().includes(value)

      const matchesStatus =
        statusFilter === 'ALL' ||
        company.status?.toUpperCase() === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [companies, search, statusFilter])

  return (
    <main className="companies-page">
      <div className="companies-page-header">
        <div>
          <div className="page-eyebrow">COMPANIES</div>
          <h1>Companies</h1>
          <p>
            Create and manage companies using the Phoenix Company
            Platform.
          </p>
        </div>
      </div>

      {message && (
        <div className="company-message" role="alert">
          {message}
        </div>
      )}

      <section className="companies-toolbar">
        <div className="company-search">
          <span>⌕</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search companies by name or code..."
          />
        </div>

        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="ALL">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="SUSPENDED">Suspended</option>
          <option value="CLOSED">Closed</option>
        </select>

        <button
          className="phoenix-primary-button"
          type="button"
          onClick={() => setShowAddCompany(true)}
        >
          + Add Company
        </button>
      </section>

      {showAddCompany && (
        <section className="add-company-panel">
          <div>
            <h2>Add Company</h2>
            <p>Create a new company on the Phoenix platform.</p>
          </div>

          <div className="company-form-grid">
            <label>
              Company Code
              <input
                value={newCode}
                onChange={(event) => setNewCode(event.target.value)}
                placeholder="e.g. ACME"
              />
            </label>

            <label>
              Company Name
              <input
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="e.g. Acme (Pty) Ltd"
              />
            </label>
          </div>

          <div className="company-form-actions">
            <button
              className="phoenix-primary-button"
              type="button"
              onClick={() => void createCompany()}
              disabled={saving}
            >
              {saving ? 'Creating...' : 'Create Company'}
            </button>

            <button
              className="phoenix-secondary-button"
              type="button"
              onClick={() => setShowAddCompany(false)}
            >
              Cancel
            </button>
          </div>
        </section>
      )}

      <section className="companies-workspace">
        <div className="companies-list-panel">
          <div className="companies-list-header">
            <h2>Companies ({filteredCompanies.length})</h2>
            <span>Sort by: Name</span>
          </div>

          {loading ? (
            <div className="company-empty-state">
              Loading companies...
            </div>
          ) : filteredCompanies.length === 0 ? (
            <div className="company-empty-state">
              No companies found.
            </div>
          ) : (
            <div className="company-list">
              {filteredCompanies.map((company) => {
                const selected = company.id === selectedCompanyId

                return (
                  <button
                    key={company.id}
                    type="button"
                    className={`company-list-item ${
                      selected ? 'selected' : ''
                    }`}
                    onClick={() => setSelectedCompanyId(company.id)}
                  >
                    <span className="company-list-icon">▦</span>

                    <span className="company-list-content">
                      <strong>{company.name}</strong>
                      <small>{company.code}</small>
                    </span>

                    <span
                      className={`company-status ${
                        company.status?.toLowerCase()
                      }`}
                    >
                      {company.status || 'UNKNOWN'}
                    </span>

                    <span className="company-chevron">›</span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="company-detail-panel">
          {detailLoading ? (
            <div className="company-empty-state">
              Loading company...
            </div>
          ) : !selectedCompany ? (
            <div className="company-empty-state">
              Select a company to view its details.
            </div>
          ) : (
            <>
              <div className="company-detail-header">
                <div className="company-detail-title">
                  <div className="company-large-icon">▦</div>

                  <div>
                    <div className="company-title-row">
                      <h2>{selectedCompany.name}</h2>

                      <span
                        className={`company-status ${
                          selectedCompany.status?.toLowerCase()
                        }`}
                      >
                        {selectedCompany.status || 'UNKNOWN'}
                      </span>
                    </div>

                    <p>
                      Code: {selectedCompany.code}
                      {selectedCompany.created_at
                        ? ` • Created ${new Date(
                            selectedCompany.created_at,
                          ).toLocaleDateString()}`
                        : ''}
                    </p>
                  </div>

                  <div className="company-detail-actions">
                    {selectedCompany.status?.toUpperCase() === 'ACTIVE' && (
                      <button
                        className="phoenix-secondary-button company-suspend-button"
                        type="button"
                        disabled={saving}
                        onClick={() => setStatusAction('suspend')}
                      >
                        Suspend Company
                      </button>
                    )}

                    {selectedCompany.status?.toUpperCase() === 'SUSPENDED' && (
                      <button
                        className="phoenix-primary-button"
                        type="button"
                        disabled={saving}
                        onClick={() => setStatusAction('activate')}
                      >
                        Activate Company
                      </button>
                    )}
                  </div>
                </div>
              </div>

              <div className="company-tabs">
                <button type="button" className="active">
                  Overview
                </button>
                <button type="button">Business Modules</button>
                <button type="button">Settings</button>
                <button type="button">Audit Log</button>
              </div>

              <div className="company-information-card">
                <div className="company-section-heading">
                  <div>
                    <h3>Company Details</h3>
                    <p>Core legal and business information.</p>
                  </div>
                </div>

                <div className="company-detail-form-grid">
                  <label>
                    Company Name
                    <input
                      value={editName}
                      onChange={(event) =>
                        setEditName(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Company Code
                    <input
                      value={editCode}
                      onChange={(event) =>
                        setEditCode(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Legal Name
                    <input
                      value={editLegalName}
                      onChange={(event) =>
                        setEditLegalName(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Trading Name
                    <input
                      value={editTradingName}
                      onChange={(event) =>
                        setEditTradingName(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Company Type
                    <input
                      value={editCompanyType}
                      onChange={(event) =>
                        setEditCompanyType(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Industry
                    <input
                      value={editIndustry}
                      onChange={(event) =>
                        setEditIndustry(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Registration Number
                    <input
                      value={editRegistrationNumber}
                      onChange={(event) =>
                        setEditRegistrationNumber(
                          event.target.value,
                        )
                      }
                    />
                  </label>

                  <label>
                    Tax Number
                    <input
                      value={editTaxNumber}
                      onChange={(event) =>
                        setEditTaxNumber(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Website
                    <input
                      value={editWebsite}
                      onChange={(event) =>
                        setEditWebsite(event.target.value)
                      }
                      placeholder="https://..."
                    />
                  </label>
                </div>
              </div>

              <div className="company-information-card">
                <div className="company-section-heading">
                  <div>
                    <h3>Primary Contact</h3>
                    <p>Main company contact information.</p>
                  </div>
                </div>

                <div className="company-detail-form-grid">
                  <label>
                    Primary Email
                    <input
                      type="email"
                      value={editPrimaryEmail}
                      onChange={(event) =>
                        setEditPrimaryEmail(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Telephone
                    <input
                      value={editTelephone}
                      onChange={(event) =>
                        setEditTelephone(event.target.value)
                      }
                    />
                  </label>
                </div>
              </div>

              <div className="company-information-card">
                <div className="company-section-heading">
                  <div>
                    <h3>Registered Address</h3>
                    <p>Official company address.</p>
                  </div>
                </div>

                <div className="company-detail-form-grid">
                  <label className="company-field-wide">
                    Address Line 1
                    <input
                      value={editAddressLine1}
                      onChange={(event) =>
                        setEditAddressLine1(event.target.value)
                      }
                    />
                  </label>

                  <label className="company-field-wide">
                    Address Line 2
                    <input
                      value={editAddressLine2}
                      onChange={(event) =>
                        setEditAddressLine2(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    City
                    <input
                      value={editCity}
                      onChange={(event) =>
                        setEditCity(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Province
                    <input
                      value={editProvince}
                      onChange={(event) =>
                        setEditProvince(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Postal Code
                    <input
                      value={editPostalCode}
                      onChange={(event) =>
                        setEditPostalCode(event.target.value)
                      }
                    />
                  </label>

                  <label>
                    Country
                    <input
                      value={editCountry}
                      onChange={(event) =>
                        setEditCountry(event.target.value)
                      }
                    />
                  </label>
                </div>
              </div>

              <div className="company-detail-save-bar">
                <button
                  className="phoenix-primary-button"
                  type="button"
                  onClick={() => void saveCompany()}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </>
          )}

          {statusAction && selectedCompany && (
            <div
              className="company-status-modal-backdrop"
              role="presentation"
              onClick={() => setStatusAction(null)}
            >
              <div
                className="company-status-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="company-status-title"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="company-status-modal-icon">
                  {statusAction === 'suspend' ? '!' : '✓'}
                </div>

                <p className="page-eyebrow">Company Lifecycle</p>

                <h2 id="company-status-title">
                  {statusAction === 'suspend'
                    ? `Suspend ${selectedCompany.name}?`
                    : `Activate ${selectedCompany.name}?`}
                </h2>

                <p>
                  {statusAction === 'suspend'
                    ? 'The company will no longer be treated as active on the Phoenix platform.'
                    : 'The company will be restored to active status on the Phoenix platform.'}
                </p>

                <div className="company-status-modal-actions">
                  <button
                    className="phoenix-secondary-button"
                    type="button"
                    disabled={saving}
                    onClick={() => setStatusAction(null)}
                  >
                    Cancel
                  </button>

                  <button
                    className={
                      statusAction === 'suspend'
                        ? 'phoenix-danger-button'
                        : 'phoenix-primary-button'
                    }
                    type="button"
                    disabled={saving}
                    onClick={() => void changeCompanyStatus(statusAction)}
                  >
                    {saving
                      ? 'Saving...'
                      : statusAction === 'suspend'
                        ? 'Suspend Company'
                        : 'Activate Company'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}