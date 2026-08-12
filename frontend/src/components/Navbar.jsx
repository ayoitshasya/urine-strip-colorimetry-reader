import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

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
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Home</NavLink>
        <NavLink to="/analyze" className={({ isActive }) => (isActive ? 'active' : '')}>Analyze</NavLink>
        {user && (
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
