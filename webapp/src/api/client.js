// Reuses the existing, already-deployed FastAPI backend — no backend changes
// needed. Auto-detects local dev vs. production the same way the previous
// vanilla frontend did.
const isBrowser = typeof window !== 'undefined';
const isLocal =
  isBrowser &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const envApiUrl = import.meta.env.VITE_API_URL;
import { getNetwork } from '../config/networks';
export const API_BASE = envApiUrl || (isLocal ? 'http://127.0.0.1:8000' : 'https://crypto-due-diligence-api.onrender.com');
export async function fetchChains() {
  const res = await fetch(`${API_BASE}/chains`);
  if (!res.ok) throw new Error('Failed to load supported chains');
  return res.json();
}

export async function analyzeToken(chainType, address) {
  const selectedNetwork = getNetwork(chainType);
  const network = selectedNetwork.chainType === 'solana' ? { chain_type: 'solana' } : { chain_type: 'evm', chain_id: selectedNetwork.chainId };
  const payload = network.chain_type === 'solana'
    ? { chain_type: 'solana', address }
    : { ...network, address };
  const res = await fetch(`${API_BASE}/analyze/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (HTTP ${res.status})`);
  }
  return res.json();
}

export async function analyzeWallet(address, chainType) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  const payload = chainType ? { address, chain_type: chainType } : { address };

  try {
    const res = await fetch(`${API_BASE}/analyze/wallet`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    const body = await res.json().catch(() => ({}));
    if (!res.ok || body?.status === 'error') {
      const message = body?.summary || body?.detail || body?.error?.message || `Request failed (HTTP ${res.status})`;
      throw new Error(message);
    }
    return body;
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('Wallet analysis timed out after 15 seconds. Please try again.');
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
