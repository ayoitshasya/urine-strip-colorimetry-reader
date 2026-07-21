import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function analyzeStripImage(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data
}