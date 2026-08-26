import { beforeEach, describe, expect, it, vi } from 'vitest'

const reactDom = vi.hoisted(() => {
  const render = vi.fn()
  return {
    render,
    createRoot: vi.fn(() => ({ render })),
    hydrateRoot: vi.fn(),
  }
})

vi.mock('react-dom/client', () => ({
  default: {
    createRoot: reactDom.createRoot,
    hydrateRoot: reactDom.hydrateRoot,
  },
  createRoot: reactDom.createRoot,
  hydrateRoot: reactDom.hydrateRoot,
}))

beforeEach(() => {
  vi.resetModules()
  reactDom.render.mockClear()
  reactDom.createRoot.mockClear()
  reactDom.hydrateRoot.mockClear()
  document.body.innerHTML = '<div id="root"></div>'
})

describe('main entry', () => {
  it('mounts when vite dev provides an empty root', async () => {
    const container = document.getElementById('root')!

    await import('./main')

    expect(reactDom.createRoot).toHaveBeenCalledWith(container)
    expect(reactDom.render).toHaveBeenCalledTimes(1)
    expect(reactDom.hydrateRoot).not.toHaveBeenCalled()
  })

  it('hydrates a prerendered production root', async () => {
    const container = document.getElementById('root')!
    container.innerHTML = '<main>Prerendered</main>'

    await import('./main')

    expect(reactDom.hydrateRoot).toHaveBeenCalledWith(container, expect.anything())
    expect(reactDom.createRoot).not.toHaveBeenCalled()
  })
})
