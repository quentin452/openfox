import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setupSignalShutdown } from '../server/index.js'

type Listener = (...args: unknown[]) => void

describe('setupSignalShutdown', () => {
  let listeners: Record<string, Listener>
  let mockProc: {
    on: ReturnType<typeof vi.fn>
    removeListener: ReturnType<typeof vi.fn>
    kill: ReturnType<typeof vi.fn>
    exit: ReturnType<typeof vi.fn>
    pid: number
  }

  beforeEach(() => {
    listeners = {}
    mockProc = {
      on: vi.fn((event: string, fn: Listener) => {
        listeners[event] = fn
      }),
      removeListener: vi.fn(),
      kill: vi.fn(),
      exit: vi.fn(),
      pid: 12345,
    }
  })

  it('registers SIGINT and SIGTERM listeners on startup', () => {
    const mockHandle = { close: vi.fn().mockResolvedValue(undefined) }

    setupSignalShutdown(mockHandle, mockProc as any)

    expect(mockProc.on).toHaveBeenCalledWith('SIGINT', expect.any(Function))
    expect(mockProc.on).toHaveBeenCalledWith('SIGTERM', expect.any(Function))
    expect(listeners['SIGINT']).toBeDefined()
    expect(listeners['SIGTERM']).toBeDefined()
  })

  it('closes handle, removes signal listeners, and re-raises SIGINT signal on process', async () => {
    const mockHandle = { close: vi.fn().mockResolvedValue(undefined) }

    const { shutdown } = setupSignalShutdown(mockHandle, mockProc as any)

    await shutdown('SIGINT')

    expect(mockHandle.close).toHaveBeenCalledTimes(1)
    expect(mockProc.removeListener).toHaveBeenCalledWith('SIGINT', expect.any(Function))
    expect(mockProc.removeListener).toHaveBeenCalledWith('SIGTERM', expect.any(Function))
    expect(mockProc.kill).toHaveBeenCalledWith(12345, 'SIGINT')
    expect(mockProc.exit).not.toHaveBeenCalledWith(0)
  })

  it('closes handle, removes signal listeners, and re-raises SIGTERM signal on process', async () => {
    const mockHandle = { close: vi.fn().mockResolvedValue(undefined) }

    const { shutdown } = setupSignalShutdown(mockHandle, mockProc as any)

    await shutdown('SIGTERM')

    expect(mockHandle.close).toHaveBeenCalledTimes(1)
    expect(mockProc.removeListener).toHaveBeenCalledWith('SIGINT', expect.any(Function))
    expect(mockProc.removeListener).toHaveBeenCalledWith('SIGTERM', expect.any(Function))
    expect(mockProc.kill).toHaveBeenCalledWith(12345, 'SIGTERM')
    expect(mockProc.exit).not.toHaveBeenCalledWith(0)
  })

  it('triggers shutdown when SIGINT listener is called', async () => {
    const mockHandle = { close: vi.fn().mockResolvedValue(undefined) }

    setupSignalShutdown(mockHandle, mockProc as any)

    const sigintListener = listeners['SIGINT']!
    sigintListener()

    // Allow async shutdown to resolve
    await new Promise((resolve) => setTimeout(resolve, 10))

    expect(mockHandle.close).toHaveBeenCalledTimes(1)
    expect(mockProc.kill).toHaveBeenCalledWith(12345, 'SIGINT')
  })
})
