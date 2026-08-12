"""
AI explanation layer.

Takes the deterministic score + reasons and produces a human-readable verdict,
top concerns, and recommended checks. Two paths:

  * LLM path (when OPENAI_API_KEY is set) — the model is given the score,
    severity, economic context and positives and asked ONLY to explain them,
    never to recompute the number.
  * Templated path (no key, or the LLM call fails after one retry) — a
    deterministic synthesizer. This is NOT a throwaway stub: the public service
    frequently runs without an OpenAI key, so this template is what most callers
    actually read. It therefore does real synthesis — leads with the dominant
    finding, adds economic context, credits clean authorities, and flags low
    confidence — rather than merely restating "scored X/100".

Both paths converge on the same JSON shape:
    {"summary": str, "top_concerns": [str], "recommended_checks": [str]}
"""

import json
import httpx

from app.core.config import get_settings

SYSTEM_PROMPT = """You are a crypto risk analyst. You will be given a numeric risk score \
(0-100, already calculated by a deterministic rules engine), the derived risk level, the \
single most severe finding's severity, a list of specific technical reasons that contributed \
to the score, any positive signals, and — when available — economic context (absolute \
on-chain liquidity in USD and 24h trading volume in USD).

Your job is ONLY to explain the score in plain English — you must NOT change, \
recalculate, or second-guess the numeric score itself. Treat the score, level, reasons, \
positive signals, and economic context as ground truth. Never mention a signal that wasn't \
provided to you, and never speculate about data you don't have.

Guidance for a genuinely useful explanation:
- Lead the summary with the SINGLE most important finding (the highest-severity reason), \
not a restatement of the number. If the numeric score looks mild but a high-severity flag \
is present, make that tension explicit ("contract controls look clean, but ...").
- If economic context shows very low liquidity or zero recent volume, translate what that \
means for a user in practice (hard to sell, severe slippage, possibly abandoned) — this is \
often the most decision-relevant fact even when the score is moderate.
- If positive signals or clean authorities are present, acknowledge them so the verdict is \
balanced, not alarmist.
- If confidence is below 0.5, say plainly that limited provider data was available rather \
than sounding confident.

Respond ONLY with a JSON object, no other text, no markdown fences, in this exact shape:
{
  "summary": "2-3 sentence plain-English verdict that leads with the dominant risk",
  "top_concerns": ["short phrase", "short phrase", "short phrase"],
  "recommended_checks": ["actionable next step", "actionable next step", "actionable next step"]
}

top_concerns should restate the most important reasons in plain language (max 3, empty list if none).
recommended_checks should be concrete things a user should verify before acting (max 3).
Keep every string under 22 words. Do not include generic disclaimers or filler."""


def _fmt_usd(value: float) -> str:
    """Compact USD formatting: $12, $8.4K, $2.3M."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "$0"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:,.0f}"


def _economic_sentence(economic: dict) -> str | None:
    """A plain-English read of absolute liquidity/volume, or None if we have neither."""
    if not economic:
        return None
    liq = economic.get("total_liquidity_usd")
    vol = economic.get("total_volume_24h_usd")
    parts: list[str] = []
    if liq is not None:
        if liq < 1_000:
            parts.append(f"on-chain liquidity is effectively gone ({_fmt_usd(liq)} across all known pools), so the token is likely unsellable in any real size")
        elif liq < 50_000:
            parts.append(f"liquidity is shallow ({_fmt_usd(liq)}), so larger trades will move the price sharply")
        else:
            parts.append(f"liquidity depth is reasonable ({_fmt_usd(liq)})")
    if vol is not None and vol <= 0:
        parts.append("no trades were recorded in the last 24h, suggesting an inactive or abandoned market")
    elif vol is not None and vol > 0:
        parts.append(f"~{_fmt_usd(vol)} changed hands in the last 24h")
    if not parts:
        return None
    return "Economically, " + "; ".join(parts) + "."


def _clean_authorities_note(score_data: dict) -> str | None:
    """Credit reassuring 'not triggered' signals so the verdict stays balanced."""
    clean = {r.get("field") for r in score_data.get("not_triggered_rules", [])}
    reassurances = {
        "has_mint_authority": "mint authority revoked",
        "has_freeze_authority": "freeze authority revoked",
        "is_honeypot": "no honeypot detected",
        "is_open_source": "source code verified",
        "metadata_mutable": "metadata immutable",
        "closable": "cannot be closed by an authority",
    }
    hits = [text for field, text in reassurances.items() if field in clean]
    if not hits:
        return None
    shown = ", ".join(hits[:3])
    return f"On the positive side: {shown}."


def build_templated_explanation(token_name: str, token_symbol: str, score_data: dict) -> dict:
    """Deterministic, genuinely-synthesized explanation used whenever the LLM
    path is unavailable. Leads with the worst finding, adds economic + positive
    context, and always contains the literal 'scored <N>/100' substring (relied
    on by callers and regression tests)."""
    score = score_data["score"]
    level = score_data["risk_level"]
    reasons = score_data.get("reasons", [])
    max_severity = score_data.get("max_severity", "None")
    confidence = score_data.get("confidence", 0.0)

    label = token_name if token_name and token_name != "Unknown token" else "This token"
    symbol = f" ({token_symbol})" if token_symbol and token_symbol != "?" else ""

    # Lead sentence: dominant finding first, with the score woven in (never the
    # whole message). The 'scored N/100' substring is preserved verbatim.
    if reasons:
        lead = (
            f"{label}{symbol} scored {score}/100 ({level} risk); the most serious finding is "
            f"{reasons[0][0].lower() + reasons[0][1:]}."
        )
        if max_severity in ("Critical", "High") and level in ("Low", "Medium"):
            lead += (
                f" Note the headline score is moderate, but a {max_severity.lower()}-severity "
                f"issue is present and should drive the decision."
            )
    else:
        lead = (
            f"{label}{symbol} scored {score}/100 ({level} risk) with no risk rules triggered "
            f"on the available provider signals."
        )

    sentences = [lead]
    econ = _economic_sentence(score_data.get("economic_context", {}))
    if econ:
        sentences.append(econ)
    clean_note = _clean_authorities_note(score_data)
    if clean_note:
        sentences.append(clean_note)
    if confidence < 0.5:
        sentences.append(
            f"Confidence is limited ({confidence:.0%}) — the provider returned only part of the "
            f"expected security data, so treat this as a partial picture."
        )

    top_concerns = reasons[:3] if reasons else ["No specific risk signals were flagged by the rules engine."]

    recommended_checks = [
        "Review the full technical_data for details on each flagged item.",
        "Verify contract ownership and liquidity lock status independently.",
    ]
    econ_ctx = score_data.get("economic_context", {})
    if econ_ctx.get("total_liquidity_usd") is not None and econ_ctx["total_liquidity_usd"] < 50_000:
        recommended_checks.insert(
            0, "Confirm there is real, tradeable liquidity before buying — try a small test sell first."
        )
    else:
        recommended_checks.append("Check recent holder and liquidity movements before transacting.")

    return {
        "summary": " ".join(sentences),
        "top_concerns": top_concerns[:3],
        "recommended_checks": recommended_checks[:3],
    }


async def explain_score(token_name: str, token_symbol: str, score_data: dict) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return build_templated_explanation(token_name, token_symbol, score_data)

    user_content = json.dumps({
        "token_name": token_name,
        "token_symbol": token_symbol,
        "score": score_data["score"],
        "risk_level": score_data["risk_level"],
        "max_severity": score_data.get("max_severity"),
        "confidence": score_data["confidence"],
        "reasons": score_data["reasons"],
        "positive_signals": score_data.get("positive_signals", []),
        "economic_context": score_data.get("economic_context", {}),
    })

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try once, retry once. A retry is warranted whether the failure was a
        # transient upstream error (429/5xx/timeout/connection reset) or a
        # malformed model response. Any failure that survives the retry must NOT
        # propagate: an uncaught exception here becomes a Starlette 500 that is
        # generated OUTSIDE CORSMiddleware and therefore carries no
        # Access-Control-Allow-Origin, which the browser reports as a CORS
        # error. Token analysis must degrade to the templated synthesizer instead.
        for attempt in range(2):
            try:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.openai_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_content},
                        ],
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"]
                cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                parsed = json.loads(cleaned)
                # Guard against a well-formed-JSON-but-wrong-shape model reply.
                if not isinstance(parsed.get("summary"), str) or not parsed["summary"].strip():
                    raise ValueError("model response missing a usable summary")
                parsed.setdefault("top_concerns", score_data.get("reasons", [])[:3])
                parsed.setdefault("recommended_checks", [])
                return parsed
            except (
                httpx.HTTPError,        # base for TimeoutException, ConnectError, HTTPStatusError, etc.
                httpx.HTTPStatusError,  # explicitly, though HTTPError already covers it
                httpx.TimeoutException,
                httpx.ConnectError,
                KeyError,               # unexpected OpenAI response shape
                ValueError,             # includes json.JSONDecodeError (malformed content)
            ):
                if attempt == 0:
                    continue  # retry once
                break         # fall through to the templated synthesizer below

    # Final fallback: the same rich, deterministic synthesizer used on the
    # keyless path — so an AI outage degrades to a genuinely useful explanation,
    # not a bare score restatement, and the endpoint always returns a full report.
    return build_templated_explanation(token_name, token_symbol, score_data)
