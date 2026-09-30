import { api } from "../../core/api/client";

export type CompanyRole = {
  id: string;
  organisation_id: string;
  code: string;
  name: string;
  scope: string;
  status: string;
  created_at: string;
};

export type CompanyPermission = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
};

type RolesResponse = {
  items: CompanyRole[];
};

type PermissionsResponse = {
  items: CompanyPermission[];
};

export async function getCompanyRoles(): Promise<CompanyRole[]> {
  const response = await api<RolesResponse>("/api/v1/company/roles");
  return response.items ?? [];
}

export async function createCompanyRole(
  code: string,
  name: string
): Promise<CompanyRole> {
  const response = await api<CompanyRole>("/api/v1/company/roles", {
    method: "POST",
    body: JSON.stringify({
      code,
      name,
    }),
  });

  return response;
}
export async function getCompanyRolePermissions(
  roleId: string
): Promise<CompanyPermission[]> {
  const response = await api<PermissionsResponse>(
    `/api/v1/company/roles/${roleId}/permissions`
  );

  return response.items ?? [];
}

export async function getCompanyPermissions(): Promise<CompanyPermission[]> {
  const response = await api<PermissionsResponse>(
    "/api/v1/company/permissions"
  );

  return response.items ?? [];
}

export async function grantCompanyRolePermission(
  roleId: string,
  permissionId: string
): Promise<void> {
  await api(
    `/api/v1/company/roles/${roleId}/permissions/${permissionId}`,
    {
      method: "POST",
    }
  );
}

export async function revokeCompanyRolePermission(
  roleId: string,
  permissionId: string
): Promise<void> {
  await api(
    `/api/v1/company/roles/${roleId}/permissions/${permissionId}`,
    {
      method: "DELETE",
    }
  );
}
