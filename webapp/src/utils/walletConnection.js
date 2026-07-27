import { BrowserProvider, formatEther } from 'ethers';

const STORAGE_KEY = 'crypto-intelligence-wallet-connection';
const PROVIDER_TYPES = {
  metamask: 'MetaMask',
  rabby: 'Rabby',
  phantom: 'Phantom',
  walletconnect: 'WalletConnect',
};

export async function connectWallet(providerType = 'metamask') {
  if (typeof window === 'undefined' || !window.ethereum) {
    throw new Error('No browser wallet detected. Please install MetaMask, Rabby, or another compatible wallet.');
  }

  try {
    const provider = new BrowserProvider(window.ethereum);
    const accounts = await provider.send('eth_requestAccounts', []);
    const network = await provider.getNetwork();
    const balance = await provider.getBalance(accounts[0]);
    const connection = {
      providerType,
      account: accounts[0],
      chainId: Number(network.chainId),
      networkName: network.name || 'Unknown network',
      balance: formatEther(balance),
      label: PROVIDER_TYPES[providerType] || 'Wallet',
    };

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(connection));
    }
    return connection;
  } catch (error) {
    clearStoredWalletConnection();
    throw new Error(error?.message || 'Unable to connect wallet.');
  }
}

export async function disconnectWallet() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(STORAGE_KEY);
  }
  return { connected: false };
}

export function clearStoredWalletConnection() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function formatAddress(address) {
  if (!address) return '';
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}
