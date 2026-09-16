// -----------------------------------------------------------------------
// eslint.config.js
//
// What this file does:
//   Configures ESLint (the JavaScript/JSX linter) for the frontend using
//   the modern "flat config" format. It defines which rule sets apply to
//   which files and which globals (like `window`, `document`) are
//   available.
//
// Where it fits in the project:
//   Dev-tooling only — not part of the shipped app. Runs via `npm run
//   lint` (see frontend/package.json) to catch common mistakes and
//   enforce React Hooks / Fast Refresh best practices across the React
//   codebase in frontend/src.
// -----------------------------------------------------------------------

import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // Never lint the production build output.
  globalIgnores(['dist']),
  {
    // Apply this configuration to every plain JS and JSX source file.
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,             // baseline recommended JS rules
      reactHooks.configs.flat.recommended, // enforce Rules of Hooks (e.g. no conditional useState)
      reactRefresh.configs.vite,          // ensures components stay compatible with Vite's hot-reload
    ],
    languageOptions: {
      globals: globals.browser,           // recognizes browser globals like `window`/`document` as defined
      parserOptions: { ecmaFeatures: { jsx: true } }, // let the parser understand JSX syntax
    },
  },
])
