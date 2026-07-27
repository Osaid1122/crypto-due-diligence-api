import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight, Bot, CheckCircle2, ChevronDown, CircleAlert, GitCompareArrows,
  LockKeyhole, Radar, ScanSearch, ShieldCheck, ShieldQuestion,
  ShieldAlert, Sparkles, Workflow, Orbit,
} from 'lucide-react';
import Button from '../components/Button';
import Card from '../components/Card';
import ChainSelector, { addressPlaceholder, isValidAddress } from '../components/ChainSelector';
import ChainLogo from '../components/ChainLogo';
import './Home.css';

const FEATURES = [
  { icon: ScanSearch, title: 'Smart Contract Analysis', description: 'Inspect permissions, ownership, mint authority, liquidity, blacklist capability, proxy status, and security configuration.' },
  { icon: GitCompareArrows, title: 'Compare Tokens', description: 'Compare two contracts with deterministic scoring, AI summaries, security signals, and confidence metrics.' },
  { icon: ShieldCheck, title: 'Protection Advisor', description: 'Get AI-guided recommendations before investing, grounded in the risks and protections detected.' },
  { icon: Workflow, title: 'Attack Simulation', description: 'Visualize how contract capabilities could theoretically be abused through educational attack paths.' },
];

const VALUES = [
  { icon: ShieldAlert, title: 'Prevent Rug Pulls', description: 'Detect dangerous contract permissions before you invest.' },
  { icon: Bot, title: 'Understand Smart Contracts', description: 'Translate complex blockchain data into clear, practical insight.' },
  { icon: Orbit, title: 'Multi-Chain Coverage', description: 'Analyze contracts across supported EVM networks and Solana from one interface.' },
  { icon: ShieldQuestion, title: 'Decision Support', description: 'Receive actionable guidance instead of raw technical data.' },
];

const STEPS = [
  { icon: LockKeyhole, label: 'Paste contract address' },
  { icon: Sparkles, label: 'AI analyzes contract' },
  { icon: Radar, label: 'Risk engine calculates score' },
  { icon: ShieldCheck, label: 'Receive recommendations' },
];

const TRUST = ['Multi-chain analysis', 'AI-powered security scoring', 'Deterministic risk engine', 'Educational attack simulation', 'Real-time contract intelligence'];

export default function Home() {
  const navigate = useNavigate();
  const [chainType, setChainType] = useState('ethereum');
  const [address, setAddress] = useState('');
  const [error, setError] = useState('');

  function startAnalysis(event) {
    event?.preventDefault();
    if (!address.trim()) return navigate('/dashboard');
    if (!isValidAddress(chainType, address)) {
      setError(chainType === 'solana' ? 'Enter a valid Solana mint address.' : `Enter a valid ${chainType === 'xlayer' ? 'X Layer' : 'Ethereum'} address.`);
      return;
    }
    navigate(`/dashboard?chain_type=${chainType}&address=${address.trim()}`);
  }

  function scrollToFeatures() { document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' }); }

  return <div className="home">
    <section className="home-hero">
      <div className="home-hero-copy home-enter">
        <div className="home-kicker"><span className="home-kicker-dot" /> AI SECURITY INTELLIGENCE</div>
        <h1>Analyze Crypto Smart Contracts <span>Before You Invest</span></h1>
        <p>AI-powered EVM + Solana security intelligence. Detect contract risks, compare tokens, simulate attack paths, and receive actionable protection guidance in seconds.</p>
        <div className="home-hero-actions">
          <Button variant="primary" onClick={startAnalysis}>Analyze Contract <ArrowRight size={17} /></Button>
          <Button variant="secondary" onClick={scrollToFeatures}>View Features <ChevronDown size={16} /></Button>
        </div>
        <div className="home-supported-inline"><CheckCircle2 size={15} /> Ethereum <span /> <CheckCircle2 size={15} /> X Layer <span /> <CheckCircle2 size={15} /> Solana</div>
      </div>
      <div className="home-hero-visual home-enter">
        <div className="home-orbit home-orbit-one" /><div className="home-orbit home-orbit-two" />
        <div className="home-visual-panel">
          <div className="home-visual-top"><span><ShieldCheck size={15} /> SECURITY SCAN</span><b>LIVE</b></div>
          <div className="home-visual-score"><div className="home-score-ring"><strong>18</strong><small>LOW RISK</small></div><div><span>Contract intelligence</span><h3>USDC</h3><p>Ethereum · Verified signals</p></div></div>
          <div className="home-visual-bars">{[['Ownership', 84], ['Liquidity', 93], ['Trading', 88]].map(([label, width]) => <div key={label}><span>{label}</span><i><b style={{ width: `${width}%` }} /></i></div>)}</div>
          <div className="home-visual-foot"><span><CheckCircle2 size={14} /> Analysis complete</span><span>98% confidence</span></div>
        </div>
        <div className="home-float-card home-float-one"><Sparkles size={16} /><span>AI summary ready</span></div>
        <div className="home-float-card home-float-two"><CheckCircle2 size={16} /><span>3 checks passed</span></div>
      </div>
    </section>

    <section className="home-analysis-box home-reveal">
      <div><span>START HERE</span><h2>Run a live contract check</h2></div>
      <form onSubmit={startAnalysis}>
        <ChainSelector value={chainType} onChange={setChainType} />
        <input value={address} onChange={event => { setAddress(event.target.value); setError(''); }} placeholder={addressPlaceholder(chainType)} aria-label="Contract address" />
        <Button type="submit" variant="primary">Analyze <ArrowRight size={16} /></Button>
      </form>
      {error && <p className="home-input-error"><CircleAlert size={14} /> {error}</p>}
    </section>

    <section className="home-section" id="features"><div className="home-section-heading"><span>CORE INTELLIGENCE</span><h2>Everything you need to evaluate a token</h2><p>One clear security workspace for your next on-chain decision.</p></div><div className="home-feature-grid">{FEATURES.map(({ icon: Icon, title, description }, index) => <Card hoverable className="home-feature-card home-reveal" key={title} style={{ '--delay': `${index * 70}ms` }}><span className="home-feature-icon"><Icon size={21} /></span><h3>{title}</h3><p>{description}</p><ArrowRight size={16} className="home-feature-arrow" /></Card>)}</div></section>

    <section className="home-chain-section home-section"><div className="home-section-heading"><span>SUPPORTED NETWORKS</span><h2>Multi-Chain Security Intelligence</h2><p>Focused support where you need it today.</p></div><div className="home-chain-grid">{[{ name: 'Ethereum', detail: 'EVM', id: 'ethereum' }, { name: 'X Layer', detail: 'EVM', id: 'xlayer' }, { name: 'Solana', detail: 'SVM / Solana', id: 'solana' }].map(({ name, detail, id }) => <div className="home-chain-badge" key={name}><span className="home-chain-icon"><ChainLogo chain={id} size={29} /></span><div><h3>{name}</h3><p>{detail}</p></div><span className="home-chain-status"><CheckCircle2 size={15} /> Supported</span></div>)}</div></section>

    <section className="home-section home-how"><div className="home-section-heading"><span>HOW IT WORKS</span><h2>Clarity in four steps</h2></div><div className="home-step-line">{STEPS.map(({ icon: Icon, label }, index) => <div className="home-step home-reveal" key={label} style={{ '--delay': `${index * 100}ms` }}><span className="home-step-icon"><Icon size={20} /></span><strong>0{index + 1}</strong><p>{label}</p></div>)}</div></section>

    <section className="home-section"><div className="home-section-heading"><span>WHY CRYPTO DUE DILIGENCE</span><h2>Security intelligence made actionable</h2></div><div className="home-value-grid">{VALUES.map(({ icon: Icon, title, description }) => <div className="home-value" key={title}><Icon size={19} /><div><h3>{title}</h3><p>{description}</p></div></div>)}</div></section>

    <section className="home-trust">{TRUST.map(item => <div key={item}><CheckCircle2 size={17} /><span>{item}</span></div>)}</section>

    <section className="home-final-cta"><span>MAKE THE NEXT MOVE WITH CONTEXT</span><h2>Ready to Analyze a Smart Contract?</h2><p>Get a security-first view before you connect, trade, or invest.</p><Button variant="primary" onClick={() => navigate('/dashboard')}>Start Analysis <ArrowRight size={17} /></Button></section>

    <footer className="home-footer"><div><h3><span>Crypto</span> Due Diligence</h3><p>AI Security Intelligence</p><small>Built for OKX AI Genesis Hackathon</small></div><div className="home-footer-links"><div><b>Navigate</b><Link to="/dashboard">Analysis Dashboard</Link><Link to="/compare">Compare Tokens</Link><Link to="/protection">Protection Advisor</Link><Link to="/simulation">Attack Simulation</Link></div><div><b>Supported networks</b><span>Ethereum</span><span>X Layer</span><span>Solana</span></div></div></footer>
  </div>;
}
