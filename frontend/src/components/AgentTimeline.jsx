import { Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export default function AgentTimeline({ activity }) {
  // Ensure activity is always an array
  const safeActivity = Array.isArray(activity) ? activity : []
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'pending':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      default:
        return <Clock className="w-5 h-5 text-blue-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'bg-green-500/20 border-green-500/50'
      case 'failed':
        return 'bg-red-500/20 border-red-500/50'
      case 'pending':
        return 'bg-yellow-500/20 border-yellow-500/50'
      default:
        return 'bg-blue-500/20 border-blue-500/50'
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow-xl border border-gray-700 p-4 sm:p-6 h-[500px] sm:h-[600px] flex flex-col">
      <h2 className="text-lg sm:text-xl font-semibold mb-4">Agent Activity</h2>
      
      <div className="flex-1 overflow-y-auto space-y-4">
        {safeActivity.length === 0 ? (
          <div className="text-center text-gray-400 mt-20">
            <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No activity yet</p>
            <p className="text-xs mt-1">Agent actions will appear here</p>
          </div>
        ) : (
          safeActivity.map((item, idx) => (
            <div
              key={idx}
              className={`border rounded-lg p-4 ${getStatusColor(item.status)}`}
            >
              <div className="flex items-start space-x-3">
                <div className="mt-0.5">
                  {getStatusIcon(item.status)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold">Step {item.step}</span>
                    <span className="text-xs text-gray-400">
                      {item.estimated_time_minutes || 1}m
                    </span>
                  </div>
                  <p className="text-sm text-gray-200 mb-2">
                    {item.action}
                  </p>
                  {item.tool && (
                    <div className="flex items-center space-x-2 text-xs text-gray-400">
                      <span className="bg-gray-700 px-2 py-1 rounded">
                        {item.tool}
                      </span>
                    </div>
                  )}
                  {item.requires_confirmation && (
                    <div className="mt-2 flex space-x-2">
                      <button className="text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded">
                        Confirm
                      </button>
                      <button className="text-xs bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded">
                        Decline
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
