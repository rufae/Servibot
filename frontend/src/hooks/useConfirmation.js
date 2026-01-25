import { useState, useCallback } from 'react'

/**
 * Hook for managing action confirmations
 * Handles pending actions that require user confirmation before execution
 */
export function useConfirmation() {
  const [pendingAction, setPendingAction] = useState(null)

  /**
   * Set a pending action that requires confirmation
   * @param {Object} action - The action data from backend (pending_confirmation)
   */
  const setPending = useCallback((action) => {
    setPendingAction(action)
  }, [])

  /**
   * Clear the pending action
   */
  const clearPending = useCallback(() => {
    setPendingAction(null)
  }, [])

  /**
   * Check if there's a pending action
   */
  const hasPending = pendingAction !== null

  return {
    pendingAction,
    setPending,
    clearPending,
    hasPending
  }
}
