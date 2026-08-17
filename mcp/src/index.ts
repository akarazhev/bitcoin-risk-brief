#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/server'
import { serveStdio } from '@modelcontextprotocol/server/stdio'
import * as z from 'zod/v4'
import { type Fetch, getJson } from './api.js'
import {
  ADVICE_LINE,
  formatBrief,
  formatCurrentRisk,
  formatHistory,
  formatLevels,
  formatReadiness,
  formatUpstreamError,
} from './format.js'
import { deriveEnvelope, type Envelope } from './freshness.js'
import { SERVER_NAME, SERVER_VERSION } from './version.js'

interface Dependencies {
  fetchImpl?: Fetch
  now?: Date
}

// A client shows these to the model when it chooses a tool, so each must say what this tool
// returns and no other does. The boundary is repeated in every one of them by design.
const BOUNDARY = 'Analytics and research context, not financial advice.'

const DESCRIPTIONS = {
  check_readiness:
    `Report whether today's Bitcoin risk data can be trusted: the seven readiness checks, the date the data covers, how many days old it is, and the tolerance. Call this first when freshness matters. ${BOUNDARY}`,
  get_current_risk:
    `Return the latest Bitcoin risk observation: the 0.0-1.0 risk value, its band (low, neutral, high), the HLC3 model price from the last completed daily candle (not a live quote), and that day's low and high. ${BOUNDARY}`,
  get_risk_history:
    `Return the daily Bitcoin risk series, oldest first, for trend and charting questions. Defaults to the last 90 days; maximum 730. ${BOUNDARY}`,
  get_risk_levels:
    `Return the solved price ladder: the BTC prices at which the model would report each risk level. Use this to answer what would have to change for the risk band to move. ${BOUNDARY}`,
  get_brief:
    `Return the daily written brief in one locale: summary, what changed, what to avoid now, and what to confirm next. Available locales are en, ru, zh, de, fr, es, ar; defaults to en. ${BOUNDARY}`,
} as const

function textResult(text: string) {
  return { content: [{ type: 'text' as const, text }] }
}

function errorResult(error: unknown) {
  const message = error instanceof Error ? error.message : 'Bitcoin Risk Brief API request failed'
  return textResult(`${message}\n${ADVICE_LINE}`)
}

async function readinessFirst(deps: Dependencies) {
  const readiness = await getJson('/api/readiness', { fetchImpl: deps.fetchImpl })
  return {
    readiness: readiness.body,
    readinessStatus: readiness.status,
    envelope: deriveEnvelope(readiness.body, deps.now),
  }
}

function formatEndpoint(
  result: { status: number; body: unknown },
  envelope: Envelope,
  formatter: (payload: unknown, envelope: Envelope) => string,
): string {
  if (result.status < 200 || result.status >= 300) {
    return formatUpstreamError(result.status, result.body, envelope)
  }
  return formatter(result.body, envelope)
}

export function createServer(deps: Dependencies = {}): McpServer {
  const server = new McpServer({ name: SERVER_NAME, version: SERVER_VERSION })

  server.registerTool('check_readiness', {
    description: DESCRIPTIONS.check_readiness,
    inputSchema: z.object({}),
  }, async () => {
    try {
      const { readiness, readinessStatus, envelope } = await readinessFirst(deps)
      return textResult(formatReadiness(readiness, envelope, readinessStatus))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_current_risk', {
    description: DESCRIPTIONS.get_current_risk,
    inputSchema: z.object({}),
  }, async () => {
    try {
      const { envelope } = await readinessFirst(deps)
      const latest = await getJson('/api/risk/latest', { fetchImpl: deps.fetchImpl })
      return textResult(formatEndpoint(latest, envelope, formatCurrentRisk))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_risk_history', {
    description: DESCRIPTIONS.get_risk_history,
    inputSchema: z.object({ days: z.number().int().min(1).max(730).default(90) }),
  }, async ({ days }) => {
    try {
      const { envelope } = await readinessFirst(deps)
      const backendLimit = Math.max(days, 2)
      const history = await getJson(`/api/risk/history?limit=${backendLimit}`, { fetchImpl: deps.fetchImpl })
      return textResult(formatEndpoint(history, envelope, (payload, currentEnvelope) => (
        formatHistory(payload, currentEnvelope, days)
      )))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_risk_levels', {
    description: DESCRIPTIONS.get_risk_levels,
    inputSchema: z.object({}),
  }, async () => {
    try {
      const { envelope } = await readinessFirst(deps)
      const levels = await getJson('/api/risk/levels', { fetchImpl: deps.fetchImpl })
      return textResult(formatEndpoint(levels, envelope, formatLevels))
    } catch (error) {
      return errorResult(error)
    }
  })

  server.registerTool('get_brief', {
    description: DESCRIPTIONS.get_brief,
    inputSchema: z.object({ locale: z.enum(['en', 'ru', 'zh', 'de', 'fr', 'es', 'ar']).default('en') }),
  }, async ({ locale }) => {
    try {
      const { envelope } = await readinessFirst(deps)
      const brief = await getJson('/api/brief/latest', { fetchImpl: deps.fetchImpl })
      return textResult(formatEndpoint(brief, envelope, (payload, currentEnvelope) => (
        formatBrief(payload, currentEnvelope, locale)
      )))
    } catch (error) {
      return errorResult(error)
    }
  })

  return server
}

if (process.argv[1] !== undefined && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  serveStdio(() => createServer())
}
