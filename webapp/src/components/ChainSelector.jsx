import ChainLogo from './ChainLogo';
import './ChainSelector.css';
import { NETWORK_LIST, EVM_NETWORK_LIST, EVM_ADDRESS_RE, SOLANA_ADDRESS_RE, isEvmNetwork, isValidNetworkAddress, networkPlaceholder } from '../config/networks';

export { EVM_ADDRESS_RE, SOLANA_ADDRESS_RE };

export function isValidAddress(chainType, address) {
  return isValidNetworkAddress(chainType, address);
}

export function addressPlaceholder(chainType) {
  return networkPlaceholder(chainType);
}

export default function ChainSelector({ value = 'ethereum', onChange, className = '' }) {
  return (
    <div className={`chain-selector ${className}`} role="group" aria-label="Select blockchain">
      {NETWORK_LIST.map(({ key, label, selectorLabel }) => (
        <button
          key={key}
          type="button"
          className={`chain-selector-option ${(key === 'ethereum' ? isEvmNetwork(value) && value !== 'xlayer' : value === key) ? 'is-selected' : ''}`}
          onClick={() => onChange(key)}
          aria-pressed={value === key}
        >
          <ChainLogo chain={key} size={16} /> {selectorLabel || label}
        </button>
      ))}
      {isEvmNetwork(value) && value !== 'xlayer' && <select className="chain-selector-evm-network" value={value} onChange={(event) => onChange(event.target.value)} aria-label="Select EVM network">
        {EVM_NETWORK_LIST.map((network) => <option key={network.key} value={network.key}>{network.label}</option>)}
      </select>}
    </div>
  );
}
