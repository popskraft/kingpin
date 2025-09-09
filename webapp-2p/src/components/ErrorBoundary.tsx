import React from 'react'

type Props = { children: React.ReactNode }
type State = { hasError: boolean, error?: Error }

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Basic logging; could be sent to a remote logger
    // eslint-disable-next-line no-console
    console.error('App crashed in ErrorBoundary:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback" role="alert" style={{ padding: 16 }}>
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message || 'An unexpected error occurred.'}</p>
          <button onClick={this.handleReload}>Reload</button>
        </div>
      )
    }
    return this.props.children as React.ReactElement
  }
}

