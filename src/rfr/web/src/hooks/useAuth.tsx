import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface AuthContext {
  key: string | null
  role: string | null
  login: (key: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContext | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [key, setKey] = useState<string | null>(() => localStorage.getItem('rfr_api_key'))
  const [role, setRole] = useState<string | null>(null)

  useEffect(() => {
    if (key) {
      localStorage.setItem('rfr_api_key', key)
    } else {
      localStorage.removeItem('rfr_api_key')
    }
  }, [key])

  const login = (apiKey: string) => {
    setKey(apiKey)
    // Role will be set after the first API call
  }

  const logout = () => {
    setKey(null)
    setRole(null)
    localStorage.removeItem('rfr_api_key')
  }

  return (
    <AuthContext.Provider value={{ key, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContext {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
