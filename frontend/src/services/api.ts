const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type UserRole = 'admin' | 'user'

export type UserProfile = {
  id: string
  email: string
  name: string
  role: UserRole
  is_approved: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export type PendingUser = {
  id: string
  email: string
  name: string
  created_at: string
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

const ACCESS_TOKEN_KEY = 'fin_doc_access_token'
const REFRESH_TOKEN_KEY = 'fin_doc_refresh_token'
const TOKEN_TYPE_KEY = 'fin_doc_token_type'

export const getStoredToken = () => localStorage.getItem(ACCESS_TOKEN_KEY)

export const storeTokens = (token: TokenResponse) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, token.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, token.refresh_token)
  localStorage.setItem(TOKEN_TYPE_KEY, token.token_type)
}

export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(TOKEN_TYPE_KEY)
}

const buildHeaders = (auth = false) => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  if (auth) {
    const token = getStoredToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }
  return headers
}

const request = async <T>(
  path: string,
  options: RequestInit = {},
  auth = false
): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...buildHeaders(auth),
      ...(options.headers ?? {}),
    },
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const registerUser = (payload: {
  name: string
  email: string
  password: string
}) => request<UserProfile>('/auth/register', {
  method: 'POST',
  body: JSON.stringify(payload),
})

export const loginUser = (payload: { email: string; password: string }) =>
  request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const getCurrentUser = () => request<UserProfile>('/auth/me', {}, true)

export const getPendingUsers = () =>
  request<PendingUser[]>('/auth/admin/pending', {}, true)

export const approveUser = (userId: string, payload: {
  is_approved: boolean
  is_active?: boolean
}) =>
  request<UserProfile>(`/auth/admin/users/${userId}/approval`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }, true)
