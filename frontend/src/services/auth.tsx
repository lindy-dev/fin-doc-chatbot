/* eslint-disable react-refresh/only-export-components */
import {
  clearTokens,
  getCurrentUser,
  getStoredToken,
  loginUser,
  storeTokens,
  type UserProfile,
} from './api'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

type AuthContextValue = {
  user: UserProfile | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<UserProfile>
  logout: () => void
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const AuthProviderComponent = ({
  children,
}: {
  children: React.ReactNode
}) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadUser = useCallback(async () => {
    const token = getStoredToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const profile = await getCurrentUser()
      setUser(profile)
    } catch (err) {
      clearTokens()
      setUser(null)
      setError(err instanceof Error ? err.message : 'Failed to load user')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadUser()
  }, [loadUser])

  const login = useCallback(async (email: string, password: string) => {
    setError(null)
    const token = await loginUser({ email, password })
    storeTokens(token)
    const profile = await getCurrentUser()
    setUser(profile)
    return profile
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      error,
      login,
      logout,
      refresh: loadUser,
    }),
    [user, loading, error, login, logout, loadUser]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const AuthProvider = AuthProviderComponent

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
