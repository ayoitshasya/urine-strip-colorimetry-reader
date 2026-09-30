// -----------------------------------------------------------------------
// ReportPanel.jsx
//
// What this file does:
//   Shows the plain-language report for a strip analysis, with an
//   English / हिन्दी toggle. Fetches the report from the backend's
//   /report endpoint (NLP layer: report generator + English->Hindi
//   seq2seq translator + consistency check) whenever new results arrive.
//
// Where it fits in the project:
//   Rendered by pages/Analyze.jsx under ResultsDisplay.
//
// Closely related files:
//   - api/api.js: fetchReport() makes the HTTP call.
//   - backend/app/nlp/service.py: builds the report on the server.
// -----------------------------------------------------------------------

import { useEffect, useState } from 'react'
import { fetchReport } from '../api/api'

const LABEL_NAMES = { ANALYTE: 'Test', LEVEL: 'Result', CONDITION: 'Condition' }

function HighlightedLine({ segments }) {
  return segments.map((seg, i) =>
    seg.label ? (
      <mark key={i} className={`ner ner-${seg.label.toLowerCase()}`} title={LABEL_NAMES[seg.label]}>
        {seg.text}
      </mark>
    ) : (
      <span key={i}>{seg.text}</span>
    )
  )
}

export default function ReportPanel({ results }) {
  const [report, setReport] = useState(null)
  const [lang, setLang] = useState('english')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!results) {
      setReport(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchReport(results)
      .then((data) => { if (!cancelled) setReport(data) })
      .catch(() => { if (!cancelled) setError('Could not generate the written report.') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [results])

  if (!results) return null

  return (
    <div className="report-panel">
      <div className="results-header">
        <h2>Written report</h2>
        <div className="report-toggle">
          <button
            className={`btn btn-sm ${lang === 'english' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setLang('english')}
          >
            English
          </button>
          <button
            className={`btn btn-sm ${lang === 'hindi' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setLang('hindi')}
          >
            हिन्दी
          </button>
        </div>
      </div>

      {loading && <p className="muted">Generating report…</p>}
      {error && <p className="error">{error}</p>}

      {report && (
        <>
          <div className="report-text" lang={lang === 'hindi' ? 'hi' : 'en'}>
            {(lang === 'hindi' ? report.hindi_segments : report.english_segments).map((segs, i) => (
              <div key={i} className="report-line">
                <HighlightedLine segments={segs} />
              </div>
            ))}
          </div>

          <p className="ner-legend">
            <mark className="ner ner-analyte">Test</mark>
            <mark className="ner ner-level">Result</mark>
            <mark className="ner ner-condition">Condition</mark>
            <span className="muted">
              {lang === 'hindi'
                ? 'highlighted from a Hindi term list'
                : 'highlighted automatically by an NER model'}
            </span>
          </p>

          {lang === 'hindi' && !report.all_consistent && (
            <p className="muted">
              Some sentences are shown in English because the automatic translation
              could not be verified.
            </p>
          )}
          {lang === 'hindi' && (
            <p className="muted">
              Hindi is machine translated by a small model trained on templated
              sentences. Not a clinical document.
            </p>
          )}
        </>
      )}
    </div>
  )
}