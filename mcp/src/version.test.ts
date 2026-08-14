import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { SERVER_NAME, SERVER_VERSION } from './version.js'

describe('package identity', () => {
  it('matches package.json so the server never reports a version it is not', () => {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, '../package.json'), 'utf-8'))
    expect(SERVER_VERSION).toBe(pkg.version)
    expect(SERVER_NAME).toBe('bitcoin-risk-brief')
  })
})
