// Custom hook for real-time workflow execution updates via WebSocket

import { useEffect, useState, useCallback, useRef } from 'react'
import { workflowsApi } from '@/services/workflowsApi'
import { LiveExecutionUpdate, WorkflowExecution } from '@/types/workflow'

export interface WorkflowUpdateMessage {
  type: 'execution_started' | 'execution_progress' | 'execution_completed' | 'execution_failed' | 'node_executed'
  data: LiveExecutionUpdate | WorkflowExecution | any
  timestamp: string
}

export interface UseWorkflowUpdatesOptions {
  autoConnect?: boolean
  onExecutionStarted?: (data: any) => void
  onExecutionProgress?: (data: LiveExecutionUpdate) => void
  onExecutionCompleted?: (data: WorkflowExecution) => void
  onExecutionFailed?: (data: WorkflowExecution) => void
  onNodeExecuted?: (data: any) => void
  onError?: (error: Event) => void
}

export function useWorkflowUpdates(options: UseWorkflowUpdatesOptions = {}) {
  const {
    autoConnect = true,
    onExecutionStarted,
    onExecutionProgress,
    onExecutionCompleted,
    onExecutionFailed,
    onNodeExecuted,
    onError
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<WorkflowUpdateMessage | null>(null)
  const [activeExecutions, setActiveExecutions] = useState<Map<string, LiveExecutionUpdate>>(new Map())
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const shouldConnectRef = useRef(autoConnect)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = workflowsApi.connectLiveUpdates()

      ws.onopen = () => {
        console.log('[useWorkflowUpdates] Connected')
        setIsConnected(true)
        setError(null)
      }

      ws.onclose = (event) => {
        console.log('[useWorkflowUpdates] Disconnected:', event.code)
        setIsConnected(false)
        wsRef.current = null

        // Auto-reconnect if connection was not manually closed
        if (shouldConnectRef.current && !event.wasClean) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[useWorkflowUpdates] Attempting to reconnect...')
            connect()
          }, 3000)
        }
      }

      ws.onerror = (error) => {
        console.error('[useWorkflowUpdates] Error:', error)
        setError('WebSocket connection error')
        onError?.(error)
      }

      ws.onmessage = (event) => {
        try {
          const message: WorkflowUpdateMessage = JSON.parse(event.data)
          setLastUpdate(message)

          // Handle different message types
          switch (message.type) {
            case 'execution_started':
              onExecutionStarted?.(message.data)
              if (message.data.execution_id) {
                setActiveExecutions(prev => new Map(prev).set(
                  message.data.execution_id,
                  message.data
                ))
              }
              break

            case 'execution_progress':
              onExecutionProgress?.(message.data)
              if (message.data.execution_id) {
                setActiveExecutions(prev => {
                  const updated = new Map(prev)
                  updated.set(message.data.execution_id, message.data)
                  return updated
                })
              }
              break

            case 'execution_completed':
              onExecutionCompleted?.(message.data)
              if (message.data.id) {
                setActiveExecutions(prev => {
                  const updated = new Map(prev)
                  updated.delete(message.data.id)
                  return updated
                })
              }
              break

            case 'execution_failed':
              onExecutionFailed?.(message.data)
              if (message.data.id) {
                setActiveExecutions(prev => {
                  const updated = new Map(prev)
                  updated.delete(message.data.id)
                  return updated
                })
              }
              break

            case 'node_executed':
              onNodeExecuted?.(message.data)
              break

            default:
              console.warn('[useWorkflowUpdates] Unknown message type:', message.type)
          }
        } catch (err) {
          console.error('[useWorkflowUpdates] Failed to parse message:', err)
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('[useWorkflowUpdates] Failed to create WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }, [onExecutionStarted, onExecutionProgress, onExecutionCompleted, onExecutionFailed, onNodeExecuted, onError])

  const disconnect = useCallback(() => {
    shouldConnectRef.current = false

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setIsConnected(false)
    setActiveExecutions(new Map())
  }, [])

  const subscribeToExecution = useCallback((executionId: string) => {
    if (wsRef.current) {
      workflowsApi.subscribeToExecution(wsRef.current, executionId)
    }
  }, [])

  const unsubscribeFromExecution = useCallback((executionId: string) => {
    if (wsRef.current) {
      workflowsApi.unsubscribeFromExecution(wsRef.current, executionId)
    }
  }, [])

  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      shouldConnectRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount')
      }
    }
  }, [autoConnect, connect])

  return {
    isConnected,
    lastUpdate,
    activeExecutions: Array.from(activeExecutions.values()),
    error,
    connect,
    disconnect,
    subscribeToExecution,
    unsubscribeFromExecution
  }
}

/**
 * Simplified hook for monitoring a specific execution
 */
export function useExecutionMonitor(executionId: string | null) {
  const [executionUpdate, setExecutionUpdate] = useState<LiveExecutionUpdate | null>(null)
  const [isComplete, setIsComplete] = useState(false)

  const { isConnected, subscribeToExecution, unsubscribeFromExecution } = useWorkflowUpdates({
    autoConnect: true,
    onExecutionProgress: (data) => {
      if (data.execution_id === executionId) {
        setExecutionUpdate(data)
      }
    },
    onExecutionCompleted: (data) => {
      if (data.id === executionId) {
        setIsComplete(true)
      }
    },
    onExecutionFailed: (data) => {
      if (data.id === executionId) {
        setIsComplete(true)
      }
    }
  })

  useEffect(() => {
    if (executionId && isConnected) {
      subscribeToExecution(executionId)
      return () => {
        unsubscribeFromExecution(executionId)
      }
    }
  }, [executionId, isConnected, subscribeToExecution, unsubscribeFromExecution])

  return {
    executionUpdate,
    isComplete,
    isConnected
  }
}

export default useWorkflowUpdates
