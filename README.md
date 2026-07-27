# 🛡️ Crypto Due Diligence

### Security Intelligence for Crypto Wallets and Tokens

**Crypto Due Diligence** is a multi-chain security intelligence platform built for the **OKX.AI Genesis Hackathon**. It transforms live blockchain and security-provider data into deterministic risk assessments, explainable findings, wallet intelligence, and actionable security guidance.

Instead of asking an LLM to guess whether an asset is safe, the platform follows an evidence-first pipeline:

```text
Live On-Chain Data → Normalization → Deterministic Risk Engine → AI-Assisted Explanation → Actionable Security Intelligence
```

> **Live Platform:** https://cryptoduediligence.dev

---

## 🚀 What the Platform Does

Crypto Due Diligence provides a unified workspace for investigating crypto assets before interacting with them.

### 🔍 Analysis Dashboard

Analyze token contracts using live provider-backed security signals and receive:

- Deterministic security scoring
- Risk and confidence indicators
- Security signal breakdowns
- Contract and token intelligence
- Technical findings
- Explainable risk summaries
- Exportable analysis results

### 👛 Wallet Scanner

Perform live wallet due diligence with:

- Address validation
- Blockchain detection
- Wallet asset discovery
- Portfolio intelligence
- Transaction activity analysis
- Contract coverage analysis
- Asset-level risk classification
- Risk allocation and distribution
- AI-assisted wallet security summaries
- Exportable reports

### ⚖️ Compare Tokens

Analyze supported assets side by side using the same security framework to compare:

- Security scores
- Risk signals
- Contract characteristics
- Liquidity and holder indicators
- Security findings

### 🛡️ Protection Advisor

Transforms detected security risks into practical recommendations so users can understand what actions may reduce exposure.

### ⚡ Attack Simulation

Uses deterministic security signals to model evidence-based potential attack scenarios such as risks related to:

- Mint capabilities
- Proxy behavior
- Blacklisting
- Ownership controls
- Holder concentration
- Liquidity conditions

The simulation describes potential security paths based on available evidence. It does not claim that an attack has occurred.

### 🌐 Multi-Chain Intelligence

The platform supports explicit blockchain routing across provider-supported EVM networks, **X Layer**, and a dedicated **Solana** analysis path.

### 📚 Developer API

The FastAPI backend exposes documented endpoints for integrating security analysis into other applications and workflows.

---

## 🧠 Security Architecture

```text
                         ┌──────────────────────┐
                         │        User          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    React / Vite UI   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    FastAPI Backend   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Network Router    │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                  EVM / X Layer            Solana
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Blockchain / Security│
                         │      Providers       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Normalization     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Deterministic Risk   │
                         │       Engine         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   AI-Assisted        │
                         │    Explanation       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Explainable Security │
                         │      Results         │
                         └──────────────────────┘
```

---

## 🎯 Evidence First, AI Second

A core design principle of Crypto Due Diligence is that **AI should explain security evidence — not invent it**.

The platform separates risk calculation from natural-language explanation.

### Deterministic Layer

Provider-backed security signals are normalized and evaluated using reproducible rules.

### AI Layer

AI helps translate the resulting findings into understandable security summaries and guidance.

```text
Provider Data
     ↓
Normalization
     ↓
Deterministic Rules
     ↓
Risk Assessment
     ↓
AI-Assisted Explanation
```

This makes the security assessment more transparent and auditable than relying on an LLM to independently decide whether a contract is safe.

> **Unavailable data is treated as unknown/unscored — never automatically safe.**

---

## ⛓️ Supported Networks

The platform supports provider-backed analysis across multiple EVM networks:

| Network | Chain ID |
|---|---:|
| Ethereum | 1 |
| Arbitrum | 42161 |
| Optimism | 10 |
| Base | 8453 |
| Linea | 59144 |
| Scroll | 534352 |
| zkSync Era | 324 |
| BNB Chain | 56 |
| opBNB | 204 |
| Polygon | 137 |
| Avalanche C-Chain | 43114 |
| Cronos | 25 |
| Mantle | 5000 |
| Gnosis | 100 |
| X Layer | 196 |

### Solana

Solana uses a dedicated analysis path because its addressing model and security characteristics differ from EVM chains.

The Solana path handles:

- Base58 addresses
- Solana-specific provider routing
- Solana-specific normalization
- SPL-token security data
- Solana-oriented risk signals

### Why explicit network selection?

A `0x` address does not identify which EVM blockchain it belongs to.

The platform therefore requires the intended network to be selected before analysis, preventing ambiguous or incorrectly routed security requests.

---

## 🧰 Technology Stack

### Frontend

- React
- Vite
- JavaScript
- Custom responsive CSS
- Reusable security visualization components

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

### Blockchain & Security Intelligence

- GoPlus
- Moralis
- Helius
- Multi-chain provider adapters
- Chain-specific normalization
- Deterministic scoring engines

### Deployment

- **Vercel** — frontend
- **Render** — backend
- **GitHub** — source control and deployment integration

---

## 🔌 API

The backend exposes REST endpoints through FastAPI.

Core endpoints include:

```text
POST /analyze/token
GET  /analyze/token/raw
POST /analyze/wallet
GET  /chains
GET  /health
```

Interactive API documentation is available through:

```text
/docs
```

The API uses explicit chain information for network-sensitive analysis.

Example token-analysis request:

```json
{
  "chain_type": "evm",
  "chain_id": 1,
  "address": "0x..."
}
```

---

## 📁 Project Structure

```text
crypto-due-diligence-api/
│
├── app/
│   ├── core/
│   ├── models/
│   ├── routers/
│   ├── services/
│   │   └── wallet/
│   └── main.py
│
├── tests/
│
├── webapp/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── config/
│   │   ├── pages/
│   │   └── utils/
│   └── package.json
│
├── .env.example
├── render.yaml
├── requirements.txt
└── README.md
```

---

## 💻 Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/Osaid1122/crypto-due-diligence-api.git
cd crypto-due-diligence-api
```

### 2. Backend Setup

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Configure the required provider/API credentials in `.env`.

Start FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd webapp
npm install
npm run dev
```

Vite will display the local frontend address.

### Production Build

```bash
npm run build
```

---

## 🧪 Testing

Run the backend test suite:

```bash
python -m pytest -q
```

The project includes automated coverage for areas including:

- Wallet analysis
- Chain routing
- Security-analysis behavior
- Deterministic analysis logic

Before the final deployment, the backend test suite and production frontend build were verified successfully.

---

## ☁️ Production Deployment

The deployed architecture separates the frontend application from the analysis API.

```text
              cryptoduediligence.dev
                       │
                       ▼
                    Vercel
                       │
                       ▼
                React / Vite App
                       │
                       ▼
                 FastAPI Backend
                       │
                       ▼
                    Render
                       │
                       ▼
          Blockchain & Security Providers
```

Sensitive provider credentials are supplied through deployment environment variables and are not stored in the repository.

---

## 🔐 Security Design Principles

### 1. Evidence First

Security conclusions should originate from real blockchain and provider-backed signals whenever available.

### 2. Deterministic Scoring

Risk calculations should be reproducible. The same normalized signals should produce the same deterministic assessment.

### 3. Explainability

A security score alone is not enough. The platform exposes the findings and signals contributing to the assessment.

### 4. Chain-Aware Analysis

Different blockchain ecosystems require different routing, provider integrations, and interpretation.

### 5. Unknown ≠ Safe

Missing provider information must never silently become a positive security signal.

---

## 🏆 OKX.AI Genesis Hackathon

Crypto Due Diligence was developed for the **OKX.AI Genesis Hackathon** as a security-focused due-diligence platform combining:

- Live blockchain intelligence
- Multi-chain analysis
- Deterministic security scoring
- Wallet intelligence
- Token security analysis
- AI-assisted explanations
- Attack simulation
- Actionable protection guidance

The objective is simple:

> **Make complex on-chain security signals understandable enough to act on.**

---

## ⚠️ Disclaimer

Crypto Due Diligence provides security intelligence and due-diligence assistance.

It does **not** provide financial or investment advice, and no analysis can guarantee that a token, wallet, smart contract, protocol, or transaction is safe.

Provider availability, blockchain state, contract changes, market conditions, and incomplete data can affect analysis results.

Always perform independent research before making financial or security-sensitive decisions.

---

## 🛡️ Crypto Due Diligence

**Security intelligence for crypto wallets and tokens.**

🌐 **Live:** https://cryptoduediligence.dev
