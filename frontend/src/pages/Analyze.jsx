import { useState } from 'react'
import UploadForm from '../components/UploadForm'
import ResultsDisplay from '../components/ResultsDisplay'
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
    </div>
  )
}
