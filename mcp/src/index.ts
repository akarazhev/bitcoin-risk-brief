import { McpServer } from '@modelcontextprotocol/server'
import { serveStdio } from '@modelcontextprotocol/server/stdio'
import * as z from 'zod/v4'
import { type Fetch, getJson } from './api.js'
import {
  formatBrief,
  formatCurrentRisk,
  formatHistory,
  formatLevels,
  formatReadiness,
} from './format.js'
import { deriveEnvelope } from './freshness.js'
import { SERVER_NAME, SERVER_VERSION } from './version.js'

interface Dependencies {
  fetchImpl?: Fetch
  now?: Date
}

const TOOL_DESCRIPTION = 'Read Bitcoin Risk Brief analytics and research context, not financial advice.'

function textResult(text: string) {
  return { content: [{ type: 'text' as const, text }] }
}

function errorResult(error: unknown) {
  return textResult(error instanceof Error ? error.message : 'Bitcoin Risk Brief API request failed')
}

async function readinessFirst(deps: Dependencies) {
  const readiness = await getJson('/api/readiness', { fetchImpl: deps.fetchImpl })
  return { readiness: readiness.body, envelope: deriveEnvelope(readiness.body, deps.now) }
}

export function createServer(deps: Dependencies = {}): McpServer {
  const server = new McpServer({ name: SERVER_NAME, version: SERVER_VERSION })

  server.registerTool('check_readiness', {
    description: TOOL_DESCRIPTION,
    inputSchema: z.object({}),
  }, async () => {
    try {
      const { readiness, envelope } = await readinessFirst(deps)
      return textResult(formatReadiness(readiness, envelope))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_current_risk', {
    description: TOOL_DESCRIPTION,
    inputSchema: z.object({}),
  }, async () => {
    try {
      const { envelope } = await readinessFirst(deps)
      const latest = await getJson('/api/risk/latest', { fetchImpl: deps.fetchImpl })
      return textResult(formatCurrentRisk(latest.body, envelope))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_risk_history', {
    description: TOOL_DESCRIPTION,
    inputSchema: z.object({ days: z.number().int().min(1).max(730).default(90) }),
  }, async ({ days }) => {
    try {
      const { envelope } = await readinessFirst(deps)
      const history = await getJson(`/api/risk/history?limit=${days}`, { fetchImpl: deps.fetchImpl })
      return textResult(formatHistory(history.body, envelope))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_risk_levels', {
    description: TOOL_DESCRIPTION,
    inputSchema: z.object({}),
  }, async () => {
    try {
      const { envelope } = await readinessFirst(deps)
      const levels = await getJson('/api/risk/levels', { fetchImpl: deps.fetchImpl })
      return textResult(formatLevels(levels.body, envelope))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_brief', {
    description: TOOL_DESCRIPTION,
    inputSchema: z.object({ locale: z.enum(['en', 'ru', 'zh', 'de', 'fr', 'es', 'ar']).default('en') }),
  }, async ({ locale }) => {
    try {
      const { envelope } = await readinessFirst(deps)
      const brief = await getJson('/api/brief/latest', { fetchImpl: deps.fetchImpl })
      return textResult(formatBrief(brief.body, envelope, locale))
    } catch (error) {
      return errorResult(error)
    }
  })

  return server
}

if (process.argv[1] !== undefined && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  serveStdio(() => createServer())
}
