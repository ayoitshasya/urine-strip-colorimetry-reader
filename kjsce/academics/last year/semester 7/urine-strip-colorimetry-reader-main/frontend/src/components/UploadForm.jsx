import { useState } from 'react'

export default function UploadForm({ onSubmit, loading }) {
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (!selected) return
    setFile(selected)
    setPreview(URL.createObjectURL(selected))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file) onSubmit(file)
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      {preview && <img src={preview} alt="Strip preview" className="preview-img" />}
      <button type="submit" disabled={!file || loading}>
        {loading ? 'Analyzing...' : 'Analyze Strip'}
      </button>
    </form>
  )
}