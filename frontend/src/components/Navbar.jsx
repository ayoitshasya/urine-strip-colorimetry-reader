// -----------------------------------------------------------------------
// Navbar.jsx
//
// What this file does:
//   Renders the site-wide top navigation bar: brand/logo link, page
//   links, and a sign-in button or logged-in user menu depending on
//   auth state.
//
// Where it fits in the project:
//   Rendered once at the top of App.jsx, above the routed page content,
//   so it appears identically on every page.
//
// Closely related files:
//   - context/AuthContext.jsx: supplies `user` and `logout()` used below.
// -----------------------------------------------------------------------

import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    // Send the user back to the home page after logging out, rather than
    // leaving them on a page that might assume they're still logged in.
    navigate('/')
  }

  // Single-letter avatar fallback (e.g. "J" for "Jane") when there's no
  // profile picture to show; falls back to "?" if the name is somehow empty.
  const initial = user?.name ? user.name.trim().charAt(0).toUpperCase() : '?'

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">
        <div className="strip-motif">
          <span></span><span></span><span></span><span></span><span></span>
        </div>
        StripReader
      </Link>
      <div className="nav-links">
        {/* `end` on the Home link prevents it from matching every route
            (NavLink matching is prefix-based by default, and "/" is a
            prefix of every path), so it's only "active" on the exact home page. */}
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Home</NavLink>
        <NavLink to="/analyze" className={({ isActive }) => (isActive ? 'active' : '')}>Analyze</NavLink>
        {user && (
          // History only makes sense (and only has any data) for logged-in
          // users, so the link itself is hidden for guests rather than
          // shown and immediately redirecting.
          <NavLink to="/history" className={({ isActive }) => (isActive ? 'active' : '')}>History</NavLink>
        )}
        <NavLink to="/about" className={({ isActive }) => (isActive ? 'active' : '')}>About</NavLink>
        <NavLink to="/contact" className={({ isActive }) => (isActive ? 'active' : '')}>Contact</NavLink>

        {user ? (
          <div className="nav-user">
            <div className="nav-avatar">{initial}</div>
            <span className="nav-username">{user.name}</span>
            <button className="link-btn" onClick={handleLogout}>Log out</button>
          </div>
        ) : (
          <Link to="/login" className="nav-cta">Sign in</Link>
        )}
      </div>
    </nav>
  )
}
