import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    // You can log to an external service here
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-gray-900 text-white p-6 rounded-lg">
            <h3 className="text-lg font-bold mb-2">Se ha producido un error</h3>
            <p className="text-sm text-gray-300">El componente ha fallado. Recarga la página o contacta con soporte.</p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
