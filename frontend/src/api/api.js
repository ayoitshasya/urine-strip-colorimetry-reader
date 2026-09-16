// -----------------------------------------------------------------------
// api.js
//
// What this file does:
//   Central place for all HTTP calls from the frontend to the FastAPI
//   backend. Wraps a configured axios instance and exposes one small
//   function per backend endpoint.
//
// Where it fits in the project:
//   Every page/component that needs backend data (Analyze, Login, Signup,
//   History, AuthContext) imports functions from here rather than calling
//   axios/fetch directly — keeping the API base URL, auth header, and
//   request shapes defined in exactly one place.
//
// Closely related files:
//   - backend/app/main.py: the server implementing every endpoint called
//     below (paths and payload shapes must stay in sync with that file).
//   - context/AuthContext.jsx: calls setAuthToken()/fetchMe() to restore
//     a session on page load.
// -----------------------------------------------------------------------

import axios from 'axios'

// Falls back to a local dev backend if VITE_API_URL isn't set, so the app
// works out of the box during local development without extra config.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

const client = axios.create({ baseURL: API_BASE_URL })

/**
 * Attach (or remove) the JWT bearer token used to authenticate future
 * requests made through `client`. Called on login/logout and on app
 * startup when restoring a saved session, so every subsequent request
 * automatically carries the current user's credentials.
 *
 * @param {string|null} token - The access token to send as
 *   `Authorization: Bearer <token>`, or a falsy value to clear it (logout).
 */
export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete client.defaults.headers.common['Authorization']
  }
}

// ---- Analyze ----

/**
 * Upload a strip photo to the backend for colorimetric analysis.
 * Works whether or not the caller is logged in — the backend decides
 * whether to save it to history based on the attached auth token (or lack
 * thereof).
 *
 * @param {File} file - The image file selected/captured by the user.
 * @returns {Promise<object>} The parsed AnalysisResponse JSON from the
 *   backend (per-parameter results plus whether it was saved to history).
 */
export async function analyzeStripImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await client.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// ---- Auth ----

/** Register a new local account. Returns the TokenResponse JSON (access token + user info). */
export async function signup(name, email, password) {
  const response = await client.post('/auth/signup', { name, email, password })
  return response.data
}

/** Log in to an existing local account. Returns the TokenResponse JSON (access token + user info). */
export async function login(email, password) {
  const response = await client.post('/auth/login', { email, password })
  return response.data
}

/**
 * Exchange a Google Sign-In ID token for this app's own JWT session.
 * @param {string} idToken - The ID token produced by the Google sign-in widget.
 */
export async function googleAuth(idToken) {
  const response = await client.post('/auth/google', { id_token: idToken })
  return response.data
}

/** Fetch the profile of whichever user the currently attached auth token belongs to. */
export async function fetchMe() {
  const response = await client.get('/auth/me')
  return response.data
}

// ---- History ----

/** Fetch the logged-in user's saved scan history, most recent first. */
export async function fetchHistory() {
  const response = await client.get('/history')
  return response.data
}

/** Delete one saved scan (by id) belonging to the logged-in user. */
export async function deleteHistoryItem(id) {
  const response = await client.delete(`/history/${id}`)
  return response.data
}