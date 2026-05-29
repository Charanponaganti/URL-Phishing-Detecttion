/**
 * PhishGuard — Chrome Extension Background Service Worker
 * Monitors tab navigation and scans URLs via the PhishGuard API.
 */

const API_BASE = "http://localhost:8000";

// Badge colors for risk levels
const BADGE_COLORS = {
  safe: "#10b981",       // green
  suspicious: "#f59e0b", // amber
  malicious: "#ef4444",  // red
  error: "#6b7280",      // gray
  loading: "#3b82f6",    // blue
};

// Cache scan results to avoid re-scanning
const scanCache = new Map();

/**
 * Scan a URL through the PhishGuard API
 */
async function scanUrl(url) {
  // Skip internal/extension URLs
  if (!url || url.startsWith("chrome://") || url.startsWith("chrome-extension://") ||
      url.startsWith("about:") || url.startsWith("edge://")) {
    return null;
  }

  // Check cache first
  if (scanCache.has(url)) {
    const cached = scanCache.get(url);
    if (Date.now() - cached.timestamp < 300000) { // 5 min cache
      return cached.result;
    }
  }

  try {
    const response = await fetch(`${API_BASE}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);

    const result = await response.json();

    // Cache result
    scanCache.set(url, { result, timestamp: Date.now() });

    // Limit cache size
    if (scanCache.size > 100) {
      const oldest = scanCache.keys().next().value;
      scanCache.delete(oldest);
    }

    return result;
  } catch (error) {
    console.error("[PhishGuard] Scan error:", error);
    return null;
  }
}

/**
 * Update extension badge based on scan result
 */
function updateBadge(tabId, result) {
  if (!result) {
    chrome.action.setBadgeText({ text: "?", tabId });
    chrome.action.setBadgeBackgroundColor({ color: BADGE_COLORS.error, tabId });
    return;
  }

  const level = result.risk_level;
  const score = result.risk_score;

  let badgeText;
  if (level === "safe") badgeText = "✓";
  else if (level === "suspicious") badgeText = "!";
  else badgeText = "✕";

  chrome.action.setBadgeText({ text: badgeText, tabId });
  chrome.action.setBadgeBackgroundColor({
    color: BADGE_COLORS[level] || BADGE_COLORS.error,
    tabId,
  });
}

/**
 * Handle tab navigation — scan the new URL
 */
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
    // Show loading badge
    chrome.action.setBadgeText({ text: "...", tabId });
    chrome.action.setBadgeBackgroundColor({ color: BADGE_COLORS.loading, tabId });

    const result = await scanUrl(tab.url);
    updateBadge(tabId, result);

    // Store result for popup
    if (result) {
      chrome.storage.local.set({ [`scan_${tabId}`]: result });
    }
  }
});

// Listen for popup requests
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_SCAN") {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        const stored = await chrome.storage.local.get(`scan_${tabs[0].id}`);
        const result = stored[`scan_${tabs[0].id}`];
        if (result) {
          sendResponse(result);
        } else {
          // Scan on demand
          const fresh = await scanUrl(tabs[0].url);
          if (fresh) {
            chrome.storage.local.set({ [`scan_${tabs[0].id}`]: fresh });
          }
          sendResponse(fresh);
        }
      }
    });
    return true; // async response
  }

  if (message.type === "MANUAL_SCAN") {
    scanUrl(message.url).then((result) => sendResponse(result));
    return true;
  }
});
