import { useState } from 'react';

function ExportButton() {
  const [exporting, setExporting] = useState(false);

  const handleExport = async (format) => {
    setExporting(true);
    try {
      const response = await fetch(`http://localhost:8000/api/report/export?format=${format}`);
      if (!response.ok) throw new Error('Export failed');
      const data = await response.json();

      const blob = new Blob(
        [format === 'json' ? JSON.stringify(data.data, null, 2) : convertToCSV(data.data)],
        { type: format === 'json' ? 'application/json' : 'text/csv' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `phishguard_report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
    } finally {
      setExporting(false);
    }
  };

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map((row) =>
      Object.values(row).map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')
    );
    return [headers, ...rows].join('\n');
  };

  return (
    <div style={{ display: 'flex', gap: '6px' }}>
      <button className="export-btn" onClick={() => handleExport('json')} disabled={exporting}>
        JSON
      </button>
      <button className="export-btn" onClick={() => handleExport('csv')} disabled={exporting}>
        CSV
      </button>
    </div>
  );
}

export default ExportButton;
