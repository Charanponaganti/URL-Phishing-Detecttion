function RiskGauge({ score = 0, level = 'safe' }) {
  const radius = 62;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const colorMap = {
    safe: '#059669',
    suspicious: '#d97706',
    malicious: '#dc2626',
  };

  const labelMap = {
    safe: 'Low Risk',
    suspicious: 'Medium Risk',
    malicious: 'High Risk',
  };

  const color = colorMap[level] || colorMap.safe;

  return (
    <div className="risk-gauge-container">
      <div className="risk-gauge">
        <svg width="150" height="150" viewBox="0 0 150 150">
          <circle className="risk-gauge-bg" cx="75" cy="75" r={radius} />
          <circle
            className="risk-gauge-fill"
            cx="75" cy="75" r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="risk-gauge-center">
          <div className="risk-score-value" style={{ color }}>{score}</div>
          <div className="risk-score-label">{labelMap[level]}</div>
        </div>
      </div>
    </div>
  );
}

export default RiskGauge;
