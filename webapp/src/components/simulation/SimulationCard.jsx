import { ArrowRight, Bot, CheckCircle2, CircleAlert, Crosshair, Landmark, ShieldCheck, Sparkles, Target } from 'lucide-react';
import Card from '../Card';
import AttackTimeline from './AttackTimeline';
import { getNetwork } from '../../config/networks';
import './SimulationCard.css';

const SEVERITY_TONES = { Critical: 'critical', High: 'high', Medium: 'medium', Low: 'low' };
const MATRIX_LEVELS = ['Low', 'Medium', 'High'];

function matrixIndex(value) {
  if (value === 'Critical') return 2;
  return Math.max(0, MATRIX_LEVELS.indexOf(value));
}

function ThreatMatrix({ probability, impact }) {
  const col = matrixIndex(probability);
  const row = 2 - matrixIndex(impact);
  return <div className="threat-matrix" aria-label={`Risk matrix: ${probability} probability and ${impact} impact`}><div className="threat-matrix-axis threat-matrix-axis-y">Impact</div><div className="threat-matrix-y-levels"><span>High</span><span>Medium</span><span>Low</span></div><div className="threat-matrix-grid">{[0, 1, 2].map(y => [0, 1, 2].map(x => <span className={`threat-matrix-cell matrix-${x + y} ${x === col && y === row ? 'is-active' : ''}`} key={`${x}-${y}`}>{x === col && y === row && <i />}</span>))}</div><div className="threat-matrix-x-levels"><span>Low</span><span>Medium</span><span>High</span></div><div className="threat-matrix-axis threat-matrix-axis-x">Exploit probability</div><div className="threat-matrix-caption"><span>Current: {impact} impact</span><span>{probability} probability</span></div></div>;
}

export default function SimulationCard({ scenario, chainType, confidence, duration }) {
  const tone = SEVERITY_TONES[scenario.impact] || 'medium';
  const networkLabel = getNetwork(chainType)?.label || 'Unknown network';
  const confidencePct = confidence == null ? 'Unavailable' : `${Math.round(confidence * 100)}%`;
  const journeySteps = scenario.timeline.slice(0, -1);

  return <article className={`incident-report incident-report--${tone}`}>
    <Card className="incident-hero">
      <div className="incident-status"><CircleAlert size={16} /><span>Incident report</span><i /> <span>Potential exploit scenario</span></div>
      <div className="incident-hero-body"><div className="incident-hero-copy"><div className="incident-badges"><span className={`incident-severity severity-${tone}`}>{scenario.impact} severity</span><span>{networkLabel}</span><span><Bot size={13} /> AI investigation</span></div><p className="incident-kicker">On-chain threat detected</p><h2>{scenario.title}</h2><p className="incident-description">{scenario.description}</p></div><div className="incident-threat-signal"><div className="incident-signal-orb"><span>Threat</span><strong>{scenario.probability}</strong><small>probability</small></div><div><span>Threat classification</span><strong>{scenario.impact} impact potential</strong><p>Based on the detected contract capability and its assigned scenario evidence.</p></div></div></div>
      <div className="incident-assessment-band"><div><span>Exploit probability</span><strong>{scenario.probability}</strong></div><div><span>Estimated impact</span><strong>{scenario.impact}</strong></div><div><span>Data confidence</span><strong>{confidencePct}</strong></div><div><span>Simulation runtime</span><strong>{duration ? `${duration}s` : 'Unavailable'}</strong></div></div>
    </Card>

    <section className="incident-section incident-journey"><div className="incident-section-intro"><span>01 — Attack sequence</span><h3>How the threat can unfold</h3><p>A visual progression of the potential scenario identified from the available on-chain finding.</p></div><AttackTimeline steps={journeySteps} tone={tone} /></section>

    <section className="incident-section incident-investigation"><div className="incident-section-intro"><span>02 — AI investigation</span><h3>AI conclusion</h3></div><div className="incident-conclusion"><Sparkles size={22} /><div><span>Primary finding</span><p>{scenario.description}</p></div></div><div className="incident-ai-detail"><div className="incident-weakness"><Crosshair size={18} /><div><span>Detected weakness</span><strong>{scenario.title}</strong></div><b><i /> {confidencePct} confidence</b></div><div className="incident-path"><span>Observed attack path</span><div>{journeySteps.map((step, index) => <span className="incident-path-item" key={step}><em>{step}</em>{index < journeySteps.length - 1 && <ArrowRight size={15} />}</span>)}</div></div></div></section>

    <section className="incident-section incident-impact"><div className="incident-section-intro"><span>03 — Impact visualisation</span><h3>Threat position</h3><p>Probability and impact are plotted from the scenario’s existing categorical assessments.</p></div><div className="incident-impact-visual"><ThreatMatrix probability={scenario.probability} impact={scenario.impact} /><div className="incident-impact-insights"><div><Landmark size={21} /><div><span>Impact</span><strong>{scenario.impact}</strong><p>Potential market or holder consequences if this capability is abused.</p></div></div><div><Target size={21} /><div><span>Execution</span><strong>{scenario.difficulty}</strong><p>Assigned effort needed to follow this potential attack path.</p></div></div></div></div></section>

    <section className="incident-section incident-actions"><div className="incident-section-intro"><span>04 — Recommended action</span><h3>Protective next step</h3><p>Existing mitigation guidance generated for this specific scenario.</p></div><div className="incident-action-row"><div className="incident-action-icon"><ShieldCheck size={21} /></div><div><span className="incident-priority">Priority action</span><h4>{scenario.mitigation}</h4><p>Use this guidance before interacting with the token.</p></div><CheckCircle2 className="incident-action-check" size={21} /></div></section>
  </article>;
}
