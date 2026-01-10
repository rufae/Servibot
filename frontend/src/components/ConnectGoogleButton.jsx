import { useState, useEffect } from 'react'
import authService from '../services/authService'
import { useAuthStore } from '../store'
import Swal from 'sweetalert2'

/**
 * ConnectGoogleButton - Button to initiate Google OAuth flow
 * Opens popup, polls for completion, and updates connection state
 */
export default function ConnectGoogleButton() {
  const { googleConnected, googleEmail, userId, setGoogleConnected } = useAuthStore()
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState(null)

  // Check status on mount
  useEffect(() => {
    checkGoogleStatus()
  }, [])

  const checkGoogleStatus = async () => {
    const result = await authService.getGoogleStatus(userId)
    if (result.success && result.data.connected) {
      setGoogleConnected(true, result.data.email)
    }
  }

  const handleConnect = async () => {
    setIsConnecting(true)
    setError(null)

    // Open OAuth popup
    const popup = authService.startGoogleAuth(userId)

    if (!popup) {
      setError('Popup blocked. Please allow popups for this site.')
      setIsConnecting(false)
      return
    }

    // Poll for completion (check every 1 second for up to 2 minutes)
    let attempts = 0
    const maxAttempts = 120
    
    const pollInterval = setInterval(async () => {
      attempts++

      // Check if popup was closed manually (wrapped in try-catch to handle COOP)
      try {
        if (popup.closed) {
          clearInterval(pollInterval)
          setIsConnecting(false)
          return
        }
      } catch (e) {
        // Ignore COOP error - popup may be on different origin
      }

      // Check backend status
      const result = await authService.getGoogleStatus(userId)
      
      if (result.success && result.data.connected) {
        // Success! Close popup and update state
        clearInterval(pollInterval)
        try {
          popup.close()
        } catch (e) {
          // Ignore COOP error when closing popup
        }
        setGoogleConnected(true, result.data.email)
        setIsConnecting(false)
        return
      }

      // Timeout after maxAttempts
      if (attempts >= maxAttempts) {
        clearInterval(pollInterval)
        try {
          popup.close()
        } catch (e) {
          // Ignore COOP error when closing popup
        }
        setError('Connection timeout. Please try again.')
        setIsConnecting(false)
      }
    }, 1000)
  }

  const handleDisconnect = async () => {
    const swalResult = await Swal.fire({
      title: '¿Desconectar cuenta de Google?',
      text: 'Necesitarás volver a conectar para usar Calendar y Gmail',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Sí, desconectar',
      cancelButtonText: 'Cancelar',
      background: '#1f2937',
      color: '#f3f4f6'
    })

    if (!swalResult.isConfirmed) {
      return
    }

    setIsConnecting(true)
    setError(null)

    const res = await authService.revokeGoogleAccess(userId)
    
    if (res.success) {
      setGoogleConnected(false, null)
      try {
        Swal.fire({
          title: 'Desconectado',
          icon: 'success',
          timer: 1400,
          showConfirmButton: false,
          background: '#1f2937',
          color: '#f3f4f6'
        })
      } catch (e) {
        // ignore
      }
    } else {
      setError(`Error al desconectar: ${res.error}`)
      try {
        Swal.fire({
          title: 'Error al desconectar',
          text: String(res.error),
          icon: 'error',
          background: '#1f2937',
          color: '#f3f4f6'
        })
      } catch (e) {
        // ignore
      }
    }
    
    setIsConnecting(false)
  }

  if (googleConnected) {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-3 px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg">
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <div className="text-sm font-medium text-green-400">Google Connected</div>
            {googleEmail && (
              <div className="text-xs text-gray-400">{googleEmail}</div>
            )}
          </div>
        </div>

        <button
          onClick={handleDisconnect}
          disabled={isConnecting}
          className="w-full px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isConnecting ? 'Desconectando...' : 'Desconectar Google'}
        </button>

        {error && (
          <div className="px-3 py-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
            {error}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleConnect}
        disabled={isConnecting}
        className="flex items-center justify-center gap-3 w-full px-4 py-3 bg-white hover:bg-gray-50 disabled:bg-gray-300 text-gray-900 font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
      >
        {isConnecting ? (
          <>
            <svg className="animate-spin h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Connecting to Google...</span>
          </>
        ) : (
          <>
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Connect Google Account</span>
          </>
        )}
      </button>

      {error && (
        <div className="px-3 py-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
          {error}
        </div>
      )}

      <p className="text-xs text-gray-500 text-center">
        Required for Calendar and Gmail integration
      </p>
    </div>
  )
}
