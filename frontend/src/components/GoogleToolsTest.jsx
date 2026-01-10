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
      <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
        <p className="text-sm text-gray-400">
          Connect your Google account to test Calendar and Gmail integration
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-3">
          🧪 Test Google Tools
        </h3>

        <div className="space-y-3">
          {/* Calendar Test */}
          <div>
            <button
              onClick={handleListCalendar}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
            >
              {loading ? '⏳ Loading...' : '📅 List Calendar Events (Next 5)'}
            </button>
          </div>

          {/* Gmail Test */}
          <div>
            <button
              onClick={handleSendTestEmail}
              disabled={loading}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
            >
              {loading ? '⏳ Sending...' : '✉️ Send Test Email'}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-3 p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Calendar Results */}
        {calendarEvents && (
          <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">
              Calendar Events:
            </h4>
            {calendarEvents.events && calendarEvents.events.length > 0 ? (
              <ul className="space-y-2 text-sm text-gray-300">
                {calendarEvents.events.map((event, idx) => (
                  <li key={idx} className="pl-3 border-l-2 border-blue-500/30">
                    <div className="font-medium">{event.summary || 'Untitled'}</div>
                    <div className="text-xs text-gray-400">
                      {event.start} - {event.end}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No upcoming events found</p>
            )}
          </div>
        )}

        {/* Email Results */}
        {emailResult && (
          <div className="mt-3 p-3 bg-green-500/10 border border-green-500/30 rounded">
            <h4 className="text-sm font-semibold text-green-400 mb-2">
              ✅ Email Sent Successfully
            </h4>
            <pre className="text-xs text-gray-300 overflow-x-auto">
              {JSON.stringify(emailResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
