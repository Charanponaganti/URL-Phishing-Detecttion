import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function RiskDistribution({ refreshKey }) {
  const [stats, setStats] = useState(null);
  const [chartType, setChartType] = useState('bar');

  useEffect(() => {
    fetchStats();
  }, [refreshKey]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/history/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  if (!stats) {
    return (
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Scans</div>
          <div className="stat-value blue">--</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Safe</div>
          <div className="stat-value green">--</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Suspicious</div>
          <div className="stat-value amber">--</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Malicious</div>
          <div className="stat-value red">--</div>
        </div>
      </div>
    );
  }

  const barData = [
    { name: 'Legitimate', count: stats.legitimate_count, fill: '#059669' },
    { name: 'Suspicious', count: stats.suspicious_count, fill: '#d97706' },
    { name: 'Phishing', count: stats.phishing_count, fill: '#dc2626' },
  ];

  const pieData = [
    { name: 'Legitimate', value: stats.legitimate_count },
    { name: 'Suspicious', value: stats.suspicious_count },
    { name: 'Phishing', value: stats.phishing_count },
  ];

  const COLORS = ['#059669', '#d97706', '#dc2626'];

  const tooltipStyle = {
    background: '#fff',
    border: '1px solid #e2e5ea',
    borderRadius: '6px',
    color: '#1a1d23',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  };

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Scans</div>
          <div className="stat-value blue">{stats.total_scans}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Safe</div>
          <div className="stat-value green">{stats.legitimate_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Suspicious</div>
          <div className="stat-value amber">{stats.suspicious_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Malicious</div>
          <div className="stat-value red">{stats.phishing_count}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px' }}>
        <button className={`export-btn ${chartType === 'bar' ? 'active' : ''}`} onClick={() => setChartType('bar')}>
          Bar Chart
        </button>
        <button className={`export-btn ${chartType === 'pie' ? 'active' : ''}`} onClick={() => setChartType('pie')}>
          Pie Chart
        </button>
      </div>

      {chartType === 'bar' ? (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: '#e5e7eb' }} tickLine={false} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: '#e5e7eb' }} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {barData.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={2} dataKey="value" stroke="#fff" strokeWidth={2}>
              {pieData.map((entry, index) => (
                <Cell key={index} fill={COLORS[index]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: '#6b7280', fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export default RiskDistribution;
