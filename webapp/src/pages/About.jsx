import { Activity, ArrowRight, BookOpen, Braces, DatabaseZap, GitCompareArrows, Layers, Network, ScanSearch, ServerCog, ShieldCheck, ShieldAlert, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import Card from '../components/Card';
import './About.css';

const capabilities = [
  ['Wallet Intelligence', 'Review holdings, activity, and portfolio exposure.', ScanSearch],
  ['Token Risk Analysis', 'Screen contracts with deterministic security signals.', ShieldAlert],
  ['Attack Simulation', 'Explore evidence-based potential attack paths.', Sparkles],
  ['Protection Advisor', 'Turn detected risks into practical next steps.', ShieldCheck],
  ['Token Comparison', 'Compare supported assets side by side.', GitCompareArrows],
  ['Multi-Chain Analysis', 'Route analysis through the selected chain provider.', Layers],
];

const EVM_NETWORKS = ['Ethereum', 'Arbitrum', 'Optimism', 'Base', 'Linea', 'Scroll', 'zkSync Era', 'BNB Chain', 'opBNB', 'Polygon', 'Avalanche C-Chain', 'Cronos', 'Mantle', 'Gnosis', 'X Layer · 196'];

export default function About() {
  return <div className="about-page">
    <section className="about-hero">
      <div className="about-hero-copy">
        <div className="about-eyebrow"><ShieldCheck size={14} /> Crypto Due Diligence</div>
        <h1>Security intelligence for crypto wallets and tokens</h1>
        <p>Live, explainable security reviews for wallet exposure and token-contract risk across supported networks.</p>
        <div className="about-hero-actions">
          <Link className="about-action about-action-primary" to="/wallet">Analyze a Wallet <ArrowRight size={16} /></Link>
          <Link className="about-action about-action-secondary" to="/dashboard">Analyze a Token</Link>
        </div>
      </div>
      <Card className="about-status-card">
        <div className="about-status-heading"><div><span>Platform capabilities</span><h2>Built for live due diligence</h2></div><Activity size={20} /></div>
        <div className="about-status-grid">
          <div><Network size={16} /><span>Multi-chain</span></div>
          <div><DatabaseZap size={16} /><span>Live data</span></div>
          <div><Sparkles size={16} /><span>AI-assisted</span></div>
          <div><Braces size={16} /><span>API available</span></div>
        </div>
        <p>API v1.0 · FastAPI · JSON responses</p>
      </Card>
    </section>

    <section className="about-value-grid">
      <Card className="about-value-card"><ShieldCheck size={21} /><div><h2>Mission</h2><p>Make on-chain security signals clear enough to act on.</p></div></Card>
      <Card className="about-value-card"><Sparkles size={21} /><div><h2>Why it matters</h2><p>See exposure and contract risk before an interaction.</p></div></Card>
    </section>

    <section className="about-workflow">
      <div className="about-section-heading"><span>HOW IT WORKS</span><h2>A focused security review in four steps</h2></div>
      <div className="about-step-flow">
        {['Submit a wallet or token', 'Select the network', 'Retrieve live provider data', 'Review explainable findings'].map((step, index) => <div key={step}><strong>0{index + 1}</strong><span>{step}</span></div>)}
      </div>
    </section>

    <section className="about-method-card">
      <div><Layers size={20} /><h2>Analysis methodology</h2><p>Provider-backed signals are scored deterministically. Unavailable asset data stays Unscored — never Safe.</p></div>
      <div className="about-method-points"><span>Live provider data</span><span>Deterministic rules</span><span>Explainable summaries</span></div>
    </section>

    <section className="about-tech-card">
      <div className="about-section-heading"><span><ServerCog size={14} /> TECHNOLOGY STACK</span><h2>Built with the services that power the product</h2></div>
      <div className="about-stack-list"><span>FastAPI</span><span>React</span><span>Python</span><span>GoPlus</span><span>Moralis</span><span>Helius</span></div>
    </section>

    <section className="about-capabilities"><div className="about-section-heading"><span>PRODUCT CAPABILITIES</span><h2>One workspace for crypto security review</h2></div><div className="about-capability-grid">{capabilities.map(([title, description, Icon]) => <Card className="about-capability-card" key={title}><div className="about-capability-icon"><Icon size={21} /></div><h3>{title}</h3><p>{description}</p></Card>)}</div></section>

    <section className="about-networks">
      <div className="about-section-heading"><span>SUPPORTED NETWORKS</span><h2>Explicit network selection for accurate routing</h2><p>A 0x address does not identify its blockchain. Select the intended EVM network before analysis.</p></div>
      <div className="about-network-groups">
        <div className="about-network-group about-network-group-evm"><div><Layers size={19} /><strong>EVM Networks</strong><small>Provider-supported token security · X Layer is EVM-compatible</small></div><div className="about-network-badges">{EVM_NETWORKS.map(network => <span key={network}>{network}</span>)}</div></div>
        <div className="about-network-group"><div><BookOpen size={19} /><strong>Solana</strong><small>Separate SPL-token provider path</small></div><div className="about-network-badges"><span>Solana Mainnet</span></div></div>
      </div>
      <p className="about-network-note">Network availability depends on the configured security and data providers.</p>
    </section>

    <section className="about-disclaimer"><ShieldCheck size={16} /><p><strong>Security intelligence, not investment advice.</strong> Results support due diligence and do not guarantee safety or replace independent research.</p></section>
  </div>;
}
