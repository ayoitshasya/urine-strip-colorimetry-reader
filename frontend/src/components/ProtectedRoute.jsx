// -----------------------------------------------------------------------
// ProtectedRoute.jsx
//
// What this file does:
//   A route guard component: renders its children only if a user is
//   logged in, otherwise redirects to /login. Shows a small loading
//   placeholder while the auth session is still being restored.
//
// Where it fits in the project:
//   Used by App.jsx to wrap the /history route (the only route that
//   requires authentication in this app).
//
// Closely related files:
//   - context/AuthContext.jsx: supplies `user` and `loading` used below.
// -----------------------------------------------------------------------

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    // AuthContext is still checking localStorage/validating a saved token
    // on startup — show a lightweight placeholder instead of the
    // "children" (which would flash briefly) or a redirect (which would
    // be wrong if the saved session turns out to be valid).
    return (
      <div className="page">
        <div className="strip-motif animated" style={{ maxWidth: 160 }}>
          <span></span><span></span><span></span><span></span><span></span>
        </div>
      </div>
    )
  }

  if (!user) {
    // Remember where the user was trying to go (`state={{ from: ... }}`)
    // so the login page could send them back there after signing in.
    // `replace` avoids leaving the protected route in browser history,
    // so the back button doesn't bounce the user right back to it.
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return children
}
