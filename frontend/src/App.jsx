// -----------------------------------------------------------------------
// App.jsx
//
// What this file does:
//   Defines the app's page layout shell and client-side route map — which
//   page component renders for each URL path.
//
// Where it fits in the project:
//   Rendered by main.jsx inside the routing/auth providers. This is the
//   top of the visible component tree: it always shows the Navbar and
//   footer, and swaps out the middle content based on the current route.
//
// Closely related files:
//   - components/Navbar.jsx: persistent top navigation shown on every page.
//   - components/ProtectedRoute.jsx: gate used below to keep /history
//     login-only.
//   - pages/*.jsx: the individual screens routed to below.
// -----------------------------------------------------------------------

import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Analyze from './pages/Analyze'
import About from './pages/About'
import Contact from './pages/Contact'
import Login from './pages/Login'
import Signup from './pages/Signup'
import History from './pages/History'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/history"
          element={
            // History is only meaningful for a logged-in user (guest scans
            // are never saved server-side), so it's wrapped in
            // ProtectedRoute to redirect anonymous visitors instead of
            // showing an empty/erroring page.
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />
      </Routes>
      <footer className="site-footer">
        StripReader — point-of-care colorimetric analysis, for reference use only.
      </footer>
    </div>
  )
}
