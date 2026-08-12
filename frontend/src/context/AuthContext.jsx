import { createContext, useContext, useState, useEffect } from 'react'
import { setAuthToken, fetchMe } from '../api/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('stripreader_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const init = async () => {
      const saved = localStorage.getItem('stripreader_token')
      if (saved) {
        setAuthToken(saved)
        try {
          const me = await fetchMe()
          setUser(me)
          setToken(saved)
        } catch {
          localStorage.removeItem('stripreader_token')
          setAuthToken(null)
          setToken(null)
        }
      }
      setLoading(false)
    }
    init()
  }, [])

  const login = (accessToken, userData) => {
    localStorage.setItem('stripreader_token', accessToken)
    setAuthToken(accessToken)
    setToken(accessToken)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('stripreader_token')
    setAuthToken(null)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
