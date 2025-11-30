import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const API_URL = 'https://j0hz2ok0kb.execute-api.us-east-1.amazonaws.com/dev/analyze';

  // Calculate price domain with 10% buffer
  const getPriceDomain = (chartData) => {
    if (!chartData || chartData.length === 0) return ['auto', 'auto'];
    
    const prices = chartData.map(d => d.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const buffer = (maxPrice - minPrice) * 0.1;
    
    return [
      Math.floor(minPrice - buffer),
      Math.ceil(maxPrice + buffer)
    ];
  };

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
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.logo}>⚡ TERMINAL.AI</div>
        <div style={styles.searchBar}>
          <input
            type="text"
            placeholder="Search ticker..."
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && analyzeTicker()}
            style={styles.searchInput}
          />
          <button onClick={analyzeTicker} disabled={loading || !ticker} style={styles.searchButton}>
            {loading ? '...' : '→'}
          </button>
        </div>
      </div>

      {error && (
        <div style={styles.error}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.mainContent}>
          {/* Ticker Header */}
          <div style={styles.tickerHeader}>
            <div>
              <div style={styles.tickerSymbol}>{result.ticker}</div>
              <div style={styles.tickerPrice}>
                ${result.technical_analysis?.current_price?.toFixed(2)}
                <span style={{
                  ...styles.priceChange,
                  color: result.technical_analysis?.price_change_24h >= 0 ? '#00ff88' : '#ff4444'
                }}>
                  {result.technical_analysis?.price_change_24h >= 0 ? '+' : ''}
                  ${result.technical_analysis?.price_change_24h?.toFixed(2)} 
                  ({((result.technical_analysis?.price_change_24h / result.technical_analysis?.current_price) * 100).toFixed(2)}%)
                </span>
              </div>
            </div>
            <div style={styles.actionButtons}>
              <button style={{...styles.actionBtn, backgroundColor: '#00ff88', color: '#000'}}>BUY</button>
              <button style={{...styles.actionBtn, backgroundColor: '#ff4444'}}>SELL</button>
            </div>
          </div>

          {/* Charts */}
          {result.technical_analysis?.chart_data && result.technical_analysis.chart_data.length > 0 && (
            <div style={styles.chartContainer}>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={result.technical_analysis.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                  <XAxis 
                    dataKey="date" 
                    tick={{fontSize: 11, fill: '#666'}} 
                    stroke="#333"
                  />
                  <YAxis 
                    domain={getPriceDomain(result.technical_analysis.chart_data)}
                    tick={{fontSize: 11, fill: '#666'}}
                    stroke="#333"
                    orientation="right"
                  />
                  <Tooltip 
                    contentStyle={{backgroundColor: '#0a0a0a', border: '1px solid #333', borderRadius: '4px'}}
                    labelStyle={{color: '#00ff88'}}
                  />
                  <Line type="monotone" dataKey="price" stroke="#00ff88" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
              
              <ResponsiveContainer width="100%" height={150}>
                <LineChart data={result.technical_analysis.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                  <XAxis 
                    dataKey="date" 
                    tick={{fontSize: 10, fill: '#666'}} 
                    stroke="#333"
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis 
                    domain={[0, 100]} 
                    tick={{fontSize: 11, fill: '#666'}}
                    stroke="#333"
                    orientation="right"
                  />
                  <Tooltip 
                    contentStyle={{backgroundColor: '#0a0a0a', border: '1px solid #333', borderRadius: '4px'}}
                    labelStyle={{color: '#ffaa00'}}
                  />
                  <Line type="monotone" dataKey="rsi" stroke="#ffaa00" strokeWidth={2} dot={false} />
                  <ReferenceLine y={70} stroke="#ff4444" strokeDasharray="3 3" />
                  <ReferenceLine y={30} stroke="#00ff88" strokeDasharray="3 3" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Bottom Info Grid */}
          <div style={styles.infoGrid}>
            {/* Key Statistics */}
            <div style={styles.infoPanel}>
              <div style={styles.panelTitle}>KEY STATISTICS</div>
              <div style={styles.statRow}>
                <span style={styles.statLabel}>Open</span>
                <span style={styles.statValue}>${result.technical_analysis?.current_price?.toFixed(2)}</span>
              </div>
              <div style={styles.statRow}>
                <span style={styles.statLabel}>High</span>
                <span style={styles.statValue}>
                  ${Math.max(...(result.technical_analysis?.chart_data?.map(d => d.price) || [0])).toFixed(2)}
                </span>
              </div>
              <div style={styles.statRow}>
                <span style={styles.statLabel}>Low</span>
                <span style={styles.statValue}>
                  ${Math.min(...(result.technical_analysis?.chart_data?.map(d => d.price) || [0])).toFixed(2)}
                </span>
              </div>
              <div style={styles.statRow}>
                <span style={styles.statLabel}>RSI</span>
                <span style={styles.statValue}>{result.technical_analysis?.rsi?.toFixed(2)}</span>
              </div>
            </div>

            {/* Analyst Agent */}
            <div style={styles.infoPanel}>
              <div style={styles.panelTitle}>🤖 ANALYST AGENT</div>
              <div style={styles.agentBox}>
                <div style={styles.agentRecommendation}>
                  <span style={{
                    color: result.recommendation === 'BUY' ? '#00ff88' : result.recommendation === 'SELL' ? '#ff4444' : '#ffaa00',
                    fontWeight: 'bold',
                    fontSize: '18px'
                  }}>
                    {result.recommendation}
                  </span>
                  <span style={styles.confidence}>
                    {Math.round(result.confidence * 100)}% confidence
                  </span>
                </div>
                <div style={styles.agentSummary}>{result.summary}</div>
                <div style={styles.sentimentRow}>
                  <span style={styles.statLabel}>Sentiment:</span>
                  <span style={{
                    ...styles.statValue,
                    color: result.sentiment_analysis?.sentiment === 'Bullish' ? '#00ff88' : '#ff4444'
                  }}>
                    {result.sentiment_analysis?.sentiment || 'N/A'}
                  </span>
                </div>
                <div style={styles.sentimentRow}>
                  <span style={styles.statLabel}>Signal:</span>
                  <span style={styles.statValue}>{result.technical_analysis?.rsi_signal}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📊</div>
          <div style={styles.emptyText}>Enter a ticker symbol to analyze</div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#000000',
    color: '#ffffff',
    fontFamily: '"Courier New", monospace',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 24px',
    backgroundColor: '#0a0a0a',
    borderBottom: '1px solid #1a1a1a',
  },
  logo: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#ffaa00',
    letterSpacing: '2px',
  },
  searchBar: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  searchInput: {
    backgroundColor: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '4px',
    padding: '8px 16px',
    color: '#fff',
    fontSize: '14px',
    fontFamily: '"Courier New", monospace',
    outline: 'none',
    width: '200px',
  },
  searchButton: {
    backgroundColor: '#ffaa00',
    border: 'none',
    borderRadius: '4px',
    padding: '8px 16px',
    color: '#000',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontFamily: '"Courier New", monospace',
  },
  error: {
    margin: '20px',
    padding: '16px',
    backgroundColor: '#2a0000',
    border: '1px solid #ff4444',
    borderRadius: '4px',
    color: '#ff4444',
  },
  mainContent: {
    padding: '0',
  },
  tickerHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '24px',
    backgroundColor: '#0a0a0a',
    borderBottom: '1px solid #1a1a1a',
  },
  tickerSymbol: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: '8px',
  },
  tickerPrice: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#fff',
  },
  priceChange: {
    fontSize: '18px',
    marginLeft: '16px',
  },
  actionButtons: {
    display: 'flex',
    gap: '12px',
  },
  actionBtn: {
    padding: '12px 32px',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontFamily: '"Courier New", monospace',
    color: '#fff',
  },
  chartContainer: {
    backgroundColor: '#0a0a0a',
    padding: '20px',
    borderBottom: '1px solid #1a1a1a',
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 2fr',
    gap: '1px',
    backgroundColor: '#1a1a1a',
  },
  infoPanel: {
    backgroundColor: '#0a0a0a',
    padding: '20px',
  },
  panelTitle: {
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#ffaa00',
    marginBottom: '16px',
    letterSpacing: '1px',
  },
  statRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid #1a1a1a',
  },
  statLabel: {
    color: '#666',
    fontSize: '13px',
  },
  statValue: {
    color: '#fff',
    fontSize: '13px',
    fontWeight: 'bold',
  },
  agentBox: {
    backgroundColor: '#0f0f0f',
    padding: '16px',
    borderRadius: '4px',
    border: '1px solid #1a1a1a',
  },
  agentRecommendation: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
    paddingBottom: '12px',
    borderBottom: '1px solid #1a1a1a',
  },
  confidence: {
    color: '#666',
    fontSize: '12px',
  },
  agentSummary: {
    color: '#999',
    fontSize: '13px',
    lineHeight: '1.6',
    marginBottom: '16px',
  },
  sentimentRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '6px 0',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '60vh',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
    opacity: 0.3,
  },
  emptyText: {
    color: '#666',
    fontSize: '16px',
  },
};
