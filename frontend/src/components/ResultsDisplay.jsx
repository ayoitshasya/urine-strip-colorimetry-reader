// -----------------------------------------------------------------------
// ResultsDisplay.jsx
//
// What this file does:
//   Renders the outcome of a strip analysis as a grid of per-parameter
//   result cards (detected color swatch, RGB values, matched result
//   label), plus a button to download the results as a PDF report.
//
// Where it fits in the project:
//   Used by pages/Analyze.jsx (and similar) to show the results returned
//   by the backend's /analyze endpoint (via api/api.js's
//   analyzeStripImage).
//
// Closely related files:
//   - utils/pdfExport.js: builds the actual PDF triggered by the
//     "Download PDF report" button.
// -----------------------------------------------------------------------

import { exportResultsToPDF } from '../utils/pdfExport'

export default function ResultsDisplay({ results, filename, savedToHistory }) {
  // No results yet (e.g. before the first analysis completes) — render
  // nothing rather than an empty/broken grid.
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
          // "Negative" results are the normal/healthy case, so they're
          // styled plainly while any other result gets a "flag" style to
          // visually draw attention to it.
          const isNegative = String(data.result).toLowerCase() === 'negative'
          return (
            <div key={parameter} className="result-card">
              <h3>{parameter}</h3>
              <div
                className="color-swatch"
                style={{
                  // Renders the exact color sampled from the strip photo,
                  // so the user can visually sanity-check the detected
                  // color against their own strip.
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
        // Only shown when the backend actually persisted this scan (i.e.
        // the user was logged in at analysis time) — see main.py's
        // /analyze route.
        <p className="saved-note">✓ Saved to your scan history</p>
      )}
    </div>
  )
}
