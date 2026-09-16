// -----------------------------------------------------------------------
// AuthContext.jsx
//
// What this file does:
//   Provides app-wide authentication state via React Context: who (if
//   anyone) is logged in, the current JWT, and login()/logout() actions.
//   Also restores a saved session from localStorage on first load.
//
// Where it fits in the project:
//   Wrapped around the whole app in main.jsx. Any component can call
//   `useAuth()` to read the current user or trigger login/logout, instead
//   of prop-drilling auth state through every page.
//
// Closely related files:
//   - api/api.js: setAuthToken()/fetchMe() used to validate and attach
//     the saved token.
//   - components/ProtectedRoute.jsx: reads this context to gate routes.
//   - pages/Login.jsx, Signup.jsx: call login() from this context after a
//     successful backend auth call.
// -----------------------------------------------------------------------

import { createContext, useContext, useState, useEffect } from 'react'
import { setAuthToken, fetchMe } from '../api/api'

const AuthContext = createContext(null)

/**
 * Wraps the app and supplies auth state/actions to every descendant via
 * `useAuth()`. On mount, attempts to restore a previously saved session
 * from localStorage so refreshing the page doesn't log the user out.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Lazy initializer so the token is read from localStorage exactly once,
  // synchronously, on the very first render (avoids a flash where the
  // token briefly appears absent).
  const [token, setToken] = useState(() => localStorage.getItem('stripreader_token'))
  // Starts true so consumers (e.g. ProtectedRoute) can wait for the saved
  // session to finish being validated before deciding to redirect.
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const init = async () => {
      const saved = localStorage.getItem('stripreader_token')
      if (saved) {
        setAuthToken(saved)
        try {
          // A saved token could be expired or otherwise invalid (e.g. the
          // backend's secret changed) — confirm it still works by fetching
          // the profile it claims to belong to, rather than trusting it blindly.
          const me = await fetchMe()
          setUser(me)
          setToken(saved)
        } catch {
          // Any failure here means the token is no longer usable, so
          // clear it out entirely rather than leaving stale auth state.
          localStorage.removeItem('stripreader_token')
          setAuthToken(null)
          setToken(null)
        }
      }
      setLoading(false)
    }
    init()
  }, [])

  /** Store a freshly issued token/user (after signup, login, or Google auth) and mark the session as active. */
  const login = (accessToken, userData) => {
    localStorage.setItem('stripreader_token', accessToken)
    setAuthToken(accessToken)
    setToken(accessToken)
    setUser(userData)
  }

  /** Clear the session everywhere: localStorage, the axios client's auth header, and local state. */
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

/**
 * Hook for consuming auth state/actions from any component.
 * @throws {Error} If called outside of an AuthProvider — this guards
 *   against silently getting a null context and crashing later with a
 *   confusing error somewhere else.
 */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
