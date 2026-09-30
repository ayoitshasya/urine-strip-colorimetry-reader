// -----------------------------------------------------------------------
// Analyze.jsx
//
// What this file does:
//   The main "read a strip" page: hosts the upload form, triggers the
//   backend analysis call, and shows the resulting readings (or an error).
//
// Where it fits in the project:
//   Routed at /analyze in App.jsx. Works for both guests and logged-in
//   users — the backend itself decides whether to persist the scan to
//   history based on whether the request carried a valid auth token.
//
// Closely related files:
//   - components/UploadForm.jsx: file picker/drop UI, calls back into
//     handleAnalyze below.
//   - components/ResultsDisplay.jsx: renders the results returned here.
//   - api/api.js: analyzeStripImage() performs the actual HTTP request.
// -----------------------------------------------------------------------

import { useState } from 'react'
import UploadForm from '../components/UploadForm'
import ResultsDisplay from '../components/ResultsDisplay'
import ReportPanel from '../components/ReportPanel'
import { analyzeStripImage } from '../api/api'
import { useAuth } from '../context/AuthContext'

export default function Analyze() {
  const [results, setResults] = useState(null)
  const [filename, setFilename] = useState(null)
  const [savedToHistory, setSavedToHistory] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { user } = useAuth()

  const handleAnalyze = async (file) => {
    setLoading(true)
    setError(null)
    try {
      const data = await analyzeStripImage(file)
      setResults(data.results)
      setFilename(data.filename)
      setSavedToHistory(data.saved_to_history)
    } catch (err) {
      // Prefer the backend's specific error message (FastAPI's
      // HTTPException `detail`) when available, falling back to a generic
      // message for network errors or unexpected failures.
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h1>Analyze strip</h1>
      <p className="page-subtitle">
        {user
          ? 'Upload a photo of the reacted strip. Results are matched against the reference chart and saved to your history.'
          : 'Upload a photo of the reacted strip to get an instant reading. Sign in to save results and download PDF reports later.'}
      </p>

      <UploadForm onSubmit={handleAnalyze} loading={loading} />

      {loading && (
        <div className="strip-motif animated" style={{ maxWidth: 200, marginTop: '1.5rem' }}>
          <span></span><span></span><span></span><span></span><span></span>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <ResultsDisplay results={results} filename={filename} savedToHistory={savedToHistory} />

      <ReportPanel results={results} />
    </div>
  )
}
