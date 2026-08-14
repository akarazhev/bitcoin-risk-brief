export type Fetch = typeof fetch

export class ApiUnreachable extends Error {
  constructor(cause?: unknown) {
    super('Bitcoin Risk Brief API is unreachable', { cause })
    this.name = 'ApiUnreachable'
  }
}

export class ApiMalformed extends Error {
  constructor(cause?: unknown) {
    super('Bitcoin Risk Brief API returned malformed JSON', { cause })
    this.name = 'ApiMalformed'
  }
}

export function baseUrl(): string {
  return (process.env.BRB_API_BASE_URL ?? 'https://bitcoinriskbrief.minihub.app').replace(/\/+$/, '')
}

export async function getJson(
  path: string,
  opts?: { fetchImpl?: Fetch },
): Promise<{ status: number; body: unknown }> {
  const fetchImpl = opts?.fetchImpl ?? globalThis.fetch
  const url = `${baseUrl()}${path.startsWith('/') ? path : `/${path}`}`

  let response: Response
  try {
    response = await fetchImpl(url, { signal: AbortSignal.timeout(15_000) })
  } catch (error) {
    throw new ApiUnreachable(error)
  }

  try {
    return { status: response.status, body: await response.json() }
  } catch (error) {
    throw new ApiMalformed(error)
  }
}
