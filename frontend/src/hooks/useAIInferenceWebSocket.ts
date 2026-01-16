import { useEffect, useState, useRef, useCallback } from 'react'

// WebSocket 활성화 (Daphne ASGI 서버 사용)
const DISABLE_WEBSOCKET = false

export interface AIInferenceMessage {
  type: string
  request_id?: string
  job_id?: string
  status: string
  patient_id?: number
  model_code?: string
  result?: {
    grade?: {
      predicted_class: string
      probability: number
      probabilities?: Record<string, number>
    }
    idh?: {
      predicted_class: string
      mutant_probability: number
    }
    mgmt?: {
      predicted_class: string
      methylated_probability: number
    }
    survival?: {
      risk_score: number
      risk_category: string
    }
    os_days?: {
      predicted_days: number
      predicted_months: number
    }
    processing_time_ms?: number
  }
  error?: string
}

interface UseAIInferenceWebSocketReturn {
  lastMessage: AIInferenceMessage | null
  isConnected: boolean
  isDisabled: boolean
  connectionState: string
  connect: () => void
  disconnect: () => void
}

export function useAIInferenceWebSocket(): UseAIInferenceWebSocketReturn {
  const [lastMessage, setLastMessage] = useState<AIInferenceMessage | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionState, setConnectionState] = useState<string>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<number | null>(null)
  const connectionAttemptedRef = useRef(false)

  const connect = useCallback(() => {
    // WebSocket 비활성화 시 연결 시도하지 않음
    if (DISABLE_WEBSOCKET) {
      if (!connectionAttemptedRef.current) {
        console.log('[AI WS] WebSocket disabled for development (Django runserver)')
        connectionAttemptedRef.current = true
      }
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const token = localStorage.getItem('accessToken')
    const wsUrl = `ws://localhost:8000/ws/ai-inference/?token=${token}`

    console.log('[AI WS] Connecting...')
    setConnectionState('connecting')
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('[AI WS] Connected')
      setIsConnected(true)
      setConnectionState('connected')

      // Ping every 30 seconds
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('[AI WS] Message:', data)

        if (data.type === 'pong') {
          return
        }

        setLastMessage(data)
      } catch (e) {
        console.error('[AI WS] Parse error:', e)
      }
    }

    ws.onerror = () => {
      // 개발 모드에서 에러 로깅 최소화
      console.log('[AI WS] Connection failed (WebSocket not available)')
    }

    ws.onclose = () => {
      console.log('[AI WS] Disconnected')
      setIsConnected(false)
      setConnectionState('disconnected')

      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
        pingIntervalRef.current = null
      }
    }

    wsRef.current = ws
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    lastMessage,
    isConnected,
    isDisabled: DISABLE_WEBSOCKET,
    connectionState,
    connect,
    disconnect,
  }
}
