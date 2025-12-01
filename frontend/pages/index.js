import { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function Home() {
  const [ticker, setTicker] = useState('AAPL');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [watchlistData, setWatchlistData] = useState([]);
  const [chatMessages, setChatMessages] = useState([
    { role: 'agent', content: 'Terminal.ai Analyst online. Market data stream active.\n\nTry asking:\n• "Analyze AAPL"\n• "Should I buy NVDA?"\n• "What\'s the sentiment on MSFT?"\n• "Compare AMZN and JPM"', timestamp: new Date() }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [showWatchlist, setShowWatchlist] = useState(true);
  const messagesEndRef = useRef(null);

  const API_URL = 'https://j0hz2ok0kb.execute-api.us-east-1.amazonaws.com/dev/analyze';
  const WATCHLIST = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'JPM'];

  const getPriceDomain = (chartData) => {
    if (!chartData || chartData.length === 0) return ['auto', 'auto'];
    const prices = chartData.map(d => d.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const buffer = (maxPrice - minPrice) * 0.1;
    return [Math.floor(minPrice - buffer), Math.ceil(maxPrice + buffer)];
  };

  const fetchWatchlistData = async () => {
    const promises = WATCHLIST.map(async (symbol) => {
      try {
        const response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            inputText: `Analyze ${symbol} stock with comprehensive analysis including technical and sentiment data`
          }),
        });
        const data = await response.json();
        return {
          symbol: data.ticker || symbol,
          name: symbol,
          price: data.technical_analysis?.current_price || 0,
          change: data.technical_analysis?.price_change_24h || 0,
          changePercent: ((data.technical_analysis?.price_change_24h / data.technical_analysis?.current_price) * 100) || 0,
        };
      } catch (err) {
        return { symbol, name: symbol, price: 0, change: 0, changePercent: 0 };
      }
    });
    
    const results = await Promise.all(promises);
    setWatchlistData(results);
  };

  const analyzeTicker = async (symbol) => {
    if (!symbol) return;
    
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputText: `Analyze ${symbol} stock with comprehensive analysis including technical and sentiment data`
        }),
      });

      const data = await response.json();
      if (data.ticker) {
        setResult(data);
        setTicker(symbol);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = { role: 'user', content: chatInput, timestamp: new Date() };
    const query = chatInput;
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      // Extract ticker from user query - skip common words
      const skipWords = ['SENTIMENT', 'FOR', 'THE', 'WHAT', 'IS', 'SHOULD', 'BUY', 'SELL', 'ANALYZE', 'ANALYSIS', 'STOCK', 'PRICE', 'RSI'];
      const words = query.toUpperCase().match(/\b([A-Z]{2,5})\b/g) || [];
      const extractedTicker = words.find(w => !skipWords.includes(w)) || ticker;
      
      // Always request full analysis to ensure technical data is included
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputText: `Analyze ${extractedTicker} stock with comprehensive analysis including technical and sentiment data`
        }),
      });

      const data = await response.json();
      
      // Format the response based on what the API returns
      let agentResponse = '';
      
      // Check if there was an error
      if (data.recommendation === 'ERROR' || (data.summary && data.summary.includes('failed'))) {
        // Use the extracted ticker for retry suggestion
        const suggestedTicker = extractedTicker || 'AAPL';
        
        agentResponse = `Analysis failed for "${query}".\n\n`;
        
        if (query.toLowerCase().includes('sentiment')) {
          agentResponse += `Sentiment-only queries require Alpha Vantage API.\n\n`;
          agentResponse += `Try a full analysis instead:\n`;
          agentResponse += `• "Analyze ${suggestedTicker}"\n`;
          agentResponse += `• "Should I buy ${suggestedTicker}?"\n\n`;
        } else {
          agentResponse += `Possible causes:\n`;
          agentResponse += `• Invalid ticker symbol\n`;
          agentResponse += `• Market data temporarily unavailable\n\n`;
          agentResponse += `Try: "Analyze ${suggestedTicker}"\n\n`;
        }
        agentResponse += `Or click a stock in the watchlist.`;
      } else if (data.ticker && data.technical_analysis?.current_price) {
        // If it's a successful stock analysis
        agentResponse = `Analysis for ${data.ticker}:\n\n`;
        agentResponse += `Price: $${data.technical_analysis.current_price.toFixed(2)}\n`;
        agentResponse += `RSI: ${data.technical_analysis.rsi.toFixed(2)} (${data.technical_analysis.rsi_signal})\n`;
        agentResponse += `24h Change: ${data.technical_analysis.price_change_24h >= 0 ? '+' : ''}$${data.technical_analysis.price_change_24h.toFixed(2)}\n\n`;
        agentResponse += `Recommendation: ${data.recommendation} (${Math.round(data.confidence * 100)}% confidence)\n\n`;
        agentResponse += `Sentiment: ${data.sentiment_analysis?.sentiment || 'N/A'}\n\n`;
        agentResponse += `${data.summary}`;
      } else if (data.summary) {
        // If it's a general query response
        agentResponse = data.summary;
      } else {
        agentResponse = 'Analysis complete. Please check the main display for detailed information.';
      }

      const agentMessage = {
        role: 'agent',
        content: agentResponse,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, agentMessage]);
    } catch (err) {
      const errorMessage = {
        role: 'agent',
        content: `Error: Unable to process your request. ${err.message}`,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  useEffect(() => {
    analyzeTicker('AAPL');
    fetchWatchlistData();
    
    // Refresh watchlist every 30 seconds
    const interval = setInterval(fetchWatchlistData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>⚡ TERMINAL.AI</div>
        </div>
        <div style={styles.headerCenter}>
          <span style={styles.marketStatus}>
            <span style={styles.statusDot}></span>
            MARKET OPEN
          </span>
          <span style={styles.divider}>|</span>
          <span style={styles.time}>{new Date().toLocaleTimeString()}</span>
          <span style={styles.divider}>|</span>
          <span style={styles.location}>NYC</span>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.userAvatar}>JD</div>
        </div>
      </header>

      {/* Ticker Tape */}
      <div style={styles.tickerTape}>
        <div style={styles.tickerContent}>
          {watchlistData.length > 0 && [...watchlistData, ...watchlistData, ...watchlistData].map((stock, idx) => (
            <div key={idx} style={styles.tickerItem}>
              <span style={styles.tickerSymbol}>{stock.symbol}</span>
              <span style={{...styles.tickerPrice, color: stock.change >= 0 ? '#00ff88' : '#ff4444'}}>
                {stock.price.toFixed(2)}
              </span>
              <span style={{...styles.tickerChange, color: stock.changePercent >= 0 ? '#00ff88' : '#ff4444'}}>
                {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main style={styles.mainContent}>
        {/* Left Sidebar: Watchlist */}
        {showWatchlist && (
          <aside style={styles.watchlistSidebar}>
            <div style={styles.watchlistHeader}>
              <span style={styles.watchlistTitle}>WATCHLIST</span>
            </div>
            <div style={styles.watchlistContent}>
              {watchlistData.map((stock) => (
                <div
                  key={stock.symbol}
                  onClick={() => analyzeTicker(stock.symbol)}
                  style={{
                    ...styles.watchlistItem,
                    ...(ticker === stock.symbol ? styles.watchlistItemActive : {})
                  }}
                >
                  <div style={styles.watchlistItemTop}>
                    <span style={styles.watchlistSymbol}>{stock.symbol}</span>
                    <span style={{
                      ...styles.watchlistPrice,
                      color: stock.change >= 0 ? '#00ff88' : '#ff4444'
                    }}>
                      {stock.price.toFixed(2)}
                    </span>
                  </div>
                  <div style={styles.watchlistItemBottom}>
                    <span style={styles.watchlistName}>{stock.name}</span>
                    <span style={{
                      ...styles.watchlistChange,
                      color: stock.changePercent >= 0 ? '#00ff88' : '#ff4444'
                    }}>
                      {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        )}

        {/* Toggle Button */}
        <button
          onClick={() => setShowWatchlist(!showWatchlist)}
          style={styles.toggleButton}
          title={showWatchlist ? 'Hide Watchlist' : 'Show Watchlist'}
        >
          {showWatchlist ? '◀' : '▶'}
        </button>

        {/* Center: Chart Area */}
        <section style={styles.centerSection}>
          {result && (
            <>
              {/* Stock Header */}
              <div style={styles.stockHeader}>
                <div>
                  <div style={styles.stockTitle}>
                    <h2 style={styles.stockSymbol}>{result.ticker}</h2>
                    <input
                      type="text"
                      placeholder="Search ticker..."
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          analyzeTicker(e.target.value.toUpperCase());
                        }
                      }}
                      style={styles.searchInput}
                    />
                  </div>
                  <div style={styles.priceInfo}>
                    <span style={styles.currentPrice}>
                      ${result.technical_analysis?.current_price?.toFixed(2)}
                    </span>
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
                <div style={styles.chartArea}>
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={result.technical_analysis.chart_data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                      <XAxis dataKey="date" tick={{fontSize: 11, fill: '#666'}} stroke="#333" />
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

              {/* Bottom Info Panels */}
              <div style={styles.bottomPanels}>
                <div style={styles.infoPanel}>
                  <h3 style={styles.panelTitle}>KEY STATISTICS</h3>
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

                <div style={styles.infoPanel}>
                  <h3 style={styles.panelTitle}>RECOMMENDATION</h3>
                  <div style={styles.recommendationBox}>
                    <div style={styles.recHeader}>
                      <span style={{
                        color: result.recommendation === 'BUY' ? '#00ff88' : result.recommendation === 'SELL' ? '#ff4444' : '#ffaa00',
                        fontWeight: 'bold',
                        fontSize: '18px'
                      }}>
                        {result.recommendation}
                      </span>
                      <span style={styles.confidence}>{Math.round(result.confidence * 100)}% confidence</span>
                    </div>
                    <div style={styles.summary}>{result.summary}</div>
                  </div>
                </div>

                <div style={styles.infoPanel}>
                  <h3 style={styles.panelTitle}>SENTIMENT</h3>
                  <div style={styles.statRow}>
                    <span style={styles.statLabel}>Sentiment:</span>
                    <span style={{
                      ...styles.statValue,
                      color: result.sentiment_analysis?.sentiment === 'Bullish' ? '#00ff88' : '#ff4444'
                    }}>
                      {result.sentiment_analysis?.sentiment || 'N/A'}
                    </span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statLabel}>Signal:</span>
                    <span style={styles.statValue}>{result.technical_analysis?.rsi_signal}</span>
                  </div>
                  <div style={{...styles.statRow, flexDirection: 'column', alignItems: 'flex-start'}}>
                    <span style={styles.statLabel}>Rationale:</span>
                    <p style={styles.rationale}>{result.sentiment_analysis?.rationale}</p>
                  </div>
                </div>
              </div>
            </>
          )}

          {loading && (
            <div style={styles.loadingState}>
              <div style={styles.loader}></div>
              <div>Analyzing {ticker}...</div>
            </div>
          )}
        </section>

        {/* Right Sidebar: Chat */}
        <aside style={styles.chatSidebar}>
          <div style={styles.chatHeader}>
            <div style={styles.chatHeaderLeft}>
              <span style={styles.statusDotSmall}></span>
              <h2 style={styles.chatTitle}>ANALYST AGENT</h2>
            </div>
            <div style={styles.chatVersion}>v2.5-FLASH</div>
          </div>

          <div style={styles.chatMessages}>
            {chatMessages.map((msg, idx) => (
              <div key={idx} style={{
                ...styles.chatMessage,
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div style={{
                  ...styles.messageContent,
                  backgroundColor: msg.role === 'user' ? '#1a1a1a' : '#0f0f0f',
                  borderColor: msg.role === 'user' ? '#333' : '#ffaa00'
                }}>
                  <div style={styles.messageHeader}>
                    <span>{msg.role === 'user' ? 'TRADER' : 'SYSTEM'}</span>
                    <span>{msg.timestamp.toLocaleTimeString()}</span>
                  </div>
                  <div style={styles.messageText}>{msg.content}</div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div style={styles.chatInput}>
            <form onSubmit={handleChatSubmit} style={styles.chatForm}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Query market data or ask for analysis..."
                style={styles.chatInputField}
                disabled={chatLoading}
              />
              <button 
                type="submit" 
                style={{
                  ...styles.chatSendBtn,
                  ...(chatLoading ? styles.chatSendBtnDisabled : {})
                }}
                disabled={chatLoading}
              >
                {chatLoading ? '...' : '→'}
              </button>
            </form>
          </div>
        </aside>
      </main>
    </div>
  );
}

const styles = {
  container: {
    height: '100vh',
    width: '100vw',
    backgroundColor: '#000',
    color: '#fff',
    fontFamily: '"Courier New", monospace',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    height: '48px',
    backgroundColor: '#0a0a0a',
    borderBottom: '1px solid #1a1a1a',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0 16px',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
  },
  logo: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#ffaa00',
    letterSpacing: '2px',
  },
  headerCenter: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    fontSize: '12px',
  },
  marketStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: '#00ff88',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#00ff88',
    animation: 'pulse 2s infinite',
  },
  divider: {
    color: '#666',
  },
  time: {
    color: '#fff',
  },
  location: {
    color: '#ffaa00',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  userAvatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#ffaa00',
    color: '#000',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '12px',
  },
  tickerTape: {
    height: '40px',
    backgroundColor: '#0a0a0a',
    borderBottom: '1px solid #1a1a1a',
    overflow: 'hidden',
    position: 'relative',
  },
  tickerContent: {
    display: 'flex',
    animation: 'scroll 30s linear infinite',
    whiteSpace: 'nowrap',
  },
  tickerItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '0 20px',
    borderRight: '1px solid #1a1a1a',
    height: '40px',
  },
  tickerSymbol: {
    fontWeight: 'bold',
    color: '#ffaa00',
    fontSize: '14px',
  },
  tickerPrice: {
    fontSize: '14px',
    fontWeight: 'bold',
  },
  tickerChange: {
    fontSize: '13px',
  },
  watchlistSidebar: {
    width: '240px',
    backgroundColor: '#0a0a0a',
    borderRight: '1px solid #1a1a1a',
    display: 'flex',
    flexDirection: 'column',
  },
  watchlistHeader: {
    padding: '12px',
    borderBottom: '1px solid #1a1a1a',
    backgroundColor: '#000',
  },
  watchlistTitle: {
    fontSize: '11px',
    fontWeight: 'bold',
    color: '#666',
    letterSpacing: '1px',
  },
  watchlistContent: {
    flex: 1,
    overflowY: 'auto',
  },
  watchlistItem: {
    padding: '12px',
    borderBottom: '1px solid #1a1a1a',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  watchlistItemActive: {
    backgroundColor: '#1a1a1a',
    borderLeft: '2px solid #ffaa00',
  },
  watchlistItemTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  watchlistSymbol: {
    fontWeight: 'bold',
    fontSize: '13px',
    color: '#fff',
  },
  watchlistPrice: {
    fontSize: '12px',
    fontWeight: 'bold',
  },
  watchlistItemBottom: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '11px',
  },
  watchlistName: {
    color: '#666',
    maxWidth: '120px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  watchlistChange: {
    fontSize: '11px',
  },
  toggleButton: {
    width: '24px',
    backgroundColor: '#0a0a0a',
    border: 'none',
    borderRight: '1px solid #1a1a1a',
    color: '#ffaa00',
    fontSize: '16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
    fontFamily: '"Courier New", monospace',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  },
  centerSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#000',
    overflow: 'auto',
  },
  stockHeader: {
    height: '80px',
    borderBottom: '1px solid #1a1a1a',
    padding: '16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#0a0a0a',
  },
  stockTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '8px',
  },
  stockSymbol: {
    fontSize: '24px',
    fontWeight: 'bold',
    margin: 0,
  },
  searchInput: {
    backgroundColor: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '4px',
    padding: '6px 12px',
    color: '#fff',
    fontSize: '12px',
    fontFamily: '"Courier New", monospace',
    outline: 'none',
  },
  priceInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  currentPrice: {
    fontSize: '20px',
    fontWeight: 'bold',
  },
  priceChange: {
    fontSize: '14px',
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
  chartArea: {
    flex: 1,
    padding: '16px',
    backgroundColor: '#0a0a0a',
  },
  bottomPanels: {
    height: '200px',
    borderTop: '1px solid #1a1a1a',
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr',
    gap: '1px',
    backgroundColor: '#1a1a1a',
  },
  infoPanel: {
    backgroundColor: '#0a0a0a',
    padding: '16px',
  },
  panelTitle: {
    fontSize: '11px',
    fontWeight: 'bold',
    color: '#ffaa00',
    marginBottom: '12px',
    letterSpacing: '1px',
  },
  statRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '6px 0',
    borderBottom: '1px solid #1a1a1a',
    fontSize: '12px',
  },
  statLabel: {
    color: '#666',
  },
  statValue: {
    color: '#fff',
    fontWeight: 'bold',
  },
  recommendationBox: {
    backgroundColor: '#0f0f0f',
    padding: '12px',
    borderRadius: '4px',
    border: '1px solid #1a1a1a',
  },
  recHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
    paddingBottom: '8px',
    borderBottom: '1px solid #1a1a1a',
  },
  confidence: {
    color: '#666',
    fontSize: '11px',
  },
  summary: {
    color: '#999',
    fontSize: '11px',
    lineHeight: '1.6',
  },
  rationale: {
    color: '#999',
    fontSize: '11px',
    lineHeight: '1.4',
    marginTop: '4px',
  },
  chatSidebar: {
    width: '320px',
    borderLeft: '1px solid #1a1a1a',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#0a0a0a',
  },
  chatHeader: {
    padding: '12px',
    borderBottom: '1px solid #1a1a1a',
    backgroundColor: '#000',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  chatHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusDotSmall: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: '#00ff88',
    animation: 'pulse 2s infinite',
  },
  chatTitle: {
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#ffaa00',
    letterSpacing: '1px',
    margin: 0,
  },
  chatVersion: {
    fontSize: '10px',
    color: '#666',
  },
  chatMessages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  chatMessage: {
    display: 'flex',
    maxWidth: '85%',
  },
  messageContent: {
    borderRadius: '4px',
    padding: '12px',
    border: '1px solid',
  },
  messageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '9px',
    color: '#666',
    marginBottom: '6px',
    textTransform: 'uppercase',
  },
  messageText: {
    fontSize: '12px',
    lineHeight: '1.5',
    color: '#fff',
  },
  chatInput: {
    padding: '12px',
    borderTop: '1px solid #1a1a1a',
    backgroundColor: '#000',
  },
  chatForm: {
    display: 'flex',
    gap: '8px',
  },
  chatInputField: {
    flex: 1,
    backgroundColor: '#0a0a0a',
    border: '1px solid #333',
    borderRadius: '4px',
    padding: '8px',
    color: '#fff',
    fontSize: '12px',
    fontFamily: '"Courier New", monospace',
    outline: 'none',
  },
  chatSendBtn: {
    backgroundColor: '#ffaa00',
    border: 'none',
    borderRadius: '4px',
    padding: '8px 16px',
    color: '#000',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  chatSendBtnDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  loadingState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
    color: '#666',
  },
  loader: {
    width: '40px',
    height: '40px',
    border: '3px solid #1a1a1a',
    borderTop: '3px solid #ffaa00',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
};
