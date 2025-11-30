import { useState } from 'react';

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const API_URL = 'https://j0hz2ok0kb.execute-api.us-east-1.amazonaws.com/dev/analyze';

  const analyzeTicker = async () => {
    if (!ticker) return;
    
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputText: `Analyze ${ticker} stock with comprehensive analysis including technical and sentiment data`
        }),
      });

      const data = await response.json();
      
      // API Gateway returns data directly
      if (data.ticker) {
        setResult(data);
      } else {
        setError('Unexpected response format');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>📈 Trading Supervisor</h1>
        <p style={styles.subtitle}>Multi-Agent Stock Analysis</p>

        <div style={styles.inputGroup}>
          <input
            type="text"
            placeholder="Enter stock ticker (e.g., AAPL)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && analyzeTicker()}
            style={styles.input}
          />
          <button
            onClick={analyzeTicker}
            disabled={loading || !ticker}
            style={{
              ...styles.button,
              ...(loading || !ticker ? styles.buttonDisabled : {})
            }}
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {error && (
          <div style={styles.error}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {result && (
          <div style={styles.results}>
            <div style={{
              ...styles.recommendation,
              backgroundColor: result.recommendation === 'BUY' ? '#10b981' : result.recommendation === 'SELL' ? '#ef4444' : '#f59e0b'
            }}>
              <h2 style={styles.recommendationText}>{result.recommendation}</h2>
              <p style={styles.confidence}>Confidence: {Math.round(result.confidence * 100)}%</p>
            </div>

            <div style={styles.summary}>
              <p>{result.summary}</p>
            </div>

            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>📊 Technical Analysis</h3>
              {result.technical_analysis && !result.technical_analysis.error ? (
                <div style={styles.metrics}>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Current Price:</span>
                    <span style={styles.metricValue}>${result.technical_analysis.current_price?.toFixed(2)}</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>RSI:</span>
                    <span style={styles.metricValue}>{result.technical_analysis.rsi?.toFixed(2)}</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Signal:</span>
                    <span style={styles.metricValue}>{result.technical_analysis.rsi_signal}</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>24h Change:</span>
                    <span style={{
                      ...styles.metricValue,
                      color: result.technical_analysis.price_change_24h >= 0 ? '#10b981' : '#ef4444'
                    }}>
                      ${result.technical_analysis.price_change_24h?.toFixed(2)}
                    </span>
                  </div>
                </div>
              ) : (
                <p style={styles.errorText}>Technical analysis unavailable</p>
              )}
            </div>

            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>📰 Sentiment Analysis</h3>
              {result.sentiment_analysis && !result.sentiment_analysis.error ? (
                <div style={styles.metrics}>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Sentiment:</span>
                    <span style={styles.metricValue}>{result.sentiment_analysis.sentiment}</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Confidence:</span>
                    <span style={styles.metricValue}>{Math.round(result.sentiment_analysis.confidence * 100)}%</span>
                  </div>
                  <div style={styles.metricFull}>
                    <span style={styles.metricLabel}>Rationale:</span>
                    <p style={styles.rationale}>{result.sentiment_analysis.rationale}</p>
                  </div>
                </div>
              ) : (
                <p style={styles.errorText}>Sentiment analysis unavailable</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  card: {
    maxWidth: '800px',
    margin: '0 auto',
    backgroundColor: 'white',
    borderRadius: '16px',
    padding: '40px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: '8px',
    color: '#1f2937',
  },
  subtitle: {
    textAlign: 'center',
    color: '#6b7280',
    marginBottom: '32px',
  },
  inputGroup: {
    display: 'flex',
    gap: '12px',
    marginBottom: '24px',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    fontSize: '16px',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    outline: 'none',
  },
  button: {
    padding: '12px 32px',
    fontSize: '16px',
    fontWeight: '600',
    color: 'white',
    backgroundColor: '#667eea',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  error: {
    padding: '16px',
    backgroundColor: '#fee2e2',
    color: '#991b1b',
    borderRadius: '8px',
    marginBottom: '16px',
  },
  results: {
    marginTop: '24px',
  },
  recommendation: {
    padding: '24px',
    borderRadius: '12px',
    textAlign: 'center',
    marginBottom: '24px',
    color: 'white',
  },
  recommendationText: {
    fontSize: '32px',
    fontWeight: 'bold',
    margin: '0 0 8px 0',
  },
  confidence: {
    fontSize: '18px',
    margin: 0,
    opacity: 0.9,
  },
  summary: {
    padding: '16px',
    backgroundColor: '#f3f4f6',
    borderRadius: '8px',
    marginBottom: '24px',
  },
  section: {
    marginBottom: '24px',
    padding: '20px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#1f2937',
  },
  metrics: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '12px',
  },
  metric: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px',
    backgroundColor: 'white',
    borderRadius: '6px',
  },
  metricFull: {
    gridColumn: '1 / -1',
    padding: '12px',
    backgroundColor: 'white',
    borderRadius: '6px',
  },
  metricLabel: {
    fontWeight: '600',
    color: '#6b7280',
  },
  metricValue: {
    fontWeight: '600',
    color: '#1f2937',
  },
  rationale: {
    marginTop: '8px',
    color: '#4b5563',
    lineHeight: '1.5',
  },
  errorText: {
    color: '#ef4444',
    fontStyle: 'italic',
  },
};
