import { execFileSync, spawn, spawnSync } from 'node:child_process'
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

describe('registry metadata', () => {
  const pkg = JSON.parse(readFileSync(join(packageDir, 'package.json'), 'utf-8')) as {
    name: string
    version: string
    mcpName?: string
    repository?: { url?: string }
  }
  const server = JSON.parse(readFileSync(join(packageDir, 'server.json'), 'utf-8')) as {
    name: string
    description: string
    version: string
    repository?: { url?: string }
    packages: Array<{ registryType: string; identifier: string; version: string }>
  }

  // The registry rejects a submission whose server.json disagrees with the published package, and npm
  // versions are immutable — a mismatch caught after publishing costs a version bump to fix.
  it('names the server identically in package.json and server.json', () => {
    expect(pkg.mcpName).toBe('io.github.akarazhev/bitcoin-risk-brief')
    expect(server.name).toBe(pkg.mcpName)
  })

  it('points server.json at the package that is actually published', () => {
    const npmPackage = server.packages.find((entry) => entry.registryType === 'npm')
    expect(npmPackage?.identifier).toBe(pkg.name)
  })

  it('keeps all three versions in step', () => {
    const npmPackage = server.packages.find((entry) => entry.registryType === 'npm')
    expect(server.version).toBe(pkg.version)
    expect(npmPackage?.version).toBe(pkg.version)
  })

  it('declares the repository in both files', () => {
    expect(pkg.repository?.url).toContain('akarazhev/bitcoin-risk-brief')
    expect(server.repository?.url).toContain('akarazhev/bitcoin-risk-brief')
  })

  // The registry rejected a 141-character description with a 422. Its schema limits are pinned here so
  // a local test fails first, instead of a submission failing after the npm version is already spent.
  it('keeps server.json inside the registry schema limits', () => {
    expect(server.description.length).toBeGreaterThanOrEqual(1)
    expect(server.description.length).toBeLessThanOrEqual(100)

    expect(server.name.length).toBeGreaterThanOrEqual(3)
    expect(server.name.length).toBeLessThanOrEqual(200)
    expect(server.name).toMatch(/^[a-zA-Z0-9.-]+\/[a-zA-Z0-9._-]+$/)

    expect(server.version).not.toBe('latest')
    expect(server.version).toMatch(/^\d+\.\d+\.\d+/)

    for (const entry of server.packages) {
      expect(entry.version).not.toBe('latest')
      expect(entry.version.length).toBeGreaterThanOrEqual(1)
    }
  })

  it('still states the no-advice boundary despite the length limit', () => {
    expect(server.description.toLowerCase()).toContain('not advice')
  })
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

  // Exiting 0 is indistinguishable from serving nothing, which is how 0.1.0 shipped an entrypoint
  // guard that npm's .bin symlink defeated. This launches the way npx does and demands an answer.
  it('serves over stdio when launched through a .bin symlink, as npx launches it', async () => {
    const packDir = mkdtempSync(join(tmpdir(), 'bitcoin-risk-brief-mcp-pack-'))
    const unpackDir = mkdtempSync(join(tmpdir(), 'bitcoin-risk-brief-mcp-unpack-'))
    const npmCacheDir = mkdtempSync(join(tmpdir(), 'bitcoin-risk-brief-mcp-npm-cache-'))
    tempDirs.push(packDir, unpackDir, npmCacheDir)

    if (existsSync(distDir)) renameSync(distDir, backupDistDir)
    const packed = JSON.parse(execFileSync('npm', ['pack', '--json', '--pack-destination', packDir], {
      cwd: packageDir,
      encoding: 'utf-8',
      env: { ...process.env, npm_config_cache: npmCacheDir },
    })) as Array<{ filename: string }>
    execFileSync('tar', ['-xzf', join(packDir, packed[0].filename), '-C', unpackDir])

    const unpackedPackage = join(unpackDir, 'package')
    symlinkSync(join(packageDir, 'node_modules'), join(unpackedPackage, 'node_modules'), 'dir')

    // Reproduce node_modules/.bin: a symlink pointing at the real entrypoint.
    const binDir = join(unpackDir, 'bin')
    mkdirSync(binDir, { recursive: true })
    const linkPath = join(binDir, 'bitcoin-risk-brief-mcp')
    symlinkSync(join(unpackedPackage, 'dist', 'index.js'), linkPath, 'file')

    const child = spawn(process.execPath, [linkPath], { stdio: ['pipe', 'pipe', 'pipe'] })
    try {
      const firstResponse = new Promise<string>((resolveResponse, rejectResponse) => {
        let buffered = ''
        const timer = setTimeout(() => rejectResponse(new Error(`no response; stdout was ${JSON.stringify(buffered)}`)), 15_000)
        child.stdout.on('data', (chunk) => {
          buffered += String(chunk)
          const newline = buffered.indexOf('\n')
          if (newline !== -1) {
            clearTimeout(timer)
            resolveResponse(buffered.slice(0, newline))
          }
        })
        child.on('exit', () => {
          clearTimeout(timer)
          rejectResponse(new Error(`exited without answering; stdout was ${JSON.stringify(buffered)}`))
        })
      })

      child.stdin.write(`${JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'probe', version: '0' } },
      })}\n`)

      const message = JSON.parse(await firstResponse) as { id?: number; result?: { serverInfo?: { name?: string } } }
      expect(message.id).toBe(1)
      expect(message.result?.serverInfo?.name).toBe('bitcoin-risk-brief')
    } finally {
      child.kill()
    }
  }, 40_000)
})
