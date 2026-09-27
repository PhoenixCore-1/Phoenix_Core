import { api } from './client'
import type {
  LoginRequest,
  PlatformContext,
} from './types'

export function login(input: LoginRequest): Promise<unknown> {
  return api<unknown>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<unknown> {
  return api<unknown>('/api/v1/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
}
export function logout(): Promise<unknown> {
  return api<unknown>('/api/v1/auth/logout', {
    method: 'POST',
  })
}

export function getContext(): Promise<PlatformContext> {
  return api<PlatformContext>('/api/v1/baseline/context')
}

