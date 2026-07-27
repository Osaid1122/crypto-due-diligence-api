const EVM_NETWORKS = [
  ['ethereum', 'Ethereum', 1, 'https://etherscan.io/address/'],
  ['arbitrum', 'Arbitrum', 42161, 'https://arbiscan.io/address/'],
  ['optimism', 'Optimism', 10, 'https://optimistic.etherscan.io/address/'],
  ['base', 'Base', 8453, 'https://basescan.org/address/'],
  ['linea', 'Linea', 59144, 'https://lineascan.build/address/'],
  ['scroll', 'Scroll', 534352, 'https://scrollscan.com/address/'],
  ['zksync-era', 'zkSync Era', 324, 'https://explorer.zksync.io/address/'],
  ['bnb-chain', 'BNB Chain', 56, 'https://bscscan.com/address/'],
  ['opbnb', 'opBNB', 204, 'https://mainnet.opbnbscan.com/address/'],
  ['polygon', 'Polygon', 137, 'https://polygonscan.com/address/'],
  ['avalanche-c-chain', 'Avalanche C-Chain', 43114, 'https://snowtrace.io/address/'],
  ['cronos', 'Cronos', 25, 'https://explorer.cronos.org/address/'],
  ['mantle', 'Mantle', 5000, 'https://mantlescan.xyz/address/'],
  ['gnosis', 'Gnosis', 100, 'https://gnosisscan.io/address/'],
  ['xlayer', 'X Layer', 196, 'https://www.okx.com/web3/explorer/xlayer/address/'],
];

export const NETWORKS = Object.fromEntries([
  ...EVM_NETWORKS.map(([key, label, chainId, explorer]) => [key, {
    key, label, selectorLabel: key === 'ethereum' ? 'EVM' : undefined,
    family: 'EVM', chainType: 'evm', chainId, explorer, tokenSecurity: true,
  }]),
  ['solana', { key: 'solana', label: 'Solana', family: 'SVM / Solana', chainType: 'solana', chainId: null, explorer: 'https://solscan.io/token/', tokenSecurity: true }],
]);

export const NETWORK_LIST = [NETWORKS.ethereum, NETWORKS.xlayer, NETWORKS.solana];
export const EVM_NETWORK_LIST = EVM_NETWORKS.filter(([key]) => key !== 'xlayer').map(([key]) => NETWORKS[key]);
export const EVM_ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;
export const SOLANA_ADDRESS_RE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

export function getNetwork(key) { return NETWORKS[key] || NETWORKS.ethereum; }
export function isNetworkKey(key) { return Boolean(NETWORKS[key]); }
export function isEvmNetwork(key) { return getNetwork(key).chainType === 'evm'; }
export function isValidNetworkAddress(key, address) {
  return (getNetwork(key).chainType === 'solana' ? SOLANA_ADDRESS_RE : EVM_ADDRESS_RE).test(address.trim());
}
export function networkPlaceholder(key) {
  return getNetwork(key).chainType === 'solana' ? 'Paste Solana mint address…' : '0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48';
}
