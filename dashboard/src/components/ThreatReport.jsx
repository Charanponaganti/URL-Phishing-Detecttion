function ThreatReport({ data }) {
  if (!data) return null;

  const ml = data.ml_prediction || {};
  const cti = data.cti_result || {};
  const dns = data.dns_whois || {};
  const obf = data.obfuscation || {};
  const typo = data.typosquatting || {};

  const vtData = cti.virustotal || {};
  const uhData = cti.urlhaus || {};

  return (
    <div className="threat-report">
      {/* ML Section */}
      <div className="threat-section">
        <div className="threat-section-title">ML Classification</div>
        <div className="threat-detail">
          <span className="label">Verdict</span>
          <span className={`value ${ml.label === 'phishing' ? 'malicious' : 'safe'}`}>
            {ml.label || 'N/A'}
          </span>
        </div>
        <div className="threat-detail">
          <span className="label">Confidence</span>
          <span className="value neutral">{ml.confidence ? `${(ml.confidence * 100).toFixed(1)}%` : 'N/A'}</span>
        </div>
      </div>

      {/* CTI Section */}
      <div className="threat-section">
        <div className="threat-section-title">Threat Intelligence</div>
        <div className="threat-detail">
          <span className="label">VirusTotal</span>
          <span className={`value ${vtData.malicious > 0 ? 'malicious' : vtData.status === 'found' ? 'safe' : 'neutral'}`}>
            {vtData.status === 'found'
              ? `${vtData.malicious || 0} / ${(vtData.malicious || 0) + (vtData.harmless || 0)} engines`
              : vtData.status || 'N/A'}
          </span>
        </div>
        <div className="threat-detail">
          <span className="label">URLhaus</span>
          <span className={`value ${uhData.status === 'found' ? 'malicious' : 'safe'}`}>
            {uhData.status === 'found' ? `Threat: ${uhData.threat || 'malware'}` : uhData.status || 'Clean'}
          </span>
        </div>
      </div>

      {/* DNS/WHOIS Section */}
      <div className="threat-section">
        <div className="threat-section-title">Domain Intelligence</div>
        <div className="threat-detail">
          <span className="label">Domain Age</span>
          <span className={`value ${dns.newly_registered ? 'suspicious' : 'neutral'}`}>
            {dns.domain_age_days != null ? `${dns.domain_age_days} days` : 'Unknown'}
          </span>
        </div>
        <div className="threat-detail">
          <span className="label">Registrar</span>
          <span className="value neutral">{dns.registrar || 'Unknown'}</span>
        </div>
        <div className="threat-detail">
          <span className="label">Newly Registered</span>
          <span className={`value ${dns.newly_registered ? 'suspicious' : 'safe'}`}>
            {dns.newly_registered ? 'Yes' : 'No'}
          </span>
        </div>
      </div>

      {/* Obfuscation & Typosquatting */}
      {(obf.techniques_detected?.length > 0 || typo.is_typosquatting) && (
        <div className="threat-section">
          <div className="threat-section-title">Evasion Techniques</div>
          {obf.techniques_detected?.map((tech, i) => (
            <div key={i} className="threat-detail">
              <span className="label">{tech.replace(/_/g, ' ')}</span>
              <span className="value suspicious">Detected</span>
            </div>
          ))}
          {typo.is_typosquatting && (
            <div className="threat-detail">
              <span className="label">Typosquatting target</span>
              <span className="value malicious">
                {typo.closest_match}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ThreatReport;
