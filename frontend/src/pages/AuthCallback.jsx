import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { checkAuth } = useAuthStore()
  const [status, setStatus] = useState('Procesando...')

  useEffect(() => {
    const processCallback = async () => {
      const token = searchParams.get('token')
      const error = searchParams.get('error')

      if (error) {
        console.error('OAuth error:', error)
        setStatus('Error de autenticación')
        setTimeout(() => navigate('/login', { replace: true }), 2000)
        return
      }

      if (token) {
        // Store token
        localStorage.setItem('auth_token', token)
        setStatus('Token guardado, verificando...')
        
        // Small delay to ensure token is stored
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // Verify authentication
        const isAuth = await checkAuth()
        
        if (isAuth) {
          setStatus('¡Autenticado! Redirigiendo...')
          setTimeout(() => navigate('/app', { replace: true }), 500)
        } else {
          setStatus('Error al verificar sesión')
          setTimeout(() => navigate('/login', { replace: true }), 2000)
        }
      } else {
        setStatus('Token no encontrado')
        setTimeout(() => navigate('/login', { replace: true }), 2000)
      }
    }

    processCallback()
  }, [searchParams, navigate, checkAuth])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="inline-block">
          <svg className="animate-spin h-16 w-16 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <h2 className="text-2xl font-semibold text-white">{status}</h2>
        <p className="text-gray-400">Espera un momento...</p>
      </div>
    </div>
  )
}
