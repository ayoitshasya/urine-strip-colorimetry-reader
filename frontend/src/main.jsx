// -----------------------------------------------------------------------
// main.jsx
//
// What this file does:
//   The frontend's entry point. Mounts the React app into the page's
//   #root element and wraps it with the global providers every screen
//   needs: routing, Google OAuth, and the app's own auth context.
//
// Where it fits in the project:
//   This is the first app code that runs in the browser (loaded by
//   index.html via `<script type="module" src="/src/main.jsx">`). It sets
//   up the provider tree that App.jsx and every page/component renders
//   inside of.
//
// Closely related files:
//   - App.jsx: the actual route/page tree rendered inside these providers.
//   - context/AuthContext.jsx: supplies logged-in user state app-wide.
//   - api/api.js: source of GOOGLE_CLIENT_ID used below.
// -----------------------------------------------------------------------

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { GOOGLE_CLIENT_ID } from './api/api.js'
import './index.css'

// Provider order matters here: GoogleOAuthProvider must wrap BrowserRouter
// (Google sign-in buttons can appear on any routed page), and AuthProvider
// must be inside BrowserRouter/outside App so App and all pages can read
// the logged-in user via the useAuth() hook.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </GoogleOAuthProvider>
  </StrictMode>,
)
