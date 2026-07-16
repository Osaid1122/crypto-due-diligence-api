# Crypto Due Diligence API

A2MCP service for the OKX.AI Genesis Hackathon (Finance Copilot category).
Takes a token contract address, pulls security data from GoPlus, runs it
through a deterministic scoring engine, then has an LLM explain the score
in plain English. The AI never invents the score — only explains it.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in OPENAI_API_KEY (GoPlus works without a key for now)
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Then open http://127.0.0.1:8000/docs for interactive API docs.

## Try it

Raw GoPlus data (no scoring/AI, good for inspecting real fields today):
```
GET /analyze/token/raw?chain_id=1&address=0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
```

Full analysis:
```bash
curl -X POST http://127.0.0.1:8000/analyze/token \
  -H "Content-Type: application/json" \
  -d '{"chain_id": 1, "address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"}'
```

## Project layout

- `app/services/goplus.py` — GoPlus API client
- `app/services/scoring.py` — deterministic rules engine (edit CHECKS list to tune)
- `app/services/ai.py` — AI explanation layer (OpenAI, falls back to templated text if no key)
- `app/routers/token.py` — the `/analyze/token` endpoint

## Chain IDs supported

| Chain | ID |
|---|---|
| Ethereum | 1 |
| BSC | 56 |
| Polygon | 137 |
| Arbitrum | 42161 |
| X Layer | 196 |

## Next steps

- Run `/analyze/token/raw` against the three test tokens (USDC, LINK, UNI) and
  a known risky token, compare against the CHECKS list in scoring.py, tune weights
- Add `/analyze/wallet` and `/analyze/portfolio` following the same pattern
- Wire up x402 payment support if going the paid-endpoint route

## Frontend demo

A single-file demo UI lives in `frontend/index.html` — no build step, just open it
in a browser (or serve it) while the backend is running on `localhost:8000`.

```bash
# terminal 1
uvicorn app.main:app --reload --port 8000

# terminal 2 — just open the file directly, or serve it
open frontend/index.html
# or: python3 -m http.server 5500 --directory frontend
```

If you deploy the backend somewhere other than `127.0.0.1:8000`, update `API_BASE`
near the top of the `<script>` tag in `index.html`.

## Supported chains (v0.2.0)

Fetched live from GoPlus's `/api/v1/supported_chains?name=token_security` on
2026-07-12, not assumed from generic EVM chain ID lists — some GoPlus endpoints
use non-standard IDs, so this was worth verifying directly.

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

**Not included — genuinely unsupported by GoPlus's token_security endpoint,
not a wrong ID:** Fantom, Moonbeam, Moonriver, Celo, Kava. These are absent
from GoPlus's own `supported_chains` response. Adding fabricated IDs for them
would silently fail on every scan, so they're left out rather than guessed.

The frontend dropdown is built entirely from `GET /chains` at page load —
adding or removing a chain only requires editing `SUPPORTED_CHAINS` in
`app/core/config.py`, nothing in the frontend needs to change.
