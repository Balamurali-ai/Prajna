/**
 * ====================================================
 * WebSocket Service
 * ====================================================
 * Wraps native WebSocket with auto-reconnect,
 * subscribe/unsubscribe, and typed messages.
 * ====================================================
 */
import { config } from '@config/index'
import type { WSMessage, WSMessageType } from '@/types'

type MessageHandler = (msg: WSMessage) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<WSMessageType | '*', Set<MessageHandler>> = new Map()
  private subscribedChannels: Set<string> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null
  private isConnecting = false

  constructor() {
    this.url = `${config.api.wsUrl}/ws/dashboard`
  }

  /**
   * Connect to the WebSocket server.
   * Auth is via the standard Authorization header on the
   * initial HTTP upgrade — but browsers can't set headers,
   * so we pass the token as a query param fallback.
   */
  connect(token?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) return

    this.isConnecting = true
    const url = token ? `${this.url}?token=${encodeURIComponent(token)}` : this.url

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        this.isConnecting = false
        this.reconnectAttempts = 0
        // Re-subscribe to any previously subscribed channels
        this.subscribedChannels.forEach((ch) => {
          this.send({ action: 'subscribe', channel: ch })
        })
        this.startHeartbeat()
        this.emit({ type: 'connected', message: 'WebSocket connected' })
      }

      this.ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data)
          this.emit(msg)
        } catch (err) {
          console.error('WS message parse error:', err)
        }
      }

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        this.emit({ type: 'error', message: 'Connection error' })
      }

      this.ws.onclose = () => {
        this.stopHeartbeat()
        this.attemptReconnect()
      }
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      this.isConnecting = false
      this.attemptReconnect()
    }
  }

  disconnect(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscribedChannels.clear()
  }

  send(message: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  subscribe(channel: string): void {
    this.subscribedChannels.add(channel)
    this.send({ action: 'subscribe', channel })
  }

  unsubscribe(channel: string): void {
    this.subscribedChannels.delete(channel)
    this.send({ action: 'unsubscribe', channel })
  }

  on(type: WSMessageType | '*', handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)
    return () => {
      this.handlers.get(type)?.delete(handler)
    }
  }

  private emit(msg: WSMessage): void {
    this.handlers.get(msg.type)?.forEach((h) => h(msg))
    this.handlers.get('*')?.forEach((h) => h(msg))
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('WebSocket max reconnect attempts reached')
      return
    }
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    setTimeout(() => {
      const token = localStorage.getItem('access_token') ?? undefined
      this.connect(token)
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.send({ action: 'ping' })
    }, 30_000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

export const wsService = new WebSocketService()
