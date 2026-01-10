/**
 * Normalize chat response to handle both string and list sources
 * Backend inconsistency: sources can be list[dict] or list[str]
 */
export const normalizeChatResponse = (response) => {
  if (!response) return null

  // Normalize sources field
  // Backend returns either an array of filename strings or objects with metadata.
  // Keep string sources as strings (UI expects strings) and ensure objects have metadata.
  if (response.sources && Array.isArray(response.sources)) {
    response.sources = response.sources.map((source) => {
      if (typeof source === 'string') {
        return source
      }
      // If source is an object, make sure metadata exists
      if (typeof source === 'object' && source !== null) {
        source.metadata = source.metadata || {}
        return source
      }
      return ''
    }).filter(Boolean)
  } else {
    response.sources = []
  }

  // Ensure response field exists
  if (!response.response) {
    response.response = ''
  }

  // Ensure execution_time field exists
  if (response.execution_time === undefined) {
    response.execution_time = 0
  }

  return response
}

/**
 * Normalize upload list response
 */
export const normalizeUploadList = (response) => {
  if (!response || !response.files) {
    return { files: [] }
  }

  response.files = response.files.map((file) => ({
    filename: file.filename || '',
    upload_date: file.upload_date || new Date().toISOString(),
    size: file.size || 0,
    status: file.status || 'unknown',
  }))

  return response
}

/**
 * Normalize upload status response
 */
export const normalizeUploadStatus = (response) => {
  if (!response) return null

  return {
    filename: response.filename || '',
    status: response.status || 'unknown',
    attempts: response.attempts || 0,
    last_attempt: response.last_attempt || null,
  }
}

/**
 * Parse SSE event data
 */
export const parseSSEEvent = (eventType, data) => {
  try {
    const parsed = typeof data === 'string' ? JSON.parse(data) : data

    switch (eventType) {
      case 'plan':
        return {
          type: 'plan',
          plan: parsed.plan || '',
        }

      case 'step':
        return {
          type: 'step',
          step: parsed.step || '',
          status: parsed.status || 'running',
        }

      case 'response':
        return {
          type: 'response',
          response: parsed.response || '',
          sources: parsed.sources || [],
        }

      case 'error':
        return {
          type: 'error',
          error: parsed.error || 'Unknown error',
        }

      case 'done':
        return {
          type: 'done',
          execution_time: parsed.execution_time || 0,
        }

      default:
        return {
          type: eventType,
          data: parsed,
        }
    }
  } catch (error) {
    console.error('Error parsing SSE event:', error)
    return {
      type: 'error',
      error: 'Failed to parse event data',
    }
  }
}
