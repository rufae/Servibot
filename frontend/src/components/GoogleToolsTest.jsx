import { useState } from 'react'
import authService from '../services/authService'
import { useAuthStore } from '../store'

/**
 * GoogleToolsTest - Test buttons for Calendar and Gmail integration
 */
export default function GoogleToolsTest() {
  const { googleConnected, userId } = useAuthStore()
  const [calendarEvents, setCalendarEvents] = useState(null)
  const [emailResult, setEmailResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleListCalendar = async () => {
    setLoading(true)
    setError(null)
    setCalendarEvents(null)

    const result = await authService.listCalendarEvents(userId, 5)
    
    if (result.success) {
      setCalendarEvents(result.data)
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  const handleSendTestEmail = async () => {
    setLoading(true)
    setError(null)
    setEmailResult(null)

    const result = await authService.sendEmail(
      userId,
      'test@example.com',
      'Test from ServiBot',
      'This is a test email sent from ServiBot using Gmail API.'
    )
    
    if (result.success) {
      setEmailResult(result.data)
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  if (!googleConnected) {
    return (
      <div className="p-4 glass-effect border border-dark-800 rounded-xl backdrop-blur-sm">
        <p className="text-sm text-dark-400">
          Conecta tu cuenta de Google para probar la integración con Calendar y Gmail
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="p-4 glass-effect border border-dark-800 rounded-xl backdrop-blur-sm">
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <span className="text-2xl">🧪</span>
          <span>Probar Herramientas de Google</span>
        </h3>

        <div className="space-y-3">
          {/* Calendar Test */}
          <div>
            <button
              onClick={handleListCalendar}
              disabled={loading}
              className="w-full px-4 py-2.5 bg-gradient-to-r from-info-500 to-primary-500 hover:from-info-600 hover:to-primary-600 disabled:from-dark-800 disabled:to-dark-900 text-white rounded-xl transition-all disabled:cursor-not-allowed shadow-glow hover:shadow-glow-lg hover:scale-105 active:scale-95 disabled:scale-100 font-medium"
            >
              {loading ? '⏳ Cargando...' : '📅 Listar Eventos del Calendario (Próximos 5)'}
            </button>
          </div>

          {/* Gmail Test */}
          <div>
            <button
              onClick={handleSendTestEmail}
              disabled={loading}
              className="w-full px-4 py-2.5 bg-gradient-to-r from-success-500 to-secondary-500 hover:from-success-600 hover:to-secondary-600 disabled:from-dark-800 disabled:to-dark-900 text-white rounded-xl transition-all disabled:cursor-not-allowed shadow-glow hover:shadow-glow-lg hover:scale-105 active:scale-95 disabled:scale-100 font-medium"
            >
              {loading ? '⏳ Enviando...' : '✉️ Enviar Email de Prueba'}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-3 p-3 bg-danger-500/10 border border-danger-500/30 rounded-xl text-sm text-danger-300 backdrop-blur-sm animate-scaleIn">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        )}

        {/* Calendar Results */}
        {calendarEvents && (
          <div className="mt-3 p-3 bg-info-500/10 border border-info-500/30 rounded-xl backdrop-blur-sm animate-scaleIn">
            <h4 className="text-sm font-semibold text-info-300 mb-2 flex items-center gap-2">
              <span>📅</span>
              <span>Eventos del Calendario:</span>
            </h4>
            {calendarEvents.events && calendarEvents.events.length > 0 ? (
              <ul className="space-y-2 text-sm text-dark-200">
                {calendarEvents.events.map((event, idx) => (
                  <li key={idx} className="pl-3 border-l-2 border-info-500/50 hover:border-info-500/80 transition-colors">
                    <div className="font-medium text-white">{event.summary || 'Sin título'}</div>
                    <div className="text-xs text-dark-400">
                      {event.start} - {event.end}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-dark-400">No se encontraron eventos próximos</p>
            )}
          </div>
        )}

        {/* Email Results */}
        {emailResult && (
          <div className="mt-3 p-3 bg-success-500/10 border border-success-500/30 rounded-xl backdrop-blur-sm animate-scaleIn">
            <h4 className="text-sm font-semibold text-success-300 mb-2 flex items-center gap-2">
              <span>✅</span>
              <span>Email Enviado Exitosamente</span>
            </h4>
            <pre className="text-xs text-dark-200 overflow-x-auto bg-dark-900/50 p-2 rounded-lg custom-scrollbar">
              {JSON.stringify(emailResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
