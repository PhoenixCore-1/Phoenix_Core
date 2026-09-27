export type PlatformLevel =
  | 'SYSTEM_ADMIN'
  | 'COMPANY_ADMIN'
  | 'COMPANY_USER'

export type Module = {
  id: string
  code: string
  name: string
  version: string
  active: boolean
}

export type Company = {
  id: string
  code: string
  name: string
  status: string
}

export type Context = {
  user: {
    id: string
    username: string
    display_name: string
    platform_level: PlatformLevel
  }
  company: Company | null
  modules: Module[]
}
