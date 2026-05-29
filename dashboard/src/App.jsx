import { useState } from 'react';
import './index.css';
import ScanForm from './components/ScanForm';
import ThreatReport from './components/ThreatReport';
import RiskGauge from './components/RiskGauge';
import RiskDistribution from './components/RiskDistribution';
import ScanHistory from './components/ScanHistory';
import ExportButton from './components/ExportButton';

function App() {
  const [scanResult, setScanResult] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleScanComplete = (result) => {
    setScanResult(result);
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="app-logo">
          <h1>PhishGuard</h1>
          <span className="subtitle">Analyst Dashboard</span>
        </div>

      </header>

      <main className="app-main">
        <ScanForm onScanComplete={handleScanComplete} />

        {scanResult && (
          <div>
            <div className={`summary-banner ${scanResult.risk_level}`}>
              {scanResult.summary}
            </div>

            <div className="content-grid">
              <div className="card">
                <div className="card-title">Risk Assessment</div>
                <RiskGauge score={scanResult.risk_score} level={scanResult.risk_level} />
              </div>

              <div className="card">
                <div className="card-title">Threat Intelligence</div>
                <ThreatReport data={scanResult} />
              </div>
            </div>
          </div>
        )}

        <div className="content-grid">
          <div className="card">
            <div className="card-title">
              <span>Overview</span>
              <ExportButton />
            </div>
            <RiskDistribution refreshKey={refreshKey} />
          </div>

          <div className="card">
            <div className="card-title">Recent Scans</div>
            <ScanHistory refreshKey={refreshKey} onSelectScan={setScanResult} />
          </div>
        </div>

        {!scanResult && (
          <div className="empty-state">
            <h3>No active scan</h3>
            <p>Enter a URL above to start analyzing</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
