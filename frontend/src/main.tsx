import React from 'react'
import ReactDOM from 'react-dom/client'
import Root from './Root'
import { documentForPath } from './routes'
import './App.css'

const current = documentForPath(location.pathname)
const route = current?.route ?? 'home'
const locale = current?.locale ?? 'en'

ReactDOM.hydrateRoot(
  document.getElementById('root')!,
  <React.StrictMode>
    <Root route={route} locale={locale} />
  </React.StrictMode>,
)
