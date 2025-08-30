import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  login: string
  name?: string
  avatar_url: string
}

interface AuthContextType {
  user: User | null
  accessToken: string | null
  login: () => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)

  useEffect(() => {
    const storedToken = localStorage.getItem('github_access_token')
    const storedUser = localStorage.getItem('github_user')
    
    if (storedToken && storedUser) {
      setAccessToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
  }, [])

  const login = async () => {
    try {
      const response = await fetch(`${(import.meta as any).env.VITE_API_URL}/api/auth/github`)
      const data = await response.json()
      window.location.href = data.auth_url
    } catch (error) {
      console.error('Login failed:', error)
    }
  }

  const logout = () => {
    setUser(null)
    setAccessToken(null)
    localStorage.removeItem('github_access_token')
    localStorage.removeItem('github_user')
  }

  const value = {
    user,
    accessToken,
    login,
    logout,
    isAuthenticated: !!user && !!accessToken
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
