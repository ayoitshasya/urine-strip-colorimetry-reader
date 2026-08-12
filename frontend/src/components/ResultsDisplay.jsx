import { exportResultsToPDF } from '../utils/pdfExport'

export default function ResultsDisplay({ results, filename, savedToHistory }) {
  if (!results) return null

  const handleDownload = () => {
    exportResultsToPDF({ filename, results, timestamp: new Date().toISOString() })
  }

  return (
    <div>
      <div className="results-header">
        <h2>Results</h2>
        <button className="btn btn-outline btn-sm" onClick={handleDownload}>
          Download PDF report
        </button>
      </div>

      <div className="results-grid">
        {Object.entries(results).map(([parameter, data]) => {
          const isNegative = String(data.result).toLowerCase() === 'negative'
          return (
            <div key={parameter} className="result-card">
              <h3>{parameter}</h3>
              <div
                className="color-swatch"
                style={{
                  backgroundColor: `rgb(${data.detected_rgb.join(',')})`,
                }}
              />
              <div className={`result-label ${isNegative ? '' : 'flag'}`}>{data.result}</div>
              <p className="muted">RGB {data.detected_rgb.join(', ')}</p>
            </div>
          )
        })}
      </div>

      {savedToHistory && (
        <p className="saved-note">✓ Saved to your scan history</p>
      )}
    </div>
  )
}
