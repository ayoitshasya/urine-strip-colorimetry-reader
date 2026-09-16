// -----------------------------------------------------------------------
// Login.jsx
//
// What this file does:
//   The sign-in page: email/password form plus a "Sign in with Google"
//   button, either of which logs the user in and redirects them onward.
//
// Where it fits in the project:
//   Routed at /login in App.jsx. ProtectedRoute redirects unauthenticated
//   visitors here (attaching where they came from via router state), so
//   this page sends them back to that original destination after success.
//
// Closely related files:
//   - api/api.js: login()/googleAuth() perform the backend auth calls.
//   - context/AuthContext.jsx: login() here stores the resulting session.
// -----------------------------------------------------------------------

import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { login as loginRequest, googleAuth } from '../api/api'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // If ProtectedRoute redirected here, `location.state.from` holds the
  // page the user was originally trying to reach; otherwise default to
  // the main Analyze page as the most useful post-login destination.
  const redirectTo = location.state?.from || '/analyze'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await loginRequest(email, password)
      login(data.access_token, data.user)
      navigate(redirectTo)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not sign in')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null)
    try {
      // `credentialResponse.credential` is the Google-issued ID token;
      // the backend verifies it server-side before trusting it.
      const data = await googleAuth(credentialResponse.credential)
      login(data.access_token, data.user)
      navigate(redirectTo)
    } catch (err) {
      setError(err.response?.data?.detail || 'Google sign-in failed')
    }
  }

  return (
    <div className="page page-narrow">
      <h1>Welcome back</h1>
      <p className="page-subtitle">Sign in to save and export your strip readings.</p>

      <div className="auth-card">
        <div className="google-btn-wrap">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError('Google sign-in failed')}
          />
        </div>

        <div className="auth-divider">or continue with email</div>

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account? <Link to="/signup">Create one</Link>
        </p>
      </div>
    </div>
  )
}
