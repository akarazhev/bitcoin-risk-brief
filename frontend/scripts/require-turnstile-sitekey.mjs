const sitekey = process.env.VITE_TURNSTILE_SITE_KEY?.trim()
if (!sitekey) {
  throw new Error('VITE_TURNSTILE_SITE_KEY is required for frontend builds')
}
