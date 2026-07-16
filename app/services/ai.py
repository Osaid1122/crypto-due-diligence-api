"""
AI explanation layer.

Takes the deterministic score + reasons and asks the model to produce a
human-readable verdict, top concerns, and recommended checks. The model is
explicitly instructed NOT to invent or adjust the score — only to explain it.
"""

import json
import httpx

from app.core.config import get_settings

SYSTEM_PROMPT = """You are a crypto risk analyst. You will be given a numeric risk score \
(0-100, already calculated by a deterministic rules engine), a list of specific technical \
reasons that contributed to that score, and any positive signals that were also detected.

Your job is ONLY to explain the score in plain English — you must NOT change, \
recalculate, or second-guess the numeric score itself. Treat the score, reasons, and \
positive signals as ground truth. Never mention a signal that wasn't provided to you, \
and never speculate about data you don't have. If confidence is below 0.5, say plainly \
that limited data was available rather than sounding confident.

Respond ONLY with a JSON object, no other text, no markdown fences, in this exact shape:
{
  "summary": "1-2 sentence plain-English verdict",
  "top_concerns": ["short phrase", "short phrase", "short phrase"],
  "recommended_checks": ["actionable next step", "actionable next step", "actionable next step"]
}

top_concerns should restate the most important reasons in plain language (max 3, empty list if none).
recommended_checks should be concrete things a user should verify before acting (max 3).
Keep every string under 20 words. Do not include disclaimers or hedging language."""


async def explain_score(token_name: str, token_symbol: str, score_data: dict) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return {
            "summary": f"{token_name} ({token_symbol}) scored {score_data['score']}/100 "
                       f"({score_data['risk_level']} risk) based on {len(score_data['reasons'])} flagged issue(s).",
            "top_concerns": score_data["reasons"][:3],
            "recommended_checks": [
                "Review the full technical_data for details on each flagged item.",
                "Verify contract ownership and liquidity lock status independently.",
                "Check recent holder and liquidity movements before transacting.",
            ],
        }

    user_content = json.dumps({
        "token_name": token_name,
        "token_symbol": token_symbol,
        "score": score_data["score"],
        "risk_level": score_data["risk_level"],
        "confidence": score_data["confidence"],
        "reasons": score_data["reasons"],
        "positive_signals": score_data.get("positive_signals", []),
    })

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(2):  # try once, retry once if the model returns malformed JSON
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
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                if attempt == 0:
                    continue  # retry once
                # Final fallback: templated explanation rather than a hard failure
                return {
                    "summary": f"{token_name} ({token_symbol}) scored {score_data['score']}/100 "
                               f"({score_data['risk_level']} risk).",
                    "top_concerns": score_data["reasons"][:3],
                    "recommended_checks": [
                        "Review the full technical_data for details on each flagged item.",
                        "Verify contract ownership and liquidity lock status independently.",
                    ],
                }
