// -----------------------------------------------------------------------
// UploadForm.jsx
//
// What this file does:
//   A reusable form for picking (or drag-and-dropping) a strip photo,
//   previewing it, and submitting it for analysis.
//
// Where it fits in the project:
//   Used by pages/Analyze.jsx, which supplies `onSubmit` (calls the
//   backend via api/api.js's analyzeStripImage) and `loading` (whether an
//   analysis request is currently in flight).
// -----------------------------------------------------------------------

import { useState, useRef } from 'react'

export default function UploadForm({ onSubmit, loading }) {
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const inputRef = useRef(null)

  const handleFile = (selected) => {
    if (!selected) return
    setFile(selected)
    // Creates a temporary local URL pointing directly at the file's bytes
    // in memory, so the chosen image can be previewed instantly without
    // uploading it anywhere first.
    setPreview(URL.createObjectURL(selected))
  }

  const handleFileChange = (e) => handleFile(e.target.files[0])

  const handleDrop = (e) => {
    // Without this, the browser's default behavior is to navigate to /
    // open the dropped file directly, replacing the page.
    e.preventDefault()
    handleFile(e.dataTransfer.files[0])
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file) onSubmit(file)
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label
        className="file-drop"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input type="file" accept="image/*" onChange={handleFileChange} ref={inputRef} />
        {file ? `Selected: ${file.name}` : 'Click to choose a strip photo, or drag one here'}
      </label>
      {preview && <img src={preview} alt="Strip preview" className="preview-img" />}
      <button type="submit" className="btn btn-primary" disabled={!file || loading}>
        {loading ? 'Analyzing...' : 'Analyze strip'}
      </button>
    </form>
  )
}
