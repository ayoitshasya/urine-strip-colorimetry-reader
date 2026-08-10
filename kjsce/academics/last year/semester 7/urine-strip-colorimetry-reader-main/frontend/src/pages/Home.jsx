import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="page">
      <h1>Urine Test Strip Reader</h1>
      <p>
        A point-of-care colorimetric analysis tool that reads urine test strip
        images and estimates parameters like Glucose, Protein, pH, Ketones,
        and Blood using image-based color matching.
      </p>
      <Link to="/analyze" className="cta-btn">Try it now →</Link>
    </div>
  )
}