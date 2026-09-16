// -----------------------------------------------------------------------
// Signup.jsx
//
// What this file does:
//   The account-creation page: name/email/password form plus a "Sign up
//   with Google" button, either of which creates an account and logs the
//   user in.
//
// Where it fits in the project:
//   Routed at /signup in App.jsx.
//
// Closely related files:
//   - api/api.js: signup()/googleAuth() perform the backend calls.
//   - context/AuthContext.jsx: login() here stores the resulting session.
// -----------------------------------------------------------------------

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { signup as signupRequest, googleAuth } from '../api/api'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Mirrors the backend's implicit minimum (bcrypt hashing has no
    // strength requirement itself, but this keeps accounts from being
    // created with trivially weak passwords) — checked client-side first
    // to give instant feedback before making a network request.
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)
    try {
      const data = await signupRequest(name, email, password)
      login(data.access_token, data.user)
      navigate('/analyze')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create account')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null)
    try {
      // Google sign-in doubles as signup here: the backend creates an
      // account automatically the first time a given Google email is seen
      // (see backend/app/main.py's /auth/google route).
      const data = await googleAuth(credentialResponse.credential)
      login(data.access_token, data.user)
      navigate('/analyze')
    } catch (err) {
      setError(err.response?.data?.detail || 'Google sign-in failed')
    }
  }

  return (
    <div className="page page-narrow">
      <h1>Create your account</h1>
      <p className="page-subtitle">Save every scan and export clean PDF reports.</p>

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
            <label htmlFor="name">Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
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
              minLength={8}
            />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
