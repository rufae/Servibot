import { X, Check, Edit2, XCircle, Save } from 'lucide-react'
import { useEffect, useState, useMemo } from 'react'

export default function ConfirmationModal({ pendingAction, onConfirm, onEdit, onCancel }) {
  if (!pendingAction) return null

  const { action_type, action_params, confirmation_message } = pendingAction
  
  // Edit mode state - initialize once and persist across remounts using sessionStorage
  // Stable action key: use action_type plus core timestamp/title fields to avoid
  // JSON ordering or reference changes causing key instability.
  const actionKey = useMemo(() => {
    try {
      const core = `${action_params?.summary || ''}::${action_params?.start_time || ''}::${action_params?.end_time || ''}`
      const raw = `${action_type}::${core}`
      return typeof window !== 'undefined' && window.btoa ? window.btoa(unescape(encodeURIComponent(raw))) : raw
    } catch {
      return `${action_type}`
    }
  }, [action_type, action_params?.summary, action_params?.start_time, action_params?.end_time])

  const [isEditMode, setIsEditMode] = useState(() => {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        return sessionStorage.getItem(`servibot_edit_${actionKey}`) === '1'
      }
    } catch {
      // ignore
    }
    return false
  })

  const [editedParams, setEditedParams] = useState(action_params || {})

  // Keep sessionStorage in sync when actionKey changes (do not forcibly reset edit mode)
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        const v = sessionStorage.getItem(`servibot_edit_${actionKey}`)
        console.log('🔁 actionKey changed, session edit flag:', v)
        if (v === '1') setIsEditMode(true)
        // Do not clear isEditMode here; we only restore if session indicates edit mode
      }
    } catch (e) {
      console.log('⚠️ sessionStorage read failed', e)
    }
  }, [actionKey])

  // Keep editedParams in sync when pendingAction first appears
  useEffect(() => {
    setEditedParams(action_params || {})
  }, [action_params])

  // Prevent background scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [])

  const renderActionDetails = () => {
    console.log('📋 renderActionDetails called:', { action_type, isEditMode })
    
    if (action_type === 'send_email') {
      console.log('📧 Email type detected, isEditMode:', isEditMode)
      
      if (isEditMode) {
        console.log('✏️ Rendering EDIT mode for email with params:', editedParams)
        // Editable mode - use editedParams state
        return (
          <div className="bg-gradient-to-br from-orange-500/10 to-yellow-500/10 rounded-lg p-4 border-2 border-orange-500/50">
            <p className="text-orange-300 text-xs mb-3 font-bold">⚡ MODO EDICIÓN ACTIVO</p>
            <div className="space-y-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-blue-300">Para:</label>
                <input
                  type="email"
                  value={editedParams.to || action_params.to || ''}
                  onChange={(e) => {
                    console.log('📝 Email field changed:', e.target.value)
                    setEditedParams({ ...editedParams, to: e.target.value })
                  }}
                  className="bg-gray-800/90 text-white text-sm rounded-lg px-3 py-2 border-2 border-blue-500/50 focus:border-blue-500 focus:outline-none"
                  placeholder="Destinatario"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-blue-300">Asunto:</label>
                <input
                  type="text"
                  value={editedParams.subject || action_params.subject || ''}
                  onChange={(e) => {
                    console.log('📝 Subject field changed:', e.target.value)
                    setEditedParams({ ...editedParams, subject: e.target.value })
                  }}
                  className="bg-gray-800/90 text-white text-sm rounded-lg px-3 py-2 border-2 border-blue-500/50 focus:border-blue-500 focus:outline-none"
                  placeholder="Asunto del correo"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-blue-300">Mensaje:</label>
                <textarea
                  value={editedParams.body || action_params.body || ''}
                  onChange={(e) => {
                    console.log('📝 Body field changed, length:', e.target.value.length)
                    setEditedParams({ ...editedParams, body: e.target.value })
                  }}
                  rows={8}
                  className="bg-gray-800/90 text-white text-sm rounded-lg px-3 py-2 border-2 border-blue-500/50 focus:border-blue-500 focus:outline-none resize-y"
                  placeholder="Escribe el mensaje aquí..."
                />
              </div>
            </div>
          </div>
        )
      } else {
        console.log('👁️ Rendering VIEW mode for email')
        // View mode - use action_params directly from props
        return (
          <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-lg p-4 border border-blue-500/30">
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-blue-300 min-w-[60px]">Para:</span>
                <span className="text-sm text-white">{action_params.to}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-blue-300 min-w-[60px]">Asunto:</span>
                <span className="text-sm text-white">{action_params.subject}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-blue-300 min-w-[60px]">Mensaje:</span>
                <span className="text-sm text-white whitespace-pre-wrap">{action_params.body}</span>
              </div>
            </div>
          </div>
        )
      }
    }

    if (action_type === 'create_calendar_event') {
      const formatDate = (isoString) => {
        try {
          const date = new Date(isoString)
          return date.toLocaleString('es-ES', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })
        } catch {
          return isoString
        }
      }

      const formatDateForInput = (isoString) => {
        try {
          if (!isoString) return ''
          const d = new Date(isoString)
          const pad = (n) => String(n).padStart(2, '0')
          const year = d.getFullYear()
          const month = pad(d.getMonth() + 1)
          const day = pad(d.getDate())
          const hours = pad(d.getHours())
          const minutes = pad(d.getMinutes())
          return `${year}-${month}-${day}T${hours}:${minutes}`
        } catch {
          return ''
        }
      }

      if (isEditMode) {
        console.log('✏️ Rendering EDIT mode for calendar event with params:', editedParams)
        return (
          <div className="bg-gradient-to-br from-orange-500/10 to-yellow-500/10 rounded-lg p-4 border-2 border-orange-500/50">
            <p className="text-orange-300 text-xs mb-3 font-bold">⚡ MODO EDICIÓN ACTIVO</p>
            <div className="space-y-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-green-300">Título:</label>
                <input
                  type="text"
                  value={editedParams.summary || action_params.summary || ''}
                  onChange={(e) => setEditedParams({ ...editedParams, summary: e.target.value })}
                  className="bg-gray-800/90 text-white text-sm rounded-lg px-3 py-2 border-2 border-green-500/50 focus:border-green-500 focus:outline-none"
                  placeholder="Título del evento"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-green-300">Inicio:</label>
                <input
                  type="datetime-local"
                  value={formatDateForInput(editedParams.start_time || action_params.start_time)}
                  onChange={(e) => {
                    try {
                      // e.target.value is local 'YYYY-MM-DDTHH:mm'
                      const iso = new Date(e.target.value).toISOString()
                      setEditedParams({ ...editedParams, start_time: iso })
                    } catch (err) {
                      console.error('Invalid date input', err)
                    }
                  }}
                  className="bg-gray-800/90 text-white text-sm rounded-lg px-3 py-2 border-2 border-green-500/50 focus:border-green-500 focus:outline-none"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-green-300">Fin:</label>
                <input
                  type="datetime-local"
                  value={formatDateForInput(editedParams.end_time || action_params.end_time)}
                  onChange={(e) => {
                    try {
                      const iso = new Date(e.target.value).toISOString()
                      setEditedParams({ ...editedParams, end_time: iso })
                    } catch (err) {
                      console.error('Invalid date input', err)
                    }
                  }}
                  className="bg-gray-800/90 text-white text-sm rounded-lg px-3 py-2 border-2 border-green-500/50 focus:border-green-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        )
      } else {
        console.log('👁️ Rendering VIEW mode for calendar event')
        return (
          <div className="bg-gradient-to-br from-green-500/10 to-blue-500/10 rounded-lg p-4 border border-green-500/30">
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-green-300 min-w-[70px]">Título:</span>
                <span className="text-sm text-white">{action_params.summary}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-green-300 min-w-[70px]">Inicio:</span>
                <span className="text-sm text-white">{formatDate(action_params.start_time)}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-green-300 min-w-[70px]">Fin:</span>
                <span className="text-sm text-white">{formatDate(action_params.end_time)}</span>
              </div>
            </div>
          </div>
        )
      }
    }

    if (action_type === 'delete_calendar_event') {
      // Show a simple, user-friendly summary for deletions instead of raw JSON
      return (
        <div className="bg-gradient-to-br from-red-500/10 to-danger-500/10 rounded-lg p-4 border border-danger-500/30">
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-sm font-semibold text-red-300 min-w-[70px]">Evento:</span>
              <span className="text-sm text-white">{action_params?.event_title || action_params?.summary || 'Evento sin título'}</span>
            </div>
            {action_params?.start_time && (
              <div className="flex items-start gap-2">
                <span className="text-sm font-semibold text-red-300 min-w-[70px]">Fecha:</span>
                <span className="text-sm text-white">{new Date(action_params.start_time).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>
      )
    }

    // Fallback for other action types
    return (
      <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-600/30">
        <pre className="text-sm text-gray-300 whitespace-pre-wrap overflow-x-auto">
          {JSON.stringify(action_params, null, 2)}
        </pre>
      </div>
    )
  }

  const getIcon = () => {
    if (action_type === 'send_email') {
      return (
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
          <span className="text-2xl">📧</span>
        </div>
      )
    }
    if (action_type === 'create_calendar_event') {
      return (
        <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center">
          <span className="text-2xl">📅</span>
        </div>
      )
    }
    return (
      <div className="w-12 h-12 bg-gradient-to-br from-gray-500 to-gray-600 rounded-full flex items-center justify-center">
        <span className="text-2xl">⚙️</span>
      </div>
    )
  }

  const getTitle = () => {
    if (action_type === 'send_email') return 'Confirmar envío de email'
    if (action_type === 'create_calendar_event') return 'Confirmar creación de evento'
    if (action_type === 'delete_calendar_event') return 'Confirmar eliminación de evento'
    if (action_type === 'update_calendar_event') return 'Confirmar actualización de evento'
    return 'Confirmar acción'
  }

  // Check if the "Edit" button should be shown (only for email send and event creation)
  const canEdit = action_type === 'send_email' || action_type === 'create_calendar_event'
  
  // Debug logging
  console.log('🔍 ConfirmationModal render:', { action_type, canEdit, isEditMode, editedParams })

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 lg:p-6 bg-black/70 backdrop-blur-md animate-fadeIn"
    >
      <div 
        className="bg-dark-900/95 backdrop-blur-xl rounded-2xl sm:rounded-3xl shadow-2xl border border-dark-800 w-full max-w-md sm:max-w-2xl lg:max-w-4xl max-h-[80vh] sm:max-h-[85vh] overflow-hidden flex flex-col animate-scaleIn"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600/20 to-secondary-600/20 backdrop-blur-sm px-3 sm:px-4 py-2 sm:py-3 border-b border-dark-800 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2 sm:gap-3">
            {getIcon()}
            <div>
              <h2 className="text-base sm:text-xl font-bold text-white">{getTitle()}</h2>
              <p className="text-xs text-dark-400 hidden sm:block">Revisa los detalles antes de continuar</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="p-2 sm:p-2.5 rounded-xl bg-danger-500/10 hover:bg-danger-500/20 text-danger-300 hover:text-danger-100 transition-all border border-danger-400/20 hover:scale-105 active:scale-95"
            title="Cerrar"
          >
            <X className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
        </div>

        {/* Content - Scrollable */}
        <div className="px-3 sm:px-5 lg:px-6 py-3 sm:py-4 lg:py-5 space-y-3 sm:space-y-4 lg:space-y-5 overflow-y-auto flex-1 max-h-[65vh] sm:max-h-[70vh]">
          {/* Confirmation Message */}
          {confirmation_message && (
            <div className="bg-warning-500/10 border border-warning-500/30 rounded-lg sm:rounded-xl p-3 sm:p-4 backdrop-blur-sm">
              <p className="text-xs sm:text-sm text-warning-200 whitespace-pre-wrap leading-relaxed">
                {confirmation_message.split('\n').map((line, i) => {
                  // Remove "---" separator lines
                  if (line.trim() === '---') return null
                  return <span key={i}>{line}<br /></span>
                })}
              </p>
            </div>
          )}

          {/* Action-specific details (view / edit) */}
          {renderActionDetails()}

          {/* Warning */}
          <div className="bg-warning-500/10 border border-warning-500/30 rounded-lg sm:rounded-xl p-3 sm:p-4 flex items-start gap-2 sm:gap-3">
            <span className="text-lg sm:text-2xl flex-shrink-0">⚠️</span>
            <div>
              <p className="text-xs sm:text-sm font-medium text-warning-200">Importante</p>
              <p className="text-xs text-warning-300/70 mt-1">
                Esta acción se ejecutará inmediatamente al confirmar. Revisa cuidadosamente los detalles antes de continuar.
              </p>
            </div>
          </div>
        </div>

        {/* Footer - Action Buttons */}
        <div className="sticky bottom-0 z-20 bg-dark-900/95 backdrop-blur-xl px-3 sm:px-4 py-2 sm:py-3 border-t border-dark-800 flex items-center justify-end gap-2 sm:gap-3 flex-shrink-0">
          <button
            onClick={onCancel}
            className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-dark-700/50 hover:bg-dark-700 text-dark-400 hover:text-white transition-all border border-dark-600 flex items-center gap-1.5 sm:gap-2 font-medium text-xs sm:text-sm hover:scale-105 active:scale-95"
          >
            <XCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Cancelar</span>
            <span className="sm:hidden">X</span>
          </button>

          {!isEditMode ? (
            <>
              {canEdit && (
                <button
                  onClick={() => {
                    console.log('✏️ Edit button clicked, switching to edit mode')
                    // Sync editedParams with current action_params before entering edit mode
                    setEditedParams({ ...action_params })
                    setIsEditMode(true)
                    try {
                      if (typeof window !== 'undefined' && window.sessionStorage) {
                        sessionStorage.setItem(`servibot_edit_${actionKey}`, '1')
                      }
                    } catch {}
                  }}
                  className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-primary-600/20 hover:bg-primary-600/30 text-primary-300 hover:text-primary-100 transition-all border border-primary-500/30 flex items-center gap-1.5 sm:gap-2 font-medium text-xs sm:text-sm hover:scale-105 active:scale-95"
                >
                  <Edit2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  Editar
                </button>
              )}

              <button
                onClick={() => {
                  console.log('✅ ConfirmationModal - Confirmar clicked (no edit mode)')
                  console.log('   - pendingAction:', pendingAction)
                  onConfirm()
                }}
                className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-lg bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white transition-all shadow-lg shadow-green-500/20 hover:shadow-green-500/40 flex items-center gap-1.5 sm:gap-2 font-medium text-xs sm:text-sm"
              >
                <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">Confirmar y Ejecutar</span>
                <span className="sm:hidden">Confirmar</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditMode(false)}
                className="px-4 py-2.5 rounded-lg bg-gray-600/20 hover:bg-gray-600/30 text-gray-300 hover:text-white transition-all border border-gray-500/30 flex items-center gap-2 font-medium"
              >
                Cancelar Edición
              </button>

              <button
                onClick={() => {
                  // Save edited params and confirm - create clean object
                  const updatedAction = {
                    action_type: pendingAction?.action_type || 'send_email',
                    action_params: { ...editedParams },  // Clone editedParams
                    confirmation_message: pendingAction?.confirmation_message || ''
                  }
                  console.log('✏️ ConfirmationModal - Edit mode updatedAction:', updatedAction)
                  setIsEditMode(false)
                  try {
                    if (typeof window !== 'undefined' && window.sessionStorage) {
                      sessionStorage.removeItem(`servibot_edit_${actionKey}`)
                    }
                  } catch {}
                  onConfirm(updatedAction)
                }}
                className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white transition-all shadow-lg shadow-green-500/20 hover:shadow-green-500/40 flex items-center gap-2 font-medium"
              >
                <Save className="w-4 h-4" />
                Guardar y Enviar
              </button>
            </>
          )}
        </div>
      </div>

      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }

          @keyframes slideUp {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>
    </div>
  )
}
