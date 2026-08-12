import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { user } = useAuth()

  return (
    <div className="hero">
      <span className="hero-eyebrow">Point-of-care colorimetry</span>
      <h1>Read a urine test strip like a lab does — from a photo.</h1>
      <p>
        Upload a photo of a reacted test strip and get Glucose, Protein, pH,
        Ketones, and Blood readings instantly, matched against a standard
        reference chart using image-based color analysis.
      </p>
      <Link to="/analyze" className="cta-btn">
        {user ? 'Analyze a strip →' : 'Try it now →'}
      </Link>

      <div className="hero-strip-panel">
        <div className="strip-motif animated">
          <span></span><span></span><span></span><span></span><span></span>
        </div>
        <div className="hero-strip-labels">
          <span>Glucose</span>
          <span>Protein</span>
          <span>pH</span>
          <span>Ketones</span>
          <span>Blood</span>
        </div>
      </div>

      <div className="feature-row">
        <div className="feature-card">
          <h4>Instant matching</h4>
          <p>Nearest-color matching against a reference chart for all 5 pads at once.</p>
        </div>
        <div className="feature-card">
          <h4>Saved history</h4>
          <p>Sign in to keep every scan and revisit results whenever you need them.</p>
        </div>
        <div className="feature-card">
          <h4>PDF reports</h4>
          <p>Export a clean, shareable report of any result in a single click.</p>
        </div>
      </div>
    </div>
  )
}
