/**
 * Backend API Contracts Documentation
 * This file documents the expected request/response formats for backend endpoints
 */

/**
 * Chat API - POST /api/chat
 * 
 * Request:
 * {
 *   message: string,
 *   context?: string[]
 * }
 * 
 * Response:
 * {
 *   response: string,
 *   timestamp: string (ISO format),
 *   sources?: Array<{
 *     filename: string,
 *     metadata?: { source: string }
 *   }>,
 *   plan?: Array<{
 *     step: number,
 *     action: string,
 *     tool?: string,
 *     status: 'pending' | 'completed' | 'failed' | 'success',
 *     estimated_time_minutes?: number,
 *     requires_confirmation?: boolean
 *   }>,
 *   generated_file?: {
 *     filename: string,
 *     download_url: string
 *   }
 * }
 */

/**
 * Upload API - POST /api/upload
 * 
 * Request: FormData with 'file' field
 * 
 * Response:
 * {
 *   file_id: string,
 *   filename: string,
 *   status: string
 * }
 */

/**
 * Upload Status API - GET /api/upload/status/{file_id}
 * 
 * Response:
 * {
 *   status: 'pending' | 'indexing' | 'indexed' | 'error' | 'retrying',
 *   attempts?: number
 * }
 */

/**
 * Reindex API - POST /api/upload/reindex/{file_id}
 * 
 * Response:
 * {
 *   status: string,
 *   message: string
 * }
 */

/**
 * Voice Transcribe API - POST /api/voice/transcribe
 * 
 * Request: FormData with 'file' field (audio blob)
 * 
 * Response:
 * {
 *   status: 'success' | 'error',
 *   text: string,
 *   error?: string
 * }
 */

/**
 * Voice Synthesize API - POST /api/voice/synthesize
 * 
 * Request:
 * {
 *   text: string,
 *   language: string (default: 'es'),
 *   engine: string (default: 'gtts')
 * }
 * 
 * Response:
 * {
 *   status: 'success' | 'error',
 *   audio_url: string,
 *   error?: string
 * }
 */

/**
 * Type definitions (JSDoc format for JS codebase)
 */

/**
 * @typedef {Object} ChatMessage
 * @property {'user' | 'assistant'} role
 * @property {string} content
 * @property {string} timestamp
 * @property {Array<Source>} [sources]
 * @property {Array<AgentStep>} [plan]
 * @property {boolean} [error]
 */

/**
 * @typedef {Object} Source
 * @property {string} filename
 * @property {Object} [metadata]
 * @property {string} [metadata.source]
 */

/**
 * @typedef {Object} AgentStep
 * @property {number} step
 * @property {string} action
 * @property {string} [tool]
 * @property {'pending' | 'completed' | 'failed' | 'success'} status
 * @property {number} [estimated_time_minutes]
 * @property {boolean} [requires_confirmation]
 */

/**
 * @typedef {Object} UploadedFile
 * @property {string} name
 * @property {number} size
 * @property {string} type
 * @property {'uploading' | 'success' | 'error'} status
 * @property {number} [progress]
 * @property {string} [file_id]
 * @property {'pending' | 'indexing' | 'indexed' | 'error' | 'retrying'} [indexing_status]
 * @property {number} [attempts]
 * @property {string} [error]
 */

/**
 * @typedef {Object} VoiceTranscribeResponse
 * @property {'success' | 'error'} status
 * @property {string} [text]
 * @property {string} [error]
 */

/**
 * @typedef {Object} VoiceSynthesizeResponse
 * @property {'success' | 'error'} status
 * @property {string} [audio_url]
 * @property {string} [error]
 */

export {}
