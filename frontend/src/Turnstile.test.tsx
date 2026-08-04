import { act, createRef } from 'react'
import { render, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import Turnstile, { type TurnstileHandle, type TurnstileRenderOptions } from './Turnstile'

const TURNSTILE_SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'

type TurnstileStub = {
  render: ReturnType<typeof vi.fn>
  reset: ReturnType<typeof vi.fn>
  remove: ReturnType<typeof vi.fn>
}

function installTurnstileStub(
  renderWidget: TurnstileStub['render'] = vi.fn(() => 'widget-1'),
) {
  const resetWidget = vi.fn()
  const removeWidget = vi.fn()

  Object.assign(window, {
    turnstile: { render: renderWidget, reset: resetWidget, remove: removeWidget },
  })

  return { renderWidget, resetWidget, removeWidget }
}

function renderTurnstile(overrides: Partial<React.ComponentProps<typeof Turnstile>> = {}) {
  return render(
    <Turnstile
      sitekey="1x00000000000000000000AA"
      action="waitlist"
      language="en"
      onVerify={vi.fn()}
      onError={vi.fn()}
      {...overrides}
    />,
  )
}

beforeEach(() => {
  document.querySelectorAll(`script[src="${TURNSTILE_SCRIPT_SRC}"]`).forEach((script) => script.remove())
  delete window.turnstile
})

afterEach(() => {
  delete window.turnstile
})

test('renders the widget with the configured options and exposes reset', async () => {
  const renderWidget = vi.fn((_container: HTMLElement, options: TurnstileRenderOptions) => {
    options.callback('fresh-token')
    return 'widget-1'
  })
  const resetWidget = vi.fn()
  const removeWidget = vi.fn()

  Object.assign(window, {
    turnstile: { render: renderWidget, reset: resetWidget, remove: removeWidget },
  })

  const handle = createRef<TurnstileHandle>()
  const onVerify = vi.fn()
  render(<Turnstile
    ref={handle}
    sitekey="1x00000000000000000000AA"
    action="waitlist"
    language="en"
    onVerify={onVerify}
    onError={vi.fn()}
  />)

  await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(1))
  expect(renderWidget.mock.calls[0][1]).toMatchObject({
    sitekey: '1x00000000000000000000AA',
    action: 'waitlist',
    language: 'en',
  })
  expect(onVerify).toHaveBeenCalledWith('fresh-token')
  act(() => handle.current?.reset())
  expect(resetWidget).toHaveBeenCalledWith('widget-1')
})

test('clears the verified token when the widget expires', async () => {
  const { renderWidget } = installTurnstileStub()
  const onVerify = vi.fn()

  renderTurnstile({ onVerify })

  await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(1))
  act(() => renderWidget.mock.calls[0][1]['expired-callback']())

  expect(onVerify).toHaveBeenCalledWith(null)
})

test('clears the verified token and reports widget errors', async () => {
  const { renderWidget } = installTurnstileStub()
  const onVerify = vi.fn()
  const onError = vi.fn()

  renderTurnstile({ onVerify, onError })

  await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(1))
  act(() => renderWidget.mock.calls[0][1]['error-callback']())

  expect(onVerify).toHaveBeenCalledWith(null)
  expect(onError).toHaveBeenCalledTimes(1)
})

test('removes and re-renders the widget when the language changes', async () => {
  const { renderWidget, removeWidget } = installTurnstileStub()
  const { rerender } = renderTurnstile()

  await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(1))
  rerender(
    <Turnstile
      sitekey="1x00000000000000000000AA"
      action="waitlist"
      language="de"
      onVerify={vi.fn()}
      onError={vi.fn()}
    />,
  )

  await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(2))
  expect(removeWidget).toHaveBeenCalledWith('widget-1')
  expect(renderWidget.mock.calls[1][1]).toMatchObject({ language: 'de' })
})

test('removes the widget when unmounted', async () => {
  const { renderWidget, removeWidget } = installTurnstileStub()
  const { unmount } = renderTurnstile()

  await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(1))
  unmount()

  expect(removeWidget).toHaveBeenCalledWith('widget-1')
})

test('reports failed script loading and lets a later mount retry', async () => {
  const firstError = vi.fn()
  renderTurnstile({ onError: firstError })

  const firstScript = await waitFor(() => {
    const script = document.querySelector<HTMLScriptElement>(`script[src="${TURNSTILE_SCRIPT_SRC}"]`)
    expect(script).not.toBeNull()
    return script as HTMLScriptElement
  })

  act(() => firstScript.dispatchEvent(new Event('error')))

  await waitFor(() => expect(firstError).toHaveBeenCalledTimes(1))
  expect(firstScript).not.toBeInTheDocument()

  const secondError = vi.fn()
  renderTurnstile({ onError: secondError })

  const retryScript = await waitFor(() => {
    const script = document.querySelector<HTMLScriptElement>(`script[src="${TURNSTILE_SCRIPT_SRC}"]`)
    expect(script).not.toBeNull()
    return script as HTMLScriptElement
  })

  expect(retryScript).not.toBe(firstScript)

  act(() => retryScript.dispatchEvent(new Event('error')))
  await waitFor(() => expect(secondError).toHaveBeenCalledTimes(1))
})

test('injects one explicit Turnstile script when the API is absent', async () => {
  const onVerify = vi.fn()

  render(
    <>
      <Turnstile
        sitekey="1x00000000000000000000AA"
        action="waitlist"
        language="en"
        onVerify={onVerify}
        onError={vi.fn()}
      />
      <Turnstile
        sitekey="1x00000000000000000000AA"
        action="waitlist"
        language="en"
        onVerify={onVerify}
        onError={vi.fn()}
      />
    </>,
  )

  await waitFor(() => {
    expect(document.querySelectorAll(`script[src="${TURNSTILE_SCRIPT_SRC}"]`)).toHaveLength(1)
  })
})
