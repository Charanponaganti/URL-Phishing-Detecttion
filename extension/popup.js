/**
 * PhishGuard — Extension Popup Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  const scanResult = document.getElementById("scan-result");
  const loading = document.getElementById("loading");
  const urlInput = document.getElementById("url-input");
  const scanBtn = document.getElementById("scan-btn");

  // Load current tab's scan result
  loadCurrentScan();

  // Manual scan
  scanBtn.addEventListener("click", () => manualScan());
  urlInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") manualScan();
  });

  async function loadCurrentScan() {
    try {
      chrome.runtime.sendMessage({ type: "GET_SCAN" }, (result) => {
        if (result) {
          renderResult(result);
        } else {
          renderError("Could not scan this page. Is the API running?");
        }
      });
    } catch (err) {
      renderError("Extension error. Please reload.");
    }
  }

  async function manualScan() {
    const url = urlInput.value.trim();
    if (!url) return;

    loading.style.display = "flex";
    scanResult.innerHTML = "";
    scanResult.appendChild(loading);

    chrome.runtime.sendMessage({ type: "MANUAL_SCAN", url }, (result) => {
      if (result) {
        renderResult(result);
      } else {
        renderError("Scan failed. Is the PhishGuard API running on localhost:8000?");
      }
    });
  }

  function renderResult(data) {
    const level = data.risk_level || "safe";
    const score = data.risk_score || 0;
    const ml = data.ml_prediction || {};
    const cti = data.cti_result || {};
    const obf = data.obfuscation || {};
    const typo = data.typosquatting || {};
    const dns = data.dns_whois || {};

    let levelLabel;
    if (level === "safe") levelLabel = "Safe";
    else if (level === "suspicious") levelLabel = "Suspicious";
    else levelLabel = "Malicious";

    // CTI status
    const vt = cti.virustotal || {};
    let vtText = "N/A";
    let vtClass = "neutral";
    if (vt.status === "found") {
      vtText = `${vt.malicious || 0} flags`;
      vtClass = vt.malicious > 0 ? "danger" : "safe";
    }

    const uh = cti.urlhaus || {};
    let uhText = "Clean";
    let uhClass = "safe";
    if (uh.status === "found") {
      uhText = "Threat Found";
      uhClass = "danger";
    } else if (uh.status === "clean") {
      uhText = "Clean";
      uhClass = "safe";
    }

    // Indicators
    let indicators = [];
    if (obf.techniques_detected && obf.techniques_detected.length > 0) {
      obf.techniques_detected.forEach((t) => {
        indicators.push({ text: t.replace(/_/g, " "), type: "warning" });
      });
    }
    if (typo.is_typosquatting) {
      indicators.push({ text: `Typosquat: ${typo.closest_match}`, type: "danger" });
    }
    if (dns.newly_registered) {
      indicators.push({ text: "New Domain", type: "warning" });
    }

    const indicatorsHtml = indicators.length > 0
      ? `<div class="indicators">${indicators.map(
          (i) => `<span class="indicator-tag ${i.type}">${i.text}</span>`
        ).join("")}</div>`
      : "";

    scanResult.innerHTML = `
      <div class="result-card">
        <div class="result-header">
          <div class="risk-badge ${level}">${score}</div>
          <div class="result-info">
            <h3>Risk Score: ${score}/100</h3>
            <div class="url-text">${escapeHtml(data.url || "")}</div>
            <div class="risk-label ${level}">${levelLabel}</div>
          </div>
        </div>
        <div class="details-grid">
          <div class="detail-item">
            <div class="label">ML Verdict</div>
            <div class="value ${ml.label === 'phishing' ? 'danger' : 'safe'}">
              ${ml.label || "N/A"} (${((ml.confidence || 0) * 100).toFixed(0)}%)
            </div>
          </div>
          <div class="detail-item">
            <div class="label">VirusTotal</div>
            <div class="value ${vtClass}">${vtText}</div>
          </div>
          <div class="detail-item">
            <div class="label">URLhaus</div>
            <div class="value ${uhClass}">${uhText}</div>
          </div>
          <div class="detail-item">
            <div class="label">Domain Age</div>
            <div class="value ${dns.newly_registered ? 'warning' : 'neutral'}">
              ${dns.domain_age_days != null ? dns.domain_age_days + 'd' : 'N/A'}
            </div>
          </div>
        </div>
        ${indicatorsHtml}
      </div>
    `;
  }

  function renderError(message) {
    scanResult.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚡</div>
        <p>${message}</p>
      </div>
    `;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
});
