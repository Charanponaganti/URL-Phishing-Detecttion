import { useState, useEffect } from 'react';

function ScanHistory({ refreshKey, onSelectScan }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, [refreshKey]);

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/history?limit=10');
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const formatTime = (ts) => {
    try {
      return new Date(ts).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  const riskColor = (score) => {
    if (score >= 70) return '#dc2626';
    if (score >= 40) return '#d97706';
    return '#059669';
  };

  if (history.length === 0) {
    return <p style={{ color: '#9ca3af', fontSize: '13px', padding: '16px 0' }}>No scans yet. Analyze a URL to get started.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="scan-table">
        <thead>
          <tr>
            <th>URL</th>
            <th>Score</th>
            <th>Level</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {history.map((item) => (
            <tr key={item.scan_id} onClick={() => onSelectScan && onSelectScan(item)} style={{ cursor: onSelectScan ? 'pointer' : 'default' }}>
              <td className="url-cell" title={item.url}>{item.url}</td>
              <td className="score-cell" style={{ color: riskColor(item.risk_score) }}>
                {item.risk_score}
              </td>
              <td><span className={`badge ${item.risk_level}`}>{item.risk_level}</span></td>
              <td className="time-cell">{formatTime(item.timestamp)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ScanHistory;
