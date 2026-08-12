import { useState, useRef } from 'react'

export default function UploadForm({ onSubmit, loading }) {
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const inputRef = useRef(null)

  const handleFile = (selected) => {
    if (!selected) return
    setFile(selected)
    setPreview(URL.createObjectURL(selected))
  }

  const handleFileChange = (e) => handleFile(e.target.files[0])

  const handleDrop = (e) => {
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
