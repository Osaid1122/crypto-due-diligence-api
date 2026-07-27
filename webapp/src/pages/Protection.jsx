import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, BadgeCheck, BarChart3, CheckCircle2, Compass, Droplets, ExternalLink, FileText, Globe2, HelpCircle, ListChecks, RotateCw, SearchCheck, ShieldCheck, ShieldAlert, ShieldQuestion, ShieldX, Sparkles, Users } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import ActionPriorityBadge from '../components/protection/ActionPriorityBadge';
import {
  getOverallRecommendation, getImmediateActions,
  getBeforeInvestingChecklist, getMonitoringChecklist, getGoodSigns,
} from '../components/protection/recommendationLogic';
import { analyzeToken } from '../api/client';
import ChainSelector, { addressPlaceholder, isValidAddress } from '../components/ChainSelector';
import { getNetwork, isNetworkKey } from '../config/networks';
import './Protection.css';
import './ProtectionPolish.css';

const LOADING_MESSAGES = [
  'Retrieving security data…',
  'Calculating deterministic score…',
  'Deriving recommendations…',
];

const BANNER_ICONS = {
  proceed: ShieldCheck,
  caution: ShieldQuestion,
  'high-risk': ShieldAlert,
  avoid: ShieldX,
};

function actionResources(chain, address, text) {
  const explorer = `${getNetwork(chain).explorer}${address}`;
  const market = `https://dexscreener.com/${chain === 'solana' ? 'solana' : chain === 'xlayer' ? 'x-layer' : 'ethereum'}/${address}`;
  const lower = text.toLowerCase();
  if (lower.includes('liquidity')) return [{ label: 'Review liquidity', href: market }, { label: 'Verify on explorer', href: explorer }];
  if (lower.includes('holder') || lower.includes('whale') || lower.includes('distribution')) return [{ label: 'View holder activity', href: explorer }, { label: 'Open market data', href: market }];
  if (lower.includes('source')) return [{ label: 'Read contract source', href: explorer }];
  if (lower.includes('address') || lower.includes('explorer')) return [{ label: 'Verify contract address', href: explorer }];
  return [{ label: 'Open contract explorer', href: explorer }];
}

function verificationResources(chain, address) {
  if (chain === 'solana') return [
    { label: 'Open Solscan', href: `https://solscan.io/token/${address}` },
    { label: 'Open Birdeye', href: `https://birdeye.so/token/${address}?chain=solana` },
    { label: 'Open SolanaFM', href: `https://solana.fm/address/${address}` },
    { label: 'Open DexScreener', href: `https://dexscreener.com/solana/${address}` },
  ];
  if (chain === 'xlayer') return [
    { label: 'Open X Layer Explorer', href: `https://www.okx.com/web3/explorer/xlayer/address/${address}` },
    { label: 'Open DexScreener', href: `https://dexscreener.com/x-layer/${address}` },
  ];
  if (chain !== 'ethereum') return [
    { label: `Open ${getNetwork(chain).label} explorer`, href: `${getNetwork(chain).explorer}${address}` },
  ];
  return [
    { label: 'Open Etherscan', href: `https://etherscan.io/address/${address}` },
    { label: 'Open DexScreener', href: `https://dexscreener.com/ethereum/${address}` },
    { label: 'Open GeckoTerminal', href: `https://www.geckoterminal.com/eth/pools?token_address=${address}` },
    { label: 'Open DEXTools', href: `https://www.dextools.io/app/en/ether/pair-explorer/${address}` },
  ];
}

function checklistPresentation(text) {
  const lower = text.toLowerCase();
  if (lower.includes('source') || lower.includes('audit')) return { icon: FileText, description: 'Review the verified code or a trusted audit before committing capital.' };
  if (lower.includes('address') || lower.includes('official')) return { icon: Globe2, description: 'Confirm this is the official token contract before interacting.' };
  if (lower.includes('explorer')) return { icon: SearchCheck, description: 'Independently cross-check the on-chain contract record.' };
  if (lower.includes('liquidity')) return { icon: Droplets, description: 'Check pool depth and lock status using market data.' };
  if (lower.includes('distribution')) return { icon: BarChart3, description: 'Watch how token supply is distributed across wallets.' };
  if (lower.includes('holder') || lower.includes('whale')) return { icon: Users, description: 'Track large wallet movements before making a decision.' };
  return { icon: ShieldCheck, description: 'Complete this protection step before interacting with the token.' };
}

function resourceDescription(label) {
  if (label.includes('Solscan') || label.includes('Etherscan')) return 'Official blockchain explorer';
  if (label.includes('Birdeye')) return 'Token and wallet analytics';
  if (label.includes('DexScreener')) return 'Trading and liquidity data';
  if (label.includes('Gecko')) return 'DEX market intelligence';
  if (label.includes('DEXTools')) return 'Token pair explorer';
  if (label.includes('SolanaFM')) return 'Solana transaction explorer';
  return 'External verification tool';
}

function resourceIcon(label) {
  if (label.includes('Solscan') || label.includes('Etherscan') || label.includes('SolanaFM')) return Globe2;
  if (label.includes('Birdeye')) return BarChart3;
  if (label.includes('DexScreener')) return Droplets;
  if (label.includes('Gecko') || label.includes('DEXTools')) return Compass;
  return Globe2;
}

function fadeStyle(delay) {
  return { animationDelay: `${delay}ms` };
}

export default function Protection() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [chainType, setChainType] = useState(isNetworkKey(searchParams.get('chain_type')) ? searchParams.get('chain_type') : 'ethereum');
  const [addressInput, setAddressInput] = useState(searchParams.get('address') || '');
  const [status, setStatus] = useState('idle');
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (status !== 'loading') return;
    setLoadingMsgIndex(0);
    const interval = setInterval(() => setLoadingMsgIndex(i => (i + 1) % LOADING_MESSAGES.length), 900);
    return () => clearInterval(interval);
  }, [status]);

  const runAnalysis = useCallback(async (chain, address) => {
    if (!isValidAddress(chain, address)) {
      setStatus('error');
      setErrorMsg(chain === 'solana' ? 'Invalid Solana mint address.' : `Invalid ${getNetwork(chain).label} address.`);
      return;
    }
    setStatus('loading');
    setErrorMsg('');
    try {
      const data = await analyzeToken(chain, address);
      setResult(data);
      setStatus('success');
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'Unable to analyze this contract.');
    }
  }, []);

  useEffect(() => {
    const chain = isNetworkKey(searchParams.get('chain_type')) ? searchParams.get('chain_type') : 'ethereum';
    const address = searchParams.get('address');
    if (address && isValidAddress(chain, address)) runAnalysis(chain, address);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    setSearchParams({ chain_type: chainType, address: addressInput.trim() });
    runAnalysis(chainType, addressInput.trim());
  }

  const overall = result ? getOverallRecommendation(result.risk_score) : null;
  const BannerIcon = overall ? BANNER_ICONS[overall.level] : null;
  const goodSigns = result ? getGoodSigns(result) : [];
  const address = addressInput.trim();
  const checklist = result ? [
    ...getBeforeInvestingChecklist(result),
    ...getImmediateActions(result),
    ...getMonitoringChecklist(result),
  ] : [];
  const resources = result ? verificationResources(result.network || chainType, address) : [];

  return (
    <div className="protection-page">
      <div className="protection-intro fade-in-item" style={fadeStyle(80)}><span>GUIDED PROTECTION</span><h2>Decide with a clear next step</h2></div>
      <Card className="protection-input-card fade-in-item" style={fadeStyle(140)}>
        <form onSubmit={handleSubmit} className="protection-input-row">
          <ChainSelector value={chainType} onChange={setChainType} />
          <input
            type="text"
            className="protection-address-input"
            placeholder={addressPlaceholder(chainType)}
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
          />
          <Button type="submit" variant="primary" loading={status === 'loading'}>Get advice</Button>
        </form>
      </Card>

      {status === 'idle' && (
        <Card className="protection-empty fade-in-item" style={fadeStyle(200)}><p>Paste a contract address above to get protection guidance.</p></Card>
      )}

      {status === 'loading' && (
        <Card className="protection-loading fade-in-item" style={fadeStyle(200)}>
          <div className="protection-spinner" />
          <p>{LOADING_MESSAGES[loadingMsgIndex]}</p>
        </Card>
      )}

      {status === 'error' && (
        <Card className="protection-error">
          <div className="protection-error-title"><AlertCircle size={18} /> Unable to analyze this contract</div>
          <p className="protection-error-detail">{errorMsg}</p>
          <Button variant="secondary" onClick={() => runAnalysis(chainType, addressInput.trim())}>
            <RotateCw size={14} /> Retry
          </Button>
        </Card>
      )}

      {status === 'success' && result && overall && (
        <>
          <Card className={`advisor-hero advisor-hero--${overall.level} fade-in-item`} style={fadeStyle(220)}>
            <div className="advisor-hero-main"><div className="advisor-hero-icon"><BannerIcon size={34} /></div><div className="advisor-hero-copy"><span><Sparkles size={14} /> AI investment decision</span><h2>{overall.label}</h2><p>{overall.desc}</p><small>{result.summary}</small></div><div className="advisor-decision-stats"><div><span>Confidence</span><strong>{Math.round((result.confidence || 0) * 100)}%</strong></div><div><span>Risk level</span><strong>{result.risk_level}</strong></div><div className="advisor-score"><span>Security score</span><strong>{result.risk_score}<small>/100</small></strong><b>{result.risk_level} risk</b></div></div></div>
            <div className="advisor-hero-footer"><BadgeCheck size={16} /><span>Decision based on the available on-chain security signals for this token.</span></div>
          </Card>

          <section className="advisor-why fade-in-item" style={fadeStyle(260)}><div className="advisor-section-heading"><div><span>Why this recommendation</span><h3>Signals supporting the decision</h3></div><ShieldCheck size={20} /></div>{goodSigns.length ? <div className="advisor-signal-chips">{goodSigns.map((signal, index) => <span key={`${signal}-${index}`}><CheckCircle2 size={15} />{signal}</span>)}</div> : <p className="advisor-empty-note">No additional positive signals were returned for this analysis.</p>}</section>

          <section className="advisor-checklist fade-in-item" style={fadeStyle(300)}><div className="advisor-section-heading"><div><span>Protection checklist</span><h3>Complete these steps in order</h3><p>Each task combines the existing protection guidance with a direct verification route.</p></div><ListChecks size={21} /></div><ol>{checklist.map((item, index) => { const detail = checklistPresentation(item.text); const TaskIcon = detail.icon; return <li key={`${item.text}-${index}`} className="advisor-check-card"><span className="advisor-step">{String(index + 1).padStart(2, '0')}</span><div className="advisor-check-item"><div className="advisor-task-heading"><TaskIcon size={19} /><div><strong>{item.text}</strong><p>{detail.description}</p></div><ActionPriorityBadge priority={item.priority} /></div><div className="advisor-resource-buttons">{actionResources(result.network || chainType, address, item.text).map((resource, resourceIndex) => <a className={`advisor-resource-action${resourceIndex === 0 ? ' is-primary' : ''}`} key={resource.href} href={resource.href} target="_blank" rel="noopener noreferrer">{resource.label}<ExternalLink size={12} /></a>)}</div></div></li>; })}</ol></section>

          <section className="advisor-resources fade-in-item" style={fadeStyle(340)}><div className="advisor-section-heading"><div><span>Verification resources</span><h3>Investigate with trusted tools</h3><p>Open chain-aware resources for this exact token address.</p></div><Compass size={21} /></div><div className="advisor-resource-grid">{resources.map(resource => { const ResourceIcon = resourceIcon(resource.label); return <a key={resource.href} className="advisor-resource-card" href={resource.href} target="_blank" rel="noopener noreferrer"><div className="advisor-resource-meta"><ResourceIcon size={18} /><div><span>{resource.label.replace('Open ', '')}</span><small>{resourceDescription(resource.label)}</small></div></div><span>Open <ExternalLink size={12} /></span></a>; })}</div></section>

          <section className="advisor-help fade-in-item" style={fadeStyle(380)}><HelpCircle size={18} /><p>Protection guidance is educational and based on currently available on-chain signals. Verify important decisions independently.</p></section>
        </>
      )}
    </div>
  );
}
