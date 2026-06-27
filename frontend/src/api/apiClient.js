const _host = window.location.hostname;
// Detect if we are on a local LAN network (IPs or .local hostnames)
const _isLan = /^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/.test(_host) || _host.endsWith('.local');

// Dynamically connect to the backend on the same host (port 8000) for local LAN / Tailscale / Tunnels
const _isTunnel = _host.endsWith('loca.lt') || 
                  _host.endsWith('serveousercontent.com') || 
                  _host.endsWith('pinggy-free.link') || 
                  _host.endsWith('trycloudflare.com') ||
                  _host.endsWith('ts.net') ||
                  _host.includes('tunnel') ||
                  _host.includes('ngrok');

const _isFirebase = _host.endsWith('web.app') || _host.endsWith('firebaseapp.com');

// If accessed via LAN IP, use http on port 8000. If tunnel, use https. Otherwise fallback to https on the same host.
let DEFAULT_API_BASE = `https://${_host}/api`;
if (_isLan || _host === 'localhost' || _host === '127.0.0.1') {
  DEFAULT_API_BASE = `http://${_host}:8000/api`;
} else if (_host.includes('github.dev')) {
  const codespaceHost = _host.replace('-5173.', '-8000.').replace('-5173-port.', '-8000-port.');
  DEFAULT_API_BASE = `https://${codespaceHost}/api`;
}

// If accessed externally via here.now, default directly to the active, zero-warning secure Tailscale funnel!
// During testing, we allow this to be overridden by LAN settings or manual config.
if (_host.endsWith('here.now') && !_isLan && !_host.includes('localhost')) {
  DEFAULT_API_BASE = 'https://enrichmentcaps-mac-mini.tailf77f05.ts.net/api';
}

// Persistent server URL configuration for external network access
let API_BASE = localStorage.getItem('ccmed_api_base');

// Reset to default if the stored API base is empty, or if we are on localhost/127.0.0.1
// This ensures local testing always defaults to the correct local ports.
if (!API_BASE || _host === 'localhost' || _host === '127.0.0.1') {
  API_BASE = DEFAULT_API_BASE;
} else if (!API_BASE.startsWith('http://') && !API_BASE.startsWith('https://')) {
  // If the user typed it manually without protocol, default to https://
  API_BASE = 'https://' + API_BASE;
}
console.log("[CCMed] Active hostname:", _host);
console.log("[CCMed] Is tunnel connection:", _isTunnel);
console.log("[CCMed] API_BASE URL computed:", API_BASE);

const originalFetch = window.fetch;
window.fetch = async function () {
  let [resource, config] = arguments;
  if (typeof resource === 'string' && (
    resource.includes('loca.lt') || 
    resource.includes('serveousercontent.com') || 
    resource.includes('pinggy-free.link') || 
    resource.includes('trycloudflare.com') || 
    resource.includes('tunnel') || 
    resource.includes('ngrok')
  )) {
    if (!config) config = {};
    if (!config.headers) config.headers = {};
    config.headers['Bypass-Tunnel-Reminder'] = 'true';
    config.headers['ngrok-skip-browser-warning'] = 'true';
  }
  return originalFetch(resource, config);
};

export { API_BASE };
