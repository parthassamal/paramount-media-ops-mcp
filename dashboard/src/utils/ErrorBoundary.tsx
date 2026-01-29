/**
 * React Error Boundary Component
 * 
 * Catches JavaScript errors anywhere in the component tree,
 * logs errors, and displays a fallback UI.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console (or error tracking service)
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // Update state with error details
    this.setState({
      error,
      errorInfo
    });

    // Send to error tracking service (if configured)
    if (import.meta.env.PROD) {
      this.logErrorToService(error, errorInfo);
    }
  }

  logErrorToService(error: Error, errorInfo: ErrorInfo) {
    // Send error to tracking service (e.g., Sentry, DataDog)
    try {
      const errorData = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      console.log('Error logged:', errorData);
      
      // Example: Send to backend API
      // fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorData)
      // });
    } catch (loggingError) {
      console.error('Failed to log error:', loggingError);
    }
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="error-boundary-container" style={{
          padding: '2rem',
          margin: '2rem auto',
          maxWidth: '600px',
          backgroundColor: '#FEF2F2',
          border: '2px solid #EF4444',
          borderRadius: '12px',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#EF4444"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <h2 style={{ margin: 0, color: '#DC2626', fontSize: '1.5rem', fontWeight: '600' }}>
              Something went wrong
            </h2>
          </div>

          <p style={{ color: '#7F1D1D', marginBottom: '1rem', lineHeight: '1.5' }}>
            We encountered an unexpected error. This has been logged and we'll look into it.
          </p>

          {import.meta.env.DEV && this.state.error && (
            <details style={{
              backgroundColor: '#FEE2E2',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              cursor: 'pointer'
            }}>
              <summary style={{ fontWeight: '600', color: '#991B1B', marginBottom: '0.5rem' }}>
                Error Details (Dev Mode)
              </summary>
              <pre style={{
                fontSize: '0.875rem',
                overflow: 'auto',
                color: '#7F1D1D',
                margin: '0.5rem 0 0 0',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                {this.state.error.toString()}
                {this.state.errorInfo && '\n\n' + this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}

          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={this.resetError}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#EF4444',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                cursor: 'pointer',
                fontSize: '1rem',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#DC2626'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#EF4444'}
            >
              Try Again
            </button>

            <button
              onClick={() => window.location.href = '/'}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#F3F4F6',
                color: '#374151',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontWeight: '600',
                cursor: 'pointer',
                fontSize: '1rem',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#E5E7EB'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#F3F4F6'}
            >
              Go Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
