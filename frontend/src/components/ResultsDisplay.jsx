export default function ResultsDisplay({ results }) {
  if (!results) return null

  return (
    <div className="results-grid">
      {Object.entries(results).map(([parameter, data]) => (
        <div key={parameter} className="result-card">
          <h3>{parameter}</h3>
          <div
            className="color-swatch"
            style={{
              backgroundColor: `rgb(${data.detected_rgb.join(',')})`,
            }}
          />
          <p><strong>Result:</strong> {data.result}</p>
          <p className="muted">Detected RGB: {data.detected_rgb.join(', ')}</p>
        </div>
      ))}
    </div>
  )
}