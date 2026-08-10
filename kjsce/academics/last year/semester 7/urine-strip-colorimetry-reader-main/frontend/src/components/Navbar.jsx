import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-brand">🧪 StripReader</div>
      <div className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/analyze">Analyze</Link>
        <Link to="/about">About</Link>
        <Link to="/contact">Contact</Link>
      </div>
    </nav>
  )
}