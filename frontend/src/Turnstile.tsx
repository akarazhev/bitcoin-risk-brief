import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'

const TURNSTILE_SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'

export type TurnstileHandle = { reset: () => void }

export type TurnstileRenderOptions = {
  sitekey: string
  action: string
  language: string
  theme: 'auto'
  size: 'flexible'
  callback: (token: string) => void
  'expired-callback': () => void
  'error-callback': () => void
}

type TurnstileApi = {
  render: (container: HTMLElement, options: TurnstileRenderOptions) => string
  reset: (widgetId: string) => void
  remove: (widgetId: string) => void
}

declare global {
  interface Window {
    turnstile?: TurnstileApi
  }
}

let scriptPromise: Promise<void> | undefined

function loadTurnstileScript() {
  if (window.turnstile) {
    return Promise.resolve()
  }

  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = TURNSTILE_SCRIPT_SRC
      script.async = true
      script.addEventListener('load', () => resolve(), { once: true })
      script.addEventListener('error', () => {
        script.remove()
        scriptPromise = undefined
        reject(new Error('Unable to load Turnstile'))
      }, { once: true })
      document.head.appendChild(script)
    })
  }

  return scriptPromise
}

type TurnstileProps = {
  sitekey: string
  action: string
  language: string
  onVerify: (token: string | null) => void
  onError: () => void
}

const Turnstile = forwardRef<TurnstileHandle, TurnstileProps>(function Turnstile(
  { sitekey, action, language, onVerify, onError },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string | undefined>(undefined)
  const onVerifyRef = useRef(onVerify)
  const onErrorRef = useRef(onError)
  const generationRef = useRef(0)

  onVerifyRef.current = onVerify
  onErrorRef.current = onError

  useImperativeHandle(ref, () => ({
    reset: () => {
      const widgetId = widgetIdRef.current
      if (widgetId !== undefined) {
        window.turnstile?.reset(widgetId)
      }
    },
  }), [])

  useEffect(() => {
    let cancelled = false
    let widgetId: string | undefined
    const generation = generationRef.current + 1
    generationRef.current = generation
    const isCurrentWidget = () => !cancelled && generationRef.current === generation

    const renderWidget = () => {
      if (!isCurrentWidget() || !containerRef.current || !window.turnstile) {
        return
      }

      widgetId = window.turnstile.render(containerRef.current, {
        sitekey,
        action,
        language,
        theme: 'auto',
        size: 'flexible',
        callback: (token) => {
          if (isCurrentWidget()) {
            onVerifyRef.current(token)
          }
        },
        'expired-callback': () => {
          if (isCurrentWidget()) {
            onVerifyRef.current(null)
          }
        },
        'error-callback': () => {
          if (isCurrentWidget()) {
            onVerifyRef.current(null)
            onErrorRef.current()
          }
        },
      })
      widgetIdRef.current = widgetId
    }

    if (window.turnstile) {
      renderWidget()
    } else {
      void loadTurnstileScript().then(renderWidget).catch(() => {
        if (isCurrentWidget()) {
          onErrorRef.current()
        }
      })
    }

    return () => {
      cancelled = true
      if (widgetId !== undefined) {
        window.turnstile?.remove(widgetId)
        if (widgetIdRef.current === widgetId) {
          widgetIdRef.current = undefined
        }
      }
    }
  }, [sitekey, action, language])

  return <div className="turnstile-container" ref={containerRef} />
})

export default Turnstile
