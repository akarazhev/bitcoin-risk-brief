import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const dist = resolve(root, 'dist')

const serverBundle = resolve(root, 'dist-ssr/entry-server.js')
const { renderDocument, siteDocuments } = await import(pathToFileURL(serverBundle).href).catch(() => {
  throw new Error(`missing ${serverBundle}; run the --ssr build before this script`)
})

const template = readFileSync(resolve(dist, 'index.html'), 'utf-8')
const HEAD_START = '<!--per-document-head-->'
const HEAD_END = '<!--/per-document-head-->'

const headStart = template.indexOf(HEAD_START)
const headEnd = template.indexOf(HEAD_END)
if (headStart === -1 || headEnd === -1 || headEnd < headStart) {
  throw new Error('index.html lost its per-document-head markers')
}

for (const document of siteDocuments) {
  const rendered = renderDocument(document.route, document.locale)
  let html = template.slice(0, headStart) + rendered.head + template.slice(headEnd + HEAD_END.length)
  html = html.replace('<html lang="en">', `<html lang="${rendered.lang}" dir="${rendered.dir}">`)
  html = html.replace('<div id="root"></div>', `<div id="root">${rendered.html}</div>`)
  if (html.includes('<div id="root"></div>')) {
    throw new Error(`root placeholder not replaced for ${document.urlPath}`)
  }
  const target = resolve(dist, document.filePath)
  mkdirSync(dirname(target), { recursive: true })
  writeFileSync(target, html, 'utf-8')
  console.log(`prerendered ${document.urlPath} -> dist/${document.filePath}`)
}
