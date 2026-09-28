import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  CompanyPermission,
  CompanyRole,
  getCompanyPermissions,
  getCompanyRolePermissions,
  getCompanyRoles,
  grantCompanyRolePermission,
  revokeCompanyRolePermission,
} from "./api";

export default function Roles() {
  const [roles, setRoles] = useState<CompanyRole[]>([]);
  const [selectedRole, setSelectedRole] = useState<CompanyRole | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadRoles() {
      try {
        setLoading(true);
        setError(null);

        const data = await getCompanyRoles();

        if (!cancelled) {
          setRoles(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Unable to load roles."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadRoles();

    return () => {
      cancelled = true;
    };
  }, []);

  if (selectedRole) {
    return (
      <RoleDetails
        role={selectedRole}
        onBack={() => setSelectedRole(null)}
      />
    );
  }

  const systemRoles = roles.filter(
    (role) =>
      role.scope.toUpperCase() === "SYSTEM" ||
      role.code.toUpperCase() === "COMPANY.ADMIN"
  );

  const companyRoles = roles.filter(
    (role) =>
      role.scope.toUpperCase() !== "SYSTEM" &&
      role.code.toUpperCase() !== "COMPANY.ADMIN"
  );

  if (loading) {
    return (
      <section className="company-page">
        <PageHeader />
        <div className="company-card company-loading-card">
          <p>Loading roles...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="company-page">
        <PageHeader />
        <div className="company-card company-error-card">
          <p>{error}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="company-page">
      <PageHeader />

      <RoleSection
        title="System & Protected Roles"
        description="Platform-defined roles managed by Phoenix."
        roles={systemRoles}
        protectedRoles
        emptyMessage="No system roles found."
        onView={setSelectedRole}
      />

      <RoleSection
        title="Company Roles"
        description="Organisation-defined roles and access assignments."
        roles={companyRoles}
        action={
          <button type="button" className="company-primary-button">
            + Create Role
          </button>
        }
        emptyMessage="No company roles have been created."
        emptyDescription="Create a role to define custom access for your organisation."
        onView={setSelectedRole}
      />
    </section>
  );
}

function PageHeader() {
  return (
    <div className="company-page-header">
      <div>
        <div className="company-page-eyebrow">ACCESS CONTROL</div>
        <h1>Roles</h1>
        <p>Manage organisation roles and access.</p>
      </div>
    </div>
  );
}

function RoleSection({
  title,
  description,
  roles,
  protectedRoles = false,
  action,
  emptyMessage,
  emptyDescription,
  onView,
}: {
  title: string;
  description: string;
  roles: CompanyRole[];
  protectedRoles?: boolean;
  action?: ReactNode;
  emptyMessage: string;
  emptyDescription?: string;
  onView: (role: CompanyRole) => void;
}) {
  return (
    <div className="company-card company-role-card">
      <div className="company-section-header company-role-section-header">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>

        {action}
      </div>

      {roles.length === 0 ? (
        <div className="company-empty-state">
          <p>{emptyMessage}</p>
          {emptyDescription && <span>{emptyDescription}</span>}
        </div>
      ) : (
        <RoleTable
          roles={roles}
          protectedRoles={protectedRoles}
          onView={onView}
        />
      )}
    </div>
  );
}

function RoleTable({
  roles,
  protectedRoles = false,
  onView,
}: {
  roles: CompanyRole[];
  protectedRoles?: boolean;
  onView: (role: CompanyRole) => void;
}) {
  return (
    <div className="company-table-wrapper">
      <table className="company-table company-role-table">
        <thead>
          <tr>
            <th>Role</th>
            <th>Code</th>
            <th>Scope</th>
            <th>Status</th>
            <th>Access</th>
            <th aria-label="Actions" />
          </tr>
        </thead>

        <tbody>
          {roles.map((role) => (
            <tr key={role.id}>
              <td>
                <div className="company-role-name">
                  <strong>{role.name}</strong>
                </div>
              </td>

              <td>
                <code className="company-role-code">{role.code}</code>
              </td>

              <td>
                <span className="company-scope-badge">{role.scope}</span>
              </td>

              <td>
                <StatusBadge status={role.status} />
              </td>

              <td>
                <span
                  className={
                    protectedRoles
                      ? "company-protection-badge company-protection-badge--protected"
                      : "company-protection-badge"
                  }
                >
                  {protectedRoles ? "Protected" : "Organisation"}
                </span>
              </td>

              <td className="company-role-action-cell">
                <button
                  type="button"
                  className="company-secondary-button"
                  onClick={() => onView(role)}
                >
                  {protectedRoles ? "Details" : "View"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RoleDetails({
  role,
  onBack,
}: {
  role: CompanyRole;
  onBack: () => void;
}) {
  const [permissions, setPermissions] = useState<CompanyPermission[]>([]);
  const [assignedPermissionIds, setAssignedPermissionIds] = useState<
    Set<string>
  >(new Set());
  const [loading, setLoading] = useState(true);
  const [savingPermissionId, setSavingPermissionId] = useState<string | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const protectedRole =
    role.scope.toUpperCase() === "SYSTEM" ||
    role.code.toUpperCase() === "COMPANY.ADMIN";

  useEffect(() => {
    let cancelled = false;

    async function loadPermissions() {
      try {
        setLoading(true);
        setError(null);

        const assigned = await getCompanyRolePermissions(role.id);

        if (cancelled) {
          return;
        }

        setAssignedPermissionIds(new Set(assigned.map((permission) => permission.id)));

        if (!protectedRole) {
          const available = await getCompanyPermissions();

          if (!cancelled) {
            setPermissions(available);
          }
        } else {
          setPermissions(assigned);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load role permissions."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPermissions();

    return () => {
      cancelled = true;
    };
  }, [role.id, protectedRole]);

  async function togglePermission(permission: CompanyPermission) {
    if (protectedRole || savingPermissionId) {
      return;
    }

    const currentlyAssigned = assignedPermissionIds.has(permission.id);

    try {
      setSavingPermissionId(permission.id);
      setError(null);

      if (currentlyAssigned) {
        await revokeCompanyRolePermission(role.id, permission.id);

        setAssignedPermissionIds((current) => {
          const next = new Set(current);
          next.delete(permission.id);
          return next;
        });
      } else {
        await grantCompanyRolePermission(role.id, permission.id);

        setAssignedPermissionIds((current) => {
          const next = new Set(current);
          next.add(permission.id);
          return next;
        });
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update role permission."
      );
    } finally {
      setSavingPermissionId(null);
    }
  }

  return (
    <section className="company-page">
      <div className="company-role-detail-header">
        <button
          type="button"
          className="company-secondary-button"
          onClick={onBack}
        >
          Back to Roles
        </button>

        <div className="company-role-detail-heading">
          <div className="company-page-eyebrow">ROLE DETAILS</div>
          <h1>{role.name}</h1>
          <p>{role.code}</p>
        </div>

        <span
          className={
            protectedRole
              ? "company-protection-badge company-protection-badge--protected"
              : "company-protection-badge"
          }
        >
          {protectedRole ? "Protected" : "Organisation Role"}
        </span>
      </div>

      <div className="company-role-detail-grid">
        <div className="company-card company-role-detail-card">
          <div className="company-detail-card-header">
            <div>
              <h2>Role Information</h2>
              <p>Identity and lifecycle information for this role.</p>
            </div>
          </div>

          <div className="company-role-meta-grid">
            <DetailItem label="Name" value={role.name} />
            <DetailItem label="Code" value={role.code} mono />
            <DetailItem label="Scope" value={role.scope} />
            <DetailItem label="Status" value={role.status} />
            <DetailItem
              label="Permissions"
              value={String(assignedPermissionIds.size)}
            />
          </div>
        </div>

        <div className="company-card company-role-detail-card">
          <div className="company-detail-card-header">
            <div>
              <h2>Permissions</h2>
              <p>
                {protectedRole
                  ? "Permissions assigned by Phoenix."
                  : "Select the permissions this company role should have."}
              </p>
            </div>
          </div>

          {loading ? (
            <div className="company-detail-loading">
              Loading permissions...
            </div>
          ) : error ? (
            <div className="company-detail-error">{error}</div>
          ) : permissions.length === 0 ? (
            <div className="company-empty-state">
              <p>No permissions available.</p>
              <span>This role currently has no permissions assigned.</span>
            </div>
          ) : (
            <div className="company-permission-list">
              {permissions.map((permission) => {
                const assigned = assignedPermissionIds.has(permission.id);
                const saving = savingPermissionId === permission.id;

                return (
                  <label
                    className="company-permission-row"
                    key={permission.id}
                  >
                    <input
                      type="checkbox"
                      checked={assigned}
                      disabled={protectedRole || savingPermissionId !== null}
                      onChange={() => togglePermission(permission)}
                    />

                    <div>
                      <strong>{permission.name}</strong>
                      <code>{permission.code}</code>
                    </div>

                    {saving && (
                      <span className="company-permission-saving">
                        Saving...
                      </span>
                    )}
                  </label>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
function DetailItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="company-role-detail-item">
      <span>{label}</span>
      {mono ? <code>{value}</code> : <strong>{value}</strong>}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase();

  return (
    <span
      className={`company-status-badge ${
        normalized === "ACTIVE"
          ? "company-status-badge--active"
          : "company-status-badge--inactive"
      }`}
    >
      <span className="company-status-dot" />
      {status}
    </span>
  );
}
