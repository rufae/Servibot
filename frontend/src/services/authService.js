import { api } from './api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Auth service - handles Google OAuth and authentication
 */
export const authService = {
  /**
   * Get Google OAuth status for authenticated user
   * User ID is extracted from JWT token automatically
   */
  getGoogleStatus: async () => {
    try {
      const response = await api.get('/auth/google/status')
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
   * Start Google OAuth flow (opens in popup)
   */
  startGoogleAuth: (userId = 'default_user') => {
    const authUrl = `${API_BASE_URL}/auth/google/start?user_id=${encodeURIComponent(userId)}`
    const width = 600
    const height = 700
    const left = window.screen.width / 2 - width / 2
    const top = window.screen.height / 2 - height / 2
    
    const popup = window.open(
      authUrl,
      'GoogleOAuth',
      `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,location=no`
    )
    
    return popup
  },

  /**
   * Check current user authentication status
   */
  checkAuthStatus: async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await api.get('/auth/me', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
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

  /**
   * Logout current user
   */
  logout: async () => {
    try {
      const token = localStorage.getItem('auth_token')
      await api.post('/auth/logout', {}, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      localStorage.removeItem('auth_token')
      return {
        success: true,
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
      }
    }
  },

  /**
   * List calendar events (test endpoint)
   */
  listCalendarEvents: async (userId = 'default_user', maxResults = 10) => {
    try {
      const response = await api.get(`/api/tools/calendar/events?user_id=${encodeURIComponent(userId)}&max_results=${maxResults}`)
      return {
        success: true,
        data: response,
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail 
        ? (Array.isArray(error.response.data.detail) 
            ? error.response.data.detail.map(e => e.msg || e.message || String(e)).join(', ')
            : String(error.response.data.detail))
        : error.message
      return {
        success: false,
        error: errorMsg,
      }
    }
  },

  /**
   * Send email via Gmail (test endpoint)
   */
  sendEmail: async (userId = 'default_user', to, subject, body) => {
    try {
      const response = await api.post(`/api/tools/gmail/send?user_id=${encodeURIComponent(userId)}`, {
        to,
        subject,
        body,
      })
      return {
        success: true,
        data: response,
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail 
        ? (Array.isArray(error.response.data.detail) 
            ? error.response.data.detail.map(e => e.msg || e.message || String(e)).join(', ')
            : String(error.response.data.detail))
        : error.message
      return {
        success: false,
        error: errorMsg,
      }
    }
  },

  /**
   * Revoke Google OAuth access (disconnect)
   */
  revokeGoogleAccess: async (userId = 'default_user') => {
    try {
      const response = await api.post(`/auth/google/revoke?user_id=${encodeURIComponent(userId)}`)
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

export default authService
