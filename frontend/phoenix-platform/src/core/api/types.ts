export interface ApiResponse<T> {
  data: T
}

export interface LoginRequest {
  username: string
  password: string
}

export type PlatformLevel =
  | 'SYSTEM_ADMIN'
  | 'COMPANY_ADMIN'
  | 'COMPANY_USER'

export interface PlatformUser {
  id: string
  username: string
  display_name: string
  platform_level: PlatformLevel
  [key: string]: unknown
}

export interface PlatformCompany {
  id: string
  code: string
  name: string
  status?: string
  [key: string]: unknown
}

export interface PlatformMembership {
  [key: string]: unknown
}

export interface PlatformModule {
  id: string
  code: string
  name: string
  version?: string
  active?: boolean
  status?: string
  [key: string]: unknown
}

export interface PlatformWorkspace {
  [key: string]: unknown
}

export interface PlatformContext {
  user: PlatformUser
  company?: PlatformCompany | null
  membership?: PlatformMembership | null
  module?: PlatformModule | null
  workspace?: PlatformWorkspace | null
  modules: PlatformModule[]
  permissions?: string[]
  entitlements?: string[]
  [key: string]: unknown
}


