# Crypto Due Diligence API

An A2MCP service built for the **OKX.AI Genesis Hackathon** (Finance Copilot
category). Paste a token contract address, get a plain-English risk verdict
backed by real on-chain security data — not an AI guess.

```
User → FastAPI → GoPlus → Normalizer → Deterministic Scoring → AI Explanation → JSON
```

The scoring is fully deterministic (a fixed rules engine, not a model). The AI
layer only ever explains a score that's already been calculated — it never
invents or adjusts the number itself.

## Why this exists

Most "token risk checker" hackathon submissions either trust an LLM to eyeball
a contract (unreliable, unauditable) or dump raw security-API JSON on the user
(unreadable to anyone non-technical). This does neither: real signals in,
fixed rules out, AI only for the explanation layer on top.

## Features

- Deterministic risk scoring (honeypot, mint function, blacklist, proxy,
  holder/liquidity concentration, ownership renouncement, and more)
- LP fragmentation logic — distinguishes "liquidity spread across many
  independent positions" (healthy) from "one or two dominant positions"
  (risky), instead of a naive locked/unlocked flag
- Burn-address exclusion from concentration math
- Confidence score — reflects how much real data GoPlus actually returned,
  not a guess
- 15 EVM chains, verified live against GoPlus's own supported-chains list
  (see below) — not assumed from a generic chain ID table
- Single-file vanilla HTML/CSS/JS frontend, no build step, no framework

## Project layout

```
app/
  core/config.py       — settings + verified SUPPORTED_CHAINS list
  services/goplus.py    — GoPlus API client
  services/normalizer.py — raw GoPlus JSON → stable internal signal shape
  services/scoring.py    — deterministic rules engine
  services/ai.py         — AI explanation layer (OpenAI; falls back to a
                            templated explanation if no key is set)
  routers/token.py        — /analyze/token, /analyze/token/raw
  main.py                 — app entrypoint, CORS, /chains, /health
frontend/index.html        — single-file demo UI
tests/fixtures/             — real captured GoPlus responses (regression baseline)
```

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# fill in OPENAI_API_KEY — GoPlus itself works without a key
```

Run the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs for interactive API docs.

Run the frontend — just open the file, no build step:

```bash
open frontend/index.html
# or serve it: python3 -m http.server 5500 --directory frontend
```

The frontend auto-detects local vs. deployed: it uses `127.0.0.1:8000` when
opened locally, and the URL in `PRODUCTION_API_BASE` (near the top of the
`<script>` tag) everywhere else.

## Try it

Raw GoPlus data, no scoring or AI — useful for inspecting real fields:

```
GET /analyze/token/raw?chain_id=1&address=0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
```

Full analysis:

```bash
curl -X POST http://127.0.0.1:8000/analyze/token \
  -H "Content-Type: application/json" \
  -d '{"chain_id": 1, "address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"}'
```

## Deployment

### Backend → Render

1. Push this repo to GitHub (see below).
2. In the [Render dashboard](https://dashboard.render.com), click
   **New → Blueprint**, and point it at your GitHub repo. Render will pick up
   `render.yaml` automatically and configure the service.
3. When prompted, set the environment variables Render flags as required:
   `OPENAI_API_KEY` (required for AI explanations — the app falls back to a
   templated explanation without it, so it's not strictly required to boot).
   `GOPLUS_APP_KEY` / `GOPLUS_APP_SECRET` can stay blank; GoPlus's
   `token_security` endpoint works unauthenticated at reasonable volume.
4. Deploy. Render will give you a URL like
   `https://crypto-due-diligence-api.onrender.com`. Confirm it works:
   `https://<your-app>.onrender.com/health` should return `{"status": "healthy"}`.

*No `render.yaml`? You can also create the service manually: New → Web
Service → connect the repo → Build Command `pip install -r requirements.txt`
→ Start Command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.*

### Frontend → Vercel

1. In the [Vercel dashboard](https://vercel.com/new), import the same GitHub repo.
2. Set **Root Directory** to `frontend` (important — the HTML file lives in
   a subfolder, not the repo root). No build command or framework preset needed.
3. Before deploying (or after, then redeploy), open `frontend/index.html` and
   set `PRODUCTION_API_BASE` near the top of the `<script>` tag to your actual
   Render URL from the step above.
4. Deploy. Vercel gives you a URL like `https://your-project.vercel.app`.

CORS on the backend is already open (`allow_origins=["*"]`) so the deployed
frontend can call the deployed backend with no extra config. Tighten this in
`app/main.py` to your specific Vercel domain before using this beyond a demo.

### Push to GitHub

```bash
git remote add origin https://github.com/<your-username>/<your-repo>.git
git branch -M main
git push -u origin main
```

(This repo is already git-initialized locally with an initial commit — you
just need to add your remote and push.)

## Supported chains

Verified live against GoPlus's own `/api/v1/supported_chains?name=token_security`
endpoint — not assumed from a generic EVM chain ID list, since some GoPlus
endpoints have used non-standard IDs in the past.

| Ecosystem | Chain | ID |
|---|---|---|
| Ethereum Ecosystem | Ethereum | 1 |
| Ethereum Ecosystem | Arbitrum | 42161 |
| Ethereum Ecosystem | Optimism | 10 |
| Ethereum Ecosystem | Base | 8453 |
| Ethereum Ecosystem | Linea | 59144 |
| Ethereum Ecosystem | Scroll | 534352 |
| Ethereum Ecosystem | zkSync Era | 324 |
| BNB Ecosystem | BNB Chain | 56 |
| BNB Ecosystem | opBNB | 204 |
| Other L1s & L2s | Polygon | 137 |
| Other L1s & L2s | Avalanche C-Chain | 43114 |
| Other L1s & L2s | Cronos | 25 |
| Other L1s & L2s | Mantle | 5000 |
| Other L1s & L2s | Gnosis | 100 |
| OKX Ecosystem | X Layer | 196 |

**Not included** — genuinely unsupported by GoPlus's `token_security` endpoint,
not a wrong ID: Fantom, Moonbeam, Moonriver, Celo, Kava. These are absent from
GoPlus's own `supported_chains` response, so fabricating IDs for them would
silently fail on every scan.

The frontend dropdown is built entirely from `GET /chains` at page load.
Adding or removing a chain only requires editing `SUPPORTED_CHAINS` in
`app/core/config.py` — nothing in the frontend needs to change.

## Next steps

- **Solana support** — GoPlus has a separate Solana Token Security API
  (`/api/v1/solana/token_security`) with a different address format (base58
  mint addresses, not `0x`-prefixed) and a different risk model (mint/freeze
  authority, metadata mutability, rather than EVM proxy/honeypot checks). Not
  added yet — it needs its own normalizer and scoring path verified against
  real responses, the same way the 15 EVM chains were, rather than guessed.
- Add `/analyze/wallet` and `/analyze/portfolio` following the same
  normalize → score → explain pattern
- Wire up x402 payment support if listing this as a paid A2MCP endpoint
- Tighten CORS to the specific deployed frontend origin
