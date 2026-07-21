import { useState } from 'react'
import UploadForm from '../components/UploadForm'
import ResultsDisplay from '../components/ResultsDisplay'
import { analyzeStripImage } from '../api/api'

export default function Analyze() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async (file) => {
    setLoading(true)
    setError(null)
    try {
      const data = await analyzeStripImage(file)
      setResults(data.results)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h1>Analyze Strip</h1>
      <UploadForm onSubmit={handleAnalyze} loading={loading} />
      {error && <p className="error">{error}</p>}
      <ResultsDisplay results={results} />
    </div>
  )
}