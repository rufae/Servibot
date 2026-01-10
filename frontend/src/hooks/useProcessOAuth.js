import { useEffect } from 'react'
import { useAuthStore } from '../store'

/**
 * useProcessOAuth - Hook to process OAuth callback parameters
 * Detects oauth_success or oauth_error in URL and cleans them up
 */
export function useProcessOAuth() {
  const { setGoogleConnected } = useAuthStore()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const success = params.get('oauth_success')
    const error = params.get('oauth_error')

    if (success === 'true') {
      // OAuth succeeded - update state
      setGoogleConnected(true)
      
      // Clean URL
      params.delete('oauth_success')
      const newSearch = params.toString()
      const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '')
      window.history.replaceState({}, '', newUrl)
      
      // Optional: show success notification
      console.log('✅ Google OAuth connected successfully')
    } else if (error) {
      // OAuth failed - show error
      console.error('❌ Google OAuth error:', decodeURIComponent(error))
      
      // Clean URL
      params.delete('oauth_error')
      const newSearch = params.toString()
      const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '')
      window.history.replaceState({}, '', newUrl)
      
      // Optional: show error notification
      alert(`OAuth Error: ${decodeURIComponent(error)}`)
    }
  }, [setGoogleConnected])
}
