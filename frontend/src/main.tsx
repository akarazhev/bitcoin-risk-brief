import React from 'react'
import ReactDOM from 'react-dom/client'
import Root from './Root'
import { documentForPath } from './routes'
import './App.css'

const current = documentForPath(location.pathname)
const route = current?.route ?? 'home'
const locale = current?.locale ?? 'en'

const container = document.getElementById('root')!
const tree = (
  <React.StrictMode>
    <Root route={route} locale={locale} />
  </React.StrictMode>
)

// Production always serves a prerendered document, so the container has children and we hydrate.
// vite dev serves index.html with an empty #root for any path; hydrating that logs a misleading
// mismatch before React recovers, so mount there instead.
if (container.firstChild) {
  ReactDOM.hydrateRoot(container, tree)
} else {
  ReactDOM.createRoot(container).render(tree)
}
