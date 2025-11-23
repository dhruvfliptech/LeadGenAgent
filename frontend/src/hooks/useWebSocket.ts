import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

export interface WebSocketOptions {
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export interface WebSocketState {
  socket: WebSocket | null
  isConnected: boolean
  isConnecting: boolean
  lastMessage: WebSocketMessage | null
  connectionAttempts: number
  error: string | null
}

const DEFAULT_OPTIONS: Required<Omit<WebSocketOptions, 'onOpen' | 'onClose' | 'onError' | 'onMessage'>> = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
}

export function useWebSocket(url: string, options: WebSocketOptions = {}) {
  const [state, setState] = useState<WebSocketState>({
    socket: null,
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    connectionAttempts: 0,
    error: null,
  })

  const optionsRef = useRef({ ...DEFAULT_OPTIONS, ...options })
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const shouldReconnectRef = useRef(true)

  const connect = useCallback(() => {
    // Use ref to check connection state to avoid stale closure issues
    if (state.isConnecting || state.isConnected) {
      return
    }

    setState(prev => ({
      ...prev,
      isConnecting: true,
      error: null,
    }))

    try {
      const socket = new WebSocket(url)

      socket.onopen = () => {
        setState(prev => ({
          ...prev,
          socket,
          isConnected: true,
          isConnecting: false,
          connectionAttempts: 0,
          error: null,
        }))
        optionsRef.current.onOpen?.()
      }

      socket.onclose = (event) => {
        setState(prev => ({
          ...prev,
          socket: null,
          isConnected: false,
          isConnecting: false,
        }))

        optionsRef.current.onClose?.()

        // Attempt to reconnect if it wasn't a manual close
        if (shouldReconnectRef.current && !event.wasClean) {
          setState(prev => {
            const newAttempts = prev.connectionAttempts + 1

            if (newAttempts <= optionsRef.current.maxReconnectAttempts) {
              reconnectTimeoutRef.current = setTimeout(() => {
                connect()
              }, optionsRef.current.reconnectInterval)
            } else {
              return {
                ...prev,
                error: 'Max reconnection attempts reached',
                connectionAttempts: newAttempts,
              }
            }

            return {
              ...prev,
              connectionAttempts: newAttempts,
            }
          })
        }
      }

      socket.onerror = (error) => {
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false,
        }))
        optionsRef.current.onError?.(error)
      }

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = {
            type: 'message',
            data: JSON.parse(event.data),
            timestamp: Date.now(),
          }

          setState(prev => ({
            ...prev,
            lastMessage: message,
          }))

          optionsRef.current.onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to create WebSocket connection',
        isConnecting: false,
      }))
    }
  // Only depend on url - state is handled via setState callbacks
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (state.socket) {
      state.socket.close(1000, 'Manual disconnect')
    }

    setState(prev => ({
      ...prev,
      socket: null,
      isConnected: false,
      isConnecting: false,
    }))
  }, [state.socket])

  const sendMessage = useCallback((data: any) => {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not connected. Cannot send message.')
      return false
    }

    try {
      state.socket.send(JSON.stringify(data))
      return true
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
      return false
    }
  }, [state.socket])

  const reconnect = useCallback(() => {
    disconnect()
    shouldReconnectRef.current = true
    setState(prev => ({ ...prev, connectionAttempts: 0 }))
    setTimeout(connect, 100)
  }, [connect, disconnect])

  // Connect on mount
  useEffect(() => {
    connect()
    
    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [connect])

  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = { ...DEFAULT_OPTIONS, ...options }
  }, [options])

  return {
    ...state,
    connect,
    disconnect,
    reconnect,
    sendMessage,
  }
}

// Specialized hooks for different types of real-time updates
// Note: All hooks now connect to the unified /ws endpoint
// The backend uses a single WebSocket endpoint that handles all message types

export function useLeadUpdates() {
  const wsEnv = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'
  // Use the unified /ws endpoint (backend doesn't have /ws/leads)
  const wsUrl = `${wsEnv}/ws`

  return useWebSocket(wsUrl, {
    maxReconnectAttempts: 5,
    onMessage: (message) => {
      // Filter for lead-related messages
      if (message.data.type === 'lead_update' || message.data.type === 'lead') {
        // Lead update received - handled by React Query invalidation
      }
    }
  })
}

export function useNotificationUpdates() {
  const wsEnv = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'
  // Use the unified /ws endpoint (backend doesn't have /ws/notifications)
  const wsUrl = `${wsEnv}/ws`

  return useWebSocket(wsUrl, {
    maxReconnectAttempts: 5,
    onMessage: (message) => {
      // Filter for notification-related messages
      if (message.data.type === 'notification') {
        // Notification received - handled by application
      }
    }
  })
}

export function useScheduleUpdates() {
  const wsEnv = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'
  // Use the unified /ws endpoint (backend doesn't have /ws/schedules)
  const wsUrl = `${wsEnv}/ws`

  return useWebSocket(wsUrl, {
    maxReconnectAttempts: 5,
    onMessage: (message) => {
      // Filter for schedule-related messages
      if (message.data.type === 'schedule_update' || message.data.type === 'schedule') {
        // Schedule update received - handled by application
      }
    }
  })
}

export function useAnalyticsUpdates() {
  const wsEnv = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'
  // Use the unified /ws endpoint (backend doesn't have /ws/analytics)
  const wsUrl = `${wsEnv}/ws`

  return useWebSocket(wsUrl, {
    maxReconnectAttempts: 5,
    onMessage: (message) => {
      // Filter for analytics-related messages
      if (message.data.type === 'analytics_update' || message.data.type === 'analytics') {
        // Analytics update received - handled by application
      }
    }
  })
}

export function useConversationUpdates() {
  const wsEnv = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'
  // Use the unified /ws endpoint
  const wsUrl = `${wsEnv}/ws`

  return useWebSocket(wsUrl, {
    maxReconnectAttempts: 5,
    onMessage: (message) => {
      // Filter for conversation-related messages
      if (
        message.data.type === 'conversation:new_reply' ||
        message.data.type === 'conversation:ai_ready' ||
        message.data.type === 'conversation:sent' ||
        message.data.type === 'conversation:error'
      ) {
        // Conversation update received - handled by application
      }
    }
  })
}