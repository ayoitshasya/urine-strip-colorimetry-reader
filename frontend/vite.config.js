// -----------------------------------------------------------------------
// vite.config.js
//
// What this file does:
//   Configuration for Vite, the build tool/dev server that compiles and
//   serves the React frontend.
//
// Where it fits in the project:
//   Read by every `vite`/`vite build`/`vite preview` command (see the
//   scripts in frontend/package.json). Registers the official React
//   plugin so JSX files compile and Fast Refresh (instant hot-reload of
//   component edits) works during development.
// -----------------------------------------------------------------------

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
