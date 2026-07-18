import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, ArrowRight, FileText, ScanLine, Database, Sparkles,
  FileBarChart, ShieldCheck, Activity, GitCompare, Wallet, Network,
  Code, LayoutGrid, AlertCircle,
} from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import { fetchChains, ADDRESS_RE } from '../api/client';
import './Home.css';

const HOW_IT_WORKS = [
  { icon: FileText, title: 'Enter Contract', desc: 'Paste any token contract.' },
  { icon: ScanLine, title: 'Security Analysis', desc: 'Fetch blockchain security data.' },
  { icon: Sparkles, title: 'AI Explanation', desc: 'Generate an easy-to-understand summary.' },
  { icon: FileBarChart, title: 'Risk Report', desc: 'View score, risks, and recommendations.' },
];

const FEATURES = [
  { icon: FileBarChart, title: 'Deterministic Risk Score', desc: 'Score comes from transparent rules, never AI.' },
  { icon: Sparkles, title: 'AI Explanations', desc: 'Plain-English summaries of every finding.' },
  { icon: Activity, title: 'Attack Simulation', desc: 'Educational scenarios showing how risks could be abused.' },
  { icon: ShieldCheck, title: 'Protection Advisor', desc: 'Practical recommendations before you act.' },
  { icon: GitCompare, title: 'Token Comparison', desc: 'Evaluate two tokens side by side.' },
  { icon: Wallet, title: 'Wallet Scanner', desc: 'Portfolio-level risk exposure at a glance.' },
  { icon: Network, title: 'Multi-Chain Support', desc: '15 EVM chains, verified against live data.' },
  { icon: Code, title: 'Open API', desc: 'Every analysis is available over a documented REST API.' },
];

// NOTE: SHIB address below is NOT independently verified against a live source
// the way the 15 chain IDs were — confirm it resolves to the real SHIB contract
// before this ships, or swap in a token you've already tested through the API.
const LIVE_DEMO_EXAMPLES = [
  { label: 'USDC', risk: 'Low Risk', color: 'var(--success)', address: '0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', chainId: 1 },
  { label: 'SHIB', risk: 'Medium Risk', color: 'var(--warning)', address: '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE', chainId: 1 },
];

export default function Home() {
  const navigate = useNavigate();
  const [chains, setChains] = useState([]);
  const [chainId, setChainId] = useState('');
  const [address, setAddress] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchChains()
      .then(data => {
        setChains(data.chains || []);
        if (data.chains?.length) setChainId(String(data.chains[0].id));
      })
      .catch(() => setError('Could not load supported chains — is the API running?'));
  }, []);

  function handleAnalyze(e) {
    e?.preventDefault();
    const trimmed = address.trim();
    if (!ADDRESS_RE.test(trimmed)) {
      setError('Enter a valid contract address — 0x followed by 40 hex characters.');
      return;
    }
    setError('');
    navigate(`/dashboard?chain=${chainId}&address=${trimmed}`);
  }

  function useExample(ex) {
    setChainId(String(ex.chainId));
    setAddress(ex.address);
    setError('');
  }

  const groupedChains = chains.reduce((acc, c) => {
    (acc[c.ecosystem] ||= []).push(c);
    return acc;
  }, {});

  return (
    <div className="home">

      {/* ── Hero ── */}
      <section className="home-hero">
        <div className="home-hero-badge">
          <Shield size={14} />
          <span>Deterministic scoring · AI-explained</span>
        </div>
        <h1>AI-Powered Crypto Due Diligence</h1>
        <p>Analyze any EVM token using deterministic security analysis with AI-powered explanations.</p>
        <div className="home-hero-actions">
          <Button variant="primary" onClick={handleAnalyze}>
            Analyze Token <ArrowRight size={16} />
          </Button>
          <Button variant="secondary" onClick={() => navigate('/docs')}>
            View Documentation
          </Button>
        </div>
      </section>

      {/* ── Analyze section ── */}
      <section className="home-analyze">
        <Card className="home-analyze-card">
          <form onSubmit={handleAnalyze}>
            <div className="home-analyze-row">
              <select
                className="home-chain-select"
                value={chainId}
                onChange={(e) => setChainId(e.target.value)}
                aria-label="Blockchain"
              >
                {Object.entries(groupedChains).map(([eco, list]) => (
                  <optgroup key={eco} label={eco}>
                    {list.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </optgroup>
                ))}
                {!chains.length && <option value="">Loading chains…</option>}
              </select>
              <input
                type="text"
                className="home-address-input"
                placeholder="0xA0b86991..."
                value={address}
                onChange={(e) => { setAddress(e.target.value); setError(''); }}
              />
              <Button type="submit" variant="primary">Analyze</Button>
            </div>
            {error && (
              <div className="home-analyze-error">
                <AlertCircle size={14} /> <span>{error}</span>
              </div>
            )}
          </form>
        </Card>
      </section>

      {/* ── How it works ── */}
      <section className="home-section">
        <h2>How it works</h2>
        <div className="home-grid-4">
          {HOW_IT_WORKS.map((step, i) => (
            <Card key={step.title} hoverable className="home-step-card">
              <div className="home-step-number">{i + 1}</div>
              <step.icon size={22} className="home-card-icon" />
              <h3>{step.title}</h3>
              <p>{step.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="home-section">
        <h2>Features</h2>
        <div className="home-grid-4">
          {FEATURES.map(f => (
            <Card key={f.title} hoverable className="home-feature-card">
              <f.icon size={20} className="home-card-icon" />
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Supported chains ── */}
      <section className="home-section">
        <h2>Supported networks</h2>
        <div className="home-grid-chains">
          {chains.map(c => (
            <Card
              key={c.id}
              hoverable
              className="home-chain-card"
              onClick={() => setChainId(String(c.id))}
              role="button"
              tabIndex={0}
            >
              <LayoutGrid size={18} className="home-card-icon" />
              <div className="home-chain-name">{c.name}</div>
              <div className="home-chain-id">Chain ID {c.id}</div>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Live demo ── */}
      <section className="home-section">
        <h2>Live demo</h2>
        <div className="home-grid-demo">
          {LIVE_DEMO_EXAMPLES.map(ex => (
            <Card key={ex.label} hoverable className="home-demo-card" onClick={() => useExample(ex)} role="button" tabIndex={0}>
              <div className="home-demo-label">{ex.label}</div>
              <div className="home-demo-risk" style={{ color: ex.color }}>{ex.risk}</div>
            </Card>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="home-cta">
        <h2>Start your security analysis</h2>
        <div className="home-hero-actions">
          <Button variant="primary" onClick={handleAnalyze}>Analyze Token</Button>
          <Button variant="secondary" onClick={() => navigate('/docs')}>View API Documentation</Button>
        </div>
      </section>

    </div>
  );
}
