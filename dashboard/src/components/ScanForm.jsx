import { useState } from 'react';

function ScanForm({ onScanComplete }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);

      const result = await response.json();
      onScanComplete(result);
    } catch (err) {
      setError(err.message || 'Scan failed. Is the API running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scan-form-container">
      <form className="scan-form" onSubmit={handleSubmit}>
        <div className="scan-input-wrapper">
          <svg className="scan-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M11.742 10.344a6.5 6.5 0 10-1.397 1.398h-.001l3.85 3.85a1 1 0 001.415-1.414l-3.85-3.85zm-5.242.156a5 5 0 110-10 5 5 0 010 10z"/>
          </svg>
          <input
            type="text"
            className="scan-input"
            placeholder="Enter a URL to analyze..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
        </div>
        <button type="submit" className="scan-btn" disabled={loading || !url.trim()}>
          {loading ? (
            <>
              <div className="spinner"></div>
              Analyzing...
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </form>
      {error && <div className="scan-error">{error}</div>}
    </div>
  );
}

export default ScanForm;
