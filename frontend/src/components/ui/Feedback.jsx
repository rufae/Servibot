import { XCircle, AlertTriangle, Info } from 'lucide-react'

/**
 * Toast notification component for displaying alerts
 */
export function Toast({ type = 'info', message, onClose }) {
  const styles = {
    error: {
      bg: 'bg-red-500/20',
      border: 'border-red-500/50',
      text: 'text-red-300',
      icon: <XCircle className="w-5 h-5" />,
    },
    warning: {
      bg: 'bg-yellow-500/20',
      border: 'border-yellow-500/50',
      text: 'text-yellow-300',
      icon: <AlertTriangle className="w-5 h-5" />,
    },
    info: {
      bg: 'bg-blue-500/20',
      border: 'border-blue-500/50',
      text: 'text-blue-300',
      icon: <Info className="w-5 h-5" />,
    },
    success: {
      bg: 'bg-green-500/20',
      border: 'border-green-500/50',
      text: 'text-green-300',
      icon: <Info className="w-5 h-5" />,
    },
  }

  const style = styles[type] || styles.info

  return (
    <div
      className={`fixed top-4 right-4 z-50 ${style.bg} ${style.text} border ${style.border} rounded-lg p-4 shadow-lg max-w-md animate-slideIn`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">{style.icon}</div>
        <div className="flex-1">
          <p className="text-sm leading-relaxed">{message}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 text-current opacity-70 hover:opacity-100 transition-opacity"
            aria-label="Cerrar notificación"
          >
            <XCircle className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

/**
 * Error banner component for inline error display
 */
export function ErrorBanner({ message, onRetry, onDismiss }) {
  return (
    <div
      className="bg-red-500/20 text-red-300 border border-red-500/50 rounded-lg p-4 flex items-start gap-3"
      role="alert"
    >
      <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm leading-relaxed">{message}</p>
        {(onRetry || onDismiss) && (
          <div className="mt-3 flex gap-2">
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-xs px-3 py-1.5 bg-red-500/30 hover:bg-red-500/40 rounded-lg transition-all"
              >
                Reintentar
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-xs px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg transition-all"
              >
                Cerrar
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Loading spinner component
 */
export function LoadingSpinner({ size = 'md', message = '' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3" role="status" aria-live="polite">
      <div className={`${sizes[size]} border-4 border-gray-700 border-t-primary-500 rounded-full animate-spin`} />
      {message && <p className="text-sm text-gray-400">{message}</p>}
    </div>
  )
}

/**
 * Empty state component
 */
export function EmptyState({ icon, title, description, action }) {
  return (
    <div className="text-center text-gray-400 py-12 animate-fadeIn">
      {icon && <div className="mb-4">{icon}</div>}
      {title && <p className="text-lg mb-2 font-semibold text-white">{title}</p>}
      {description && <p className="text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
