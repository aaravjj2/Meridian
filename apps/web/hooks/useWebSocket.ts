'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

type WebSocketMessage = {
  type: string
  data?: unknown
  timestamp?: string
  message?: string
  [key: string]: unknown
}

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

type UseWebSocketOptions = {
  onMessage?: (message: WebSocketMessage) => void
  onTrace?: (trace: unknown) => void
  onReflection?: (checkpoint: unknown) => void
  onComplete?: () => void
  onError?: (error: string) => void
  reconnectInterval?: number
  reconnectAttempts?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onTrace,
    onReflection,
    onComplete,
    onError,
    reconnectInterval = 3000,
    reconnectAttempts = 5,
  } = options

  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const [connectionId, setConnectionId] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setStatus('connecting')

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('connected')
        reconnectCountRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)

          // Handle specific message types
          switch (message.type) {
            case 'connected':
              setConnectionId((message.connection_id as string) || null)
              break
            case 'trace':
              onTrace?.(message.data)
              break
            case 'reflection_checkpoint':
              onReflection?.(message)
              break
            case 'complete':
              onComplete?.()
              break
            case 'error':
              onError?.(message.message || 'Unknown error')
              break
            default:
              onMessage?.(message)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = () => {
        setStatus('error')
      }

      ws.onclose = () => {
        setStatus('disconnected')

        // Attempt reconnection
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }
    } catch (err) {
      setStatus('error')
      onError?.(`Connection failed: ${err}`)
    }
  }, [url, onMessage, onTrace, onReflection, onComplete, onError, reconnectInterval, reconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('disconnected')
  }, [])

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    }
    return false
  }, [])

  const query = useCallback((question: string) => {
    return send({
      type: 'query',
      question,
    })
  }, [send])

  const ping = useCallback(() => {
    return send({ type: 'ping' })
  }, [send])

  // Auto-connect on mount
  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    status,
    connectionId,
    send,
    query,
    ping,
    disconnect,
    isConnected: status === 'connected',
  }
}

// Hook specifically for research WebSocket
export function useResearchWebSocket(options: UseWebSocketOptions = {}) {
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost:8000'
  const url = `${protocol}//${host}/api/v1/ws/research`

  return useWebSocket(url, options)
}
