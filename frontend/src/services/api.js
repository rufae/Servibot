import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Retry configuration for transient errors
 */
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  retryableStatuses: [408, 429, 500, 502, 503, 504],
}

/**
 * Calculate exponential backoff delay
 */
const getRetryDelay = (retryCount) => {
  return RETRY_CONFIG.retryDelay * Math.pow(2, retryCount)
}

/**
 * Check if error is retryable
 */
const isRetryableError = (error) => {
  return (
    !error.response ||
    RETRY_CONFIG.retryableStatuses.includes(error.response.status)
  )
}

/**
 * Central API client with error handling and base configuration
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds
})

/**
 * Request interceptor for adding auth tokens, logging, etc.
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if present
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor for global error handling and retry logic
 */
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const config = error.config

    // Handle 401 Unauthorized - redirect to login ONLY if we're in a protected route
    if (error.response?.status === 401) {
      const protectedPaths = ['/app']
      const currentPath = window.location.pathname
      
      if (protectedPaths.some(path => currentPath.startsWith(path))) {
        localStorage.removeItem('auth_token')
        console.warn('Session expired or unauthorized. Redirecting to login...')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // Initialize retry count
    if (!config._retryCount) {
      config._retryCount = 0
    }

    // Check if we should retry
    if (
      config._retryCount < RETRY_CONFIG.maxRetries &&
      isRetryableError(error)
    ) {
      config._retryCount += 1
      const delay = getRetryDelay(config._retryCount - 1)

      console.warn(
        `API request failed. Retrying (${config._retryCount}/${RETRY_CONFIG.maxRetries}) after ${delay}ms...`
      )

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay))

      // Retry the request
      return apiClient(config)
    }

    // Global error handling
    const errorMessage = error.response?.data?.detail || 
                        error.response?.data?.error || 
                        error.message || 
                        'An unexpected error occurred'
    
    console.error('API Error:', errorMessage)
    
    // Re-throw with normalized error structure
    return Promise.reject({
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data,
    })
  }
)

/**
 * API service methods
 */
export const api = {
  /**
   * GET request
   */
  get: async (endpoint, config = {}) => {
    const response = await apiClient.get(endpoint, config)
    return response.data
  },

  /**
   * POST request
   */
  post: async (endpoint, data = {}, config = {}) => {
    const response = await apiClient.post(endpoint, data, config)
    return response.data
  },

  /**
   * PUT request
   */
  put: async (endpoint, data = {}, config = {}) => {
    const response = await apiClient.put(endpoint, data, config)
    return response.data
  },

  /**
   * DELETE request
   */
  delete: async (endpoint, config = {}) => {
    const response = await apiClient.delete(endpoint, config)
    return response.data
  },

  /**
   * Upload file with progress tracking
   */
  upload: async (endpoint, file, onProgress = null) => {
    const formData = new FormData()
    formData.append('file', file)

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }

    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        onProgress(percentCompleted)
      }
    }

    const response = await apiClient.post(endpoint, formData, config)
    return response.data
  },
}

export default api
export { API_BASE_URL, apiClient }
