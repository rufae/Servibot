/**
 * Server-Sent Events (SSE) client for streaming chat responses
 * Supports reconnection and event handling
 */

/**
 * SSE Event types from backend
 */
export const SSE_EVENT_TYPES = {
  PLAN: 'plan',
  STEP: 'step',
  RESPONSE: 'response',
  ERROR: 'error',
  DONE: 'done'
}

/**
 * Create an SSE connection to stream chat responses
 * @param {string} endpoint - API endpoint (e.g., '/api/chat/stream')
 * @param {object} payload - Request payload
 * @param {object} callbacks - Event callbacks
 * @param {function} callbacks.onPlan - Called when plan is received
 * @param {function} callbacks.onStep - Called for each execution step
 * @param {function} callbacks.onResponse - Called when final response arrives
 * @param {function} callbacks.onError - Called on error
 * @param {function} callbacks.onDone - Called when stream completes
 * @returns {object} - Control object with close() method
 */
export function createSSEConnection(endpoint, payload, callbacks = {}) {
  let eventSource = null
  let isActive = true
  const {
    onPlan = () => {},
    onStep = () => {},
    onResponse = () => {},
    onError = () => {},
    onDone = () => {}
  } = callbacks

  const connect = () => {
    // Construct URL with query params (SSE doesn't support POST body directly)
    const params = new URLSearchParams({
      message: payload.message || '',
      conversation_id: payload.conversation_id || '',
      context: payload.context ? JSON.stringify(payload.context) : ''
    })
    
    const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${endpoint}?${params}`

    eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      if (!isActive) return

      try {
        const data = JSON.parse(event.data)

        if (data === '[DONE]' || event.data === '[DONE]') {
          onDone()
          close()
          return
        }

        switch (data.type) {
          case SSE_EVENT_TYPES.PLAN:
            onPlan(data.data)
            break
          case SSE_EVENT_TYPES.STEP:
            onStep(data)
            break
          case SSE_EVENT_TYPES.RESPONSE:
            onResponse(data.data)
            break
          case SSE_EVENT_TYPES.ERROR:
            onError(data.error || 'Unknown error')
            break
          default:
            console.warn('Unknown SSE event type:', data.type)
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error, event.data)
      }
    }

    eventSource.onerror = (error) => {
      if (!isActive) return
      
      console.error('SSE connection error:', error)
      onError('Connection error')
      
      // Auto-reconnect after 3 seconds if still active
      if (eventSource.readyState === EventSource.CLOSED && isActive) {
        setTimeout(() => {
          if (isActive) {
            console.log('Reconnecting SSE...')
            connect()
          }
        }, 3000)
      }
    }

    eventSource.onopen = () => {
      console.log('SSE connection established')
    }
  }

  const close = () => {
    isActive = false
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  // Start connection
  connect()

  return {
    close,
    isActive: () => isActive
  }
}

/**
 * Fallback: Use fetch for non-streaming endpoints (backward compatibility)
 * @param {string} endpoint - API endpoint
 * @param {object} payload - Request payload
 * @returns {Promise} - Response data
 */
export async function fetchChatResponse(endpoint, payload) {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${endpoint}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}
