import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

const client = axios.create({ baseURL: API_BASE_URL })

export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete client.defaults.headers.common['Authorization']
  }
}

// ---- Analyze ----

export async function analyzeStripImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await client.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// ---- Auth ----

export async function signup(name, email, password) {
  const response = await client.post('/auth/signup', { name, email, password })
  return response.data
}

export async function login(email, password) {
  const response = await client.post('/auth/login', { email, password })
  return response.data
}

export async function googleAuth(idToken) {
  const response = await client.post('/auth/google', { id_token: idToken })
  return response.data
}

export async function fetchMe() {
  const response = await client.get('/auth/me')
  return response.data
}

// ---- History ----

export async function fetchHistory() {
  const response = await client.get('/history')
  return response.data
}

export async function deleteHistoryItem(id) {
  const response = await client.delete(`/history/${id}`)
  return response.data
}