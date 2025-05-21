import React, { useState, useEffect } from 'react';
import './index.css'; 

function App() {
  const [documentText, setDocumentText] = useState('');
  const [userQuery, setUserQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiKeySetSuccess, setApiKeySetSuccess] = useState(false);
  const [online, setOnline] = useState(navigator.onLine); 


  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // API Key Submission Processing
  const handleSetApiKey = async () => {
    if (!apiKey.trim()) {
      setError("API Key cannot be empty.");
      return;
    }
    setLoading(true);
    setError('');
    setApiKeySetSuccess(false);

    try {
      const response = await fetch('/api/set-api-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_name: 'my_llm_key', key_value: apiKey }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      setApiKeySetSuccess(true);
      setTimeout(() => setApiKeySetSuccess(false), 3000); 
    } catch (e) {
      setError(`Failed to set API Key: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };


  const handleChatSubmit = async () => {
    if (!documentText.trim() || !userQuery.trim()) {
      setError("Please paste a document and enter a query.");
      return;
    }
    if (!online) {
      setError("No internet connection detected. Please check your network.");
      return;
    }

    setLoading(true);
    setError('');
    const currentQuery = userQuery;
    const currentDocument = documentText;
    setUserQuery(''); 

    // Optimism updates chat history to show user queries first
    const newChatHistory = [...chatHistory, { user_query: currentQuery, ai_response: null }];
    setChatHistory(newChatHistory);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_text: currentDocument,
          user_query: currentQuery,
          chat_history: newChatHistory.map(item => ({
            user_query: item.user_query,
            ai_response: item.ai_response
          })) 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Updating the AI response for the last chat
      setChatHistory(prevHistory => {
        const updatedHistory = [...prevHistory];
        updatedHistory[updatedHistory.length - 1].ai_response = data.response;
        return updatedHistory;
      });

    } catch (e) {
      setError(`Failed to get insights: ${e.message}`);
      setChatHistory(prevHistory => prevHistory.slice(0, prevHistory.length - 1));
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>AI Document Insight Extractor</h1>

      {!online && (
        <p className="status-message error-message">
          ⚠️ You are currently offline. Please check your internet connection.
        </p>
      )}

      {/* API Key Input Section */}
      <div className="api-key-section">
        <h3>API Key Setup (Optional)</h3>
        <p>If your LLM requires an API key, please enter it here. This key will be stored in memory for the session.</p>
        <label htmlFor="apiKeyInput">Your API Key:</label>
        <input
          id="apiKeyInput"
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter your API Key here..."
          disabled={loading}
        />
        <button onClick={handleSetApiKey} disabled={loading}>
          {loading && !apiKeySetSuccess ? 'Setting Key...' : 'Set API Key'}
        </button>
        {apiKeySetSuccess && <p className="status-message success-message">API Key set successfully!</p>}
        {error && !apiKeySetSuccess && <p className="status-message error-message">{error}</p>}
      </div>

      <div className="container">
        <div className="input-section">
          <h2>1. Paste Your Document</h2>
          <textarea
            placeholder="Paste your academic article, report, or any text document here (UTF-8 encoded)..."
            value={documentText}
            onChange={(e) => setDocumentText(e.target.value)}
            rows="10"
            disabled={loading}
          ></textarea>
        </div>

        <div className="input-section">
          <h2>2. Ask a Question</h2>
          <input
            type="text"
            placeholder="e.g., 'Summarize what dropout is and how it is used in deep learning' or 'Extract 3 key insights'"
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleChatSubmit();
            }}
            disabled={loading}
          />
          <button onClick={handleChatSubmit} disabled={loading}>
            {loading ? 'Processing...' : 'Get Insights / Ask AI'}
          </button>
        </div>

        {/* Error and loading status display */}
        {error && <p className="status-message error-message">{error}</p>}
        {loading && <p className="status-message loading-message">Processing your request...</p>}

        {/* Chat History */}
        <div className="output-section">
          <h2>3. Chat History</h2>
          <div className="chat-history">
            {chatHistory.length === 0 && !loading && !error && (
              <p className="status-message">Your conversation with the AI will appear here.</p>
            )}
            {chatHistory.map((message, index) => (
              <div key={index} className="message-pair">
                <div className="user-message"><strong>You:</strong> {message.user_query}</div>
                {message.ai_response ? (
                  <div className="ai-message"><strong>AI:</strong> {message.ai_response}</div>
                ) : (
                  <div className="ai-message loading-message">AI is thinking...</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;