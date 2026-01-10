import { useState, useCallback } from 'react'

/**
 * Custom hook for managing toast notifications
 */
export function useToast() {
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((message, type = 'info', duration = 5000) => {
    const id = Date.now()
    const toast = { id, message, type }

    setToasts((prev) => [...prev, toast])

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, duration)
    }

    return id
  }, [])

  const hideToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showError = useCallback((message, duration) => {
    return showToast(message, 'error', duration)
  }, [showToast])

  const showSuccess = useCallback((message, duration) => {
    return showToast(message, 'success', duration)
  }, [showToast])

  const showWarning = useCallback((message, duration) => {
    return showToast(message, 'warning', duration)
  }, [showToast])

  const showInfo = useCallback((message, duration) => {
    return showToast(message, 'info', duration)
  }, [showToast])

  return {
    toasts,
    showToast,
    hideToast,
    showError,
    showSuccess,
    showWarning,
    showInfo,
  }
}
