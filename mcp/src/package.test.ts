import { execFileSync, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it } from 'vitest'

const packageDir = resolve(fileURLToPath(new URL('../', import.meta.url)))
const distDir = join(packageDir, 'dist')
const backupDistDir = join(packageDir, 'dist.package-test-backup')
const tempDirs: string[] = []

afterEach(() => {
  for (const directory of tempDirs.splice(0)) rmSync(directory, { recursive: true, force: true })
  if (existsSync(backupDistDir)) {
    rmSync(distDir, { recursive: true, force: true })
    renameSync(backupDistDir, distDir)
  }
})

describe('published package', () => {
  it('removes stale test artifacts before a production build', () => {
    mkdirSync(distDir, { recursive: true })
    const staleTestPath = join(distDir, 'stale.test.js')
    const staleBuildInfoPath = join(distDir, 'tsconfig.tsbuildinfo')
    writeFileSync(staleTestPath, 'stale test output')
    writeFileSync(staleBuildInfoPath, 'stale build info')

    execFileSync('npm', ['run', 'build'], { cwd: packageDir, encoding: 'utf-8' })

    expect(existsSync(staleTestPath)).toBe(false)
    expect(existsSync(staleBuildInfoPath)).toBe(false)
  })

  it('builds a clean package with an executable production-only bin', () => {
    const packDir = mkdtempSync(join(tmpdir(), 'bitcoin-risk-brief-mcp-pack-'))
    const unpackDir = mkdtempSync(join(tmpdir(), 'bitcoin-risk-brief-mcp-unpack-'))
    const npmCacheDir = mkdtempSync(join(tmpdir(), 'bitcoin-risk-brief-mcp-npm-cache-'))
    tempDirs.push(packDir, unpackDir, npmCacheDir)

    if (existsSync(distDir)) renameSync(distDir, backupDistDir)
    const packed = JSON.parse(execFileSync('npm', ['pack', '--json', '--pack-destination', packDir], {
      cwd: packageDir,
      encoding: 'utf-8',
      env: { ...process.env, npm_config_cache: npmCacheDir },
    })) as Array<{ filename: string; files: Array<{ path: string }> }>
    const manifest = packed[0]
    const packedPaths = manifest.files.map((file) => file.path)

    expect(packedPaths).toContain('dist/index.js')
    expect(packedPaths).toContain('LICENSE')
    expect(packedPaths).not.toContain('dist/index.test.js')
    expect(packedPaths.some((path) => path.endsWith('.tsbuildinfo'))).toBe(false)

    const tarball = join(packDir, manifest.filename)
    execFileSync('tar', ['-xzf', tarball, '-C', unpackDir])
    const unpackedPackage = join(unpackDir, 'package')
    const binPath = join(unpackedPackage, 'dist', 'index.js')
    const socketGuardPath = join(unpackDir, 'socket-guard.cjs')
    symlinkSync(join(packageDir, 'node_modules'), join(unpackedPackage, 'node_modules'), 'dir')
    writeFileSync(socketGuardPath, [
      "const net = require('node:net')",
      "net.Socket.prototype.connect = function () { throw new Error('OUTBOUND NETWORK ATTEMPTED') }",
    ].join('\n'))

    expect(readFileSync(binPath, 'utf-8').startsWith('#!/usr/bin/env node\n')).toBe(true)
    const binRun = spawnSync(process.execPath, ['--require', socketGuardPath, binPath], {
      input: '',
      encoding: 'utf-8',
      timeout: 3_000,
    })
    expect(binRun.error).toBeUndefined()
    expect(binRun.signal).toBeNull()
    expect(binRun.status).toBe(0)
    expect(basename(tarball)).toBe(manifest.filename)
  })
})
