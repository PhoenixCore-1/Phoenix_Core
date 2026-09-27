import { ApiError } from './errors'
import type { ApiResponse } from './types'

export interface ApiOptions extends RequestInit {
  headers?: Record<string, string>
}

let currentOrganisationId: string | null = null

export function setApiOrganisationId(organisationId: string | null) {
  currentOrganisationId = organisationId
}

export async function api<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(currentOrganisationId
        ? { 'X-Phoenix-Organisation': currentOrganisationId }
        : {}),
      ...(options.headers || {}),
    },
  })

  let body: ApiResponse<T> | null = null

  try {
    body = (await response.json()) as ApiResponse<T>
  } catch {
    body = null
  }

  if (!response.ok) {
    const errorBody = body as
      | (ApiResponse<{
          code?: string
          message?: string
          details?: unknown
        }> & {
          code?: string
          message?: string
          details?: unknown
        })
      | null

    throw new ApiError(
      response.status,
      errorBody?.message ||
        errorBody?.data?.message ||
        response.statusText ||
        'API request failed.',
      errorBody?.code || errorBody?.data?.code,
      errorBody?.details || errorBody?.data?.details,
    )
  }

  return body?.data as T
}
