import { Clock, CheckCircle, XCircle, AlertCircle, Sparkles } from 'lucide-react'

export default function AgentTimeline({ activity }) {
  // Ensure activity is always an array
  const safeActivity = Array.isArray(activity) ? activity : []
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-success-400" />
      case 'failed':
        return <XCircle className="w-4 h-4 sm:w-5 sm:h-5 text-danger-400" />
      case 'pending':
        return <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-warning-400" />
      default:
        return <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-info-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'bg-success-500/10 border-success-500/30'
      case 'failed':
        return 'bg-danger-500/10 border-danger-500/30'
      case 'pending':
        return 'bg-warning-500/10 border-warning-500/30'
      default:
        return 'bg-info-500/10 border-info-500/30'
    }
  }

  return (
    <div className="glass-effect rounded-3xl shadow-2xl border border-white/10 p-5 sm:p-6 h-[500px] sm:h-[650px] flex flex-col backdrop-blur-xl bg-slate-800/40">
      <div className="flex items-center gap-3 mb-5">
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-secondary-500 to-accent-500 rounded-xl blur-md opacity-60 group-hover:opacity-100 transition-opacity"></div>
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-secondary-500 via-accent-500 to-warning-500 flex items-center justify-center shadow-glow-strong">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
        </div>
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-white">Actividad del Agente</h2>
          <p className="text-xs text-dark-400">Plan de ejecución en tiempo real</p>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {safeActivity.length === 0 ? (
          <div className="text-center text-dark-400 mt-16 sm:mt-20 animate-fadeIn px-4">
            <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-secondary-500/20 to-accent-500/20 flex items-center justify-center border border-secondary-500/30 shadow-glow">
              <Clock className="w-7 h-7 sm:w-8 sm:h-8 text-secondary-400" />
            </div>
            <p className="text-sm font-semibold text-white mb-1">Sin actividad aún</p>
            <p className="text-xs text-dark-500">Las acciones del agente aparecerán aquí</p>
          </div>
        ) : (
          safeActivity.map((item, idx) => (
            <div
              key={idx}
              className={`relative border rounded-xl p-3 sm:p-4 ${getStatusColor(item.status)} backdrop-blur-sm transition-all hover:scale-[1.01] animate-slideIn`}
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              {/* Timeline connector */}
              {idx < safeActivity.length - 1 && (
                <div className="absolute left-8 top-full w-0.5 h-3 bg-gradient-to-b from-dark-600 to-transparent"></div>
              )}
              
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex-shrink-0">
                  {getStatusIcon(item.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-white">Paso {item.step}</span>
                    <span className="text-xs text-dark-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.estimated_time_minutes || 1}m
                    </span>
                  </div>
                  <p className="text-sm text-dark-200 mb-2 leading-relaxed">
                    {item.action}
                  </p>
                  {item.tool && (
                    <div className="flex items-center gap-2 text-xs text-dark-400">
                      <span className="bg-dark-800/80 border border-dark-700 px-2.5 py-1 rounded-lg font-medium">
                        {item.tool}
                      </span>
                    </div>
                  )}
                  {item.requires_confirmation && (
                    <div className="mt-3 flex gap-2">
                      <button className="text-xs bg-gradient-to-r from-success-500 to-success-600 hover:from-success-600 hover:to-success-700 text-white px-3 py-1.5 rounded-lg transition-all hover:scale-105 active:scale-95 font-medium shadow-glow">
                        Confirmar
                      </button>
                      <button className="text-xs bg-gradient-to-r from-danger-500 to-danger-600 hover:from-danger-600 hover:to-danger-700 text-white px-3 py-1.5 rounded-lg transition-all hover:scale-105 active:scale-95 font-medium">
                        Rechazar
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
