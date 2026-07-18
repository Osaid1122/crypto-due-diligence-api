// Reuses the existing, already-deployed FastAPI backend — no backend changes
// needed. Auto-detects local dev vs. production the same way the previous
// vanilla frontend did.
const isLocal =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// TODO: replace with your actual Render URL once confirmed.
const PRODUCTION_API_BASE = 'https://YOUR-RENDER-APP.onrender.com';
export const API_BASE = isLocal ? 'http://127.0.0.1:8000' : PRODUCTION_API_BASE;

export async function fetchChains() {
  const res = await fetch(`${API_BASE}/chains`);
  if (!res.ok) throw new Error('Failed to load supported chains');
  return res.json();
}

export async function analyzeToken(chainId, address) {
  const res = await fetch(`${API_BASE}/analyze/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chain_id: chainId, address }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (HTTP ${res.status})`);
  }
  return res.json();
}

export const ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;
