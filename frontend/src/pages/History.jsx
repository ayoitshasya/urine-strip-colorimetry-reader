import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchHistory, deleteHistoryItem } from '../api/api'
import { exportResultsToPDF } from '../utils/pdfExport'

export default function History() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    setError(null)
    try {
      const data = await fetchHistory()
      setItems(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load history')
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteHistoryItem(id)
      setItems((prev) => prev.filter((i) => i.id !== id))
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not delete entry')
    }
  }

  const handleDownload = (item) => {
    exportResultsToPDF({
      filename: item.filename,
      results: item.results,
      timestamp: item.created_at,
    })
  }

  return (
    <div className="page">
      <h1>Scan history</h1>
      <p className="page-subtitle">Every strip you've analyzed while signed in, saved automatically.</p>

      {error && <p className="error">{error}</p>}

      {items === null && !error && (
        <div className="strip-motif animated" style={{ maxWidth: 160 }}>
          <span></span><span></span><span></span><span></span><span></span>
        </div>
      )}

      {items && items.length === 0 && (
        <div className="empty-state">
          <div className="strip-motif"><span></span><span></span><span></span><span></span><span></span></div>
          <p style={{ marginBottom: '1rem' }}>No scans yet. Analyze a strip to start building your history.</p>
          <Link to="/analyze" className="cta-btn">Analyze a strip →</Link>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="history-list">
          {items.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-item-top">
                <div>
                  <div className="history-filename">{item.filename}</div>
                  <div className="history-date">{new Date(item.created_at).toLocaleString()}</div>
                </div>
                <div className="history-actions">
                  <button className="btn btn-outline btn-sm" onClick={() => handleDownload(item)}>
                    Download PDF
                  </button>
                  <button className="btn btn-danger-ghost btn-sm" onClick={() => handleDelete(item.id)}>
                    Delete
                  </button>
                </div>
              </div>
              <div className="history-pads">
                {Object.entries(item.results).map(([parameter, data]) => (
                  <div key={parameter} className="history-pad">
                    <span
                      className="dot"
                      style={{ background: `rgb(${data.detected_rgb.join(',')})` }}
                    />
                    {parameter}: <strong>{data.result}</strong>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
