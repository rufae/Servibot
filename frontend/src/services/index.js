import { api } from './api'
import { normalizeChatResponse, normalizeUploadList, normalizeUploadStatus } from './parsers'

/**
 * Chat service - handles all chat-related API calls
 */
export const chatService = {
  /**
   * Send a message to the chat endpoint
   */
  sendMessage: async (message, context = {}) => {
    try {
      // Ensure context is an object for backend validation (FastAPI expects dict)
      const safeContext = (context && typeof context === 'object' && !Array.isArray(context)) ? context : {}
      const response = await api.post('/api/chat', {
        message,
        context: safeContext,
      })
      return {
        success: true,
        data: normalizeChatResponse(response),
      }
    } catch (error) {
      console.error('Error sending message:', error)
      return {
        success: false,
        error: error.message,
      }
    }
  },
}

/**
 * Upload service - handles file uploads and RAG indexing
 */
export const uploadService = {
  /**
   * Upload a file with progress tracking
   */
  uploadFile: async (file, onProgress) => {
    try {
      const response = await api.upload('/api/upload', file, onProgress)
      return {
        success: true,
        data: response,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
      }
    }
  },

  /**
   * Get upload status for a file
   */
  getUploadStatus: async (fileId) => {
    try {
      const response = await api.get(`/api/upload/status/${encodeURIComponent(fileId)}`)
      return {
        success: true,
        data: normalizeUploadStatus(response),
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
      }
    }
  },

  /**
   * Reindex a file
   */
  reindexFile: async (fileId) => {
    try {
      const response = await api.post(`/api/upload/reindex/${encodeURIComponent(fileId)}`)
      return {
        success: true,
        data: response,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
      }
    }
  },

  /**
   * Get file URL
   */
  getFileUrl: (filename) => {
    return `/api/upload/file/${encodeURIComponent(filename)}`
  },
}

/**
 * Voice service - handles voice transcription and TTS
 */
export const voiceService = {
  /**
   * Transcribe audio file using Whisper
   */
  transcribe: async (audioBlob) => {
    try {
      const response = await api.upload('/api/voice/transcribe', audioBlob)
      return {
        success: true,
        data: response,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
      }
    }
  },

  /**
   * Synthesize text to speech
   */
  synthesize: async (text, language = 'es', engine = 'gtts') => {
    try {
      const response = await api.post('/api/voice/synthesize', {
        text,
        language,
        engine,
      })
      return {
        success: true,
        data: response,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
      }
    }
  },
}

// Export auth service
export { default as authService } from './authService'
