import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface AuthContext {
  key: string | null
  role: string | null
  login: (key: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContext | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Store API key in memory — session-only, cleared on tab close
  const [key, setKey] = useState<string | null>(null)
  const [role, setRole] = useState<string | null>(null)

  const login = (apiKey: string) => {
    setKey(apiKey)
  }

  const logout = () => {
    setKey(null)
    setRole(null)
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
