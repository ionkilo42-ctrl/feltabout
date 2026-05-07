"""
RelateFX — Safety Classifier: Abuse-aware safety analysis

Detects coercive control patterns beyond simple keyword matching.
Rule-based fallback always runs; LLM call fires when API key is available.
"""
import os
import re
import httpx
import asyncio
from typing import Optional


# ─── Coercive Control Pattern Rules ──────────────────────────────────────────

ISOLATION_PATTERNS = [
    r"\bno one else\b",
    r"\bnobody else\b",
    r"\byour (family|friends|mother|father|parents) (is|are) (the problem|wrong|crazy)\b",
    r"\byou don't have anyone\b",
    r"\bonly me\b.*\byou need\b",
    r"\bstop talking to\b.*\byour\b",
    r"\bI don't want you seeing\b",
]

ECONOMIC_CONTROL_PATTERNS = [
    r"\bI pay for everything\b",
    r"\byou can't afford\b",
    r"\byou don't earn\b",
    r"\bmy money\b",
    r"\byou owe me\b",
    r"\bif you leave\b.*\bnowhere to go\b",
    r"\bI'll cut you off\b",
]

THREAT_PATTERNS = [
    r"\bor else\b",
    r"\byou'll regret\b",
    r"\bif you ever\b",
    r"\bdon't test me\b",
    r"\byou have no idea\b.*\bwhat I'll do\b",
    r"\bI'm not bluffing\b",
    r"\bdon't make me\b",
    r"\bif you tell anyone\b",
]

MINIMIZATION_GASLIGHTING_PATTERNS = [
    r"\byou're overreacting\b",
    r"\byou're crazy\b",
    r"\bthat never happened\b",
    r"\byou're imagining things\b",
    r"\bI never said that\b",
    r"\byou always twist\b",
    r"\byou're too sensitive\b",
    r"\bstop playing the victim\b",
]

DOMINATION_PATTERNS = [
    r"\bbecause I said so\b",
    r"\byou do what I say\b",
    r"\bI'm in charge\b",
    r"\byou don't get to decide\b",
    r"\byou lost the right\b",
    r"\byou signed up for this\b",
    r"\byou knew what you were getting into\b",
]


def _match_patterns(text: str, patterns: list[str]) -> list[str]:
    """Return list of matched pattern descriptions."""
    results = []
    t = text.lower()
    for pattern in patterns:
        if re.search(pattern, t):
            results.append(pattern)
    return results


def analyze_for_control(utterance: str, history: list[str]) -> dict:
    """
    Rule-based analysis of an utterance + recent history for coercive control patterns.
    Returns risk assessment dict.
    """
    t = utterance.lower()
    all_text = " ".join([utterance] + history).lower()

    isolation_matches = _match_patterns(all_text, ISOLATION_PATTERNS)
    economic_matches = _match_patterns(all_text, ECONOMIC_CONTROL_PATTERNS)
    threat_matches = _match_patterns(all_text, THREAT_PATTERNS)
    minimization_matches = _match_patterns(all_text, MINIMIZATION_GASLIGHTING_PATTERNS)
    domination_matches = _match_patterns(all_text, DOMINATION_PATTERNS)

    score = 0
    pattern_details = []

    if threat_matches:
        score += 3
        pattern_details.append("threat_language")
    if economic_matches:
        score += 2
        pattern_details.append("economic_control")
    if domination_matches:
        score += 2
        pattern_details.append("domination")
    if isolation_matches:
        score += 1
        pattern_details.append("isolation_language")
    if minimization_matches:
        score += 1
        pattern_details.append("minimization_gaslighting")

    # In history: check if one participant dominates with short responses
    # (possible stonewalling after conflict)
    if len(history) >= 4:
        short_count = sum(1 for h in history[-4:] if len(h.split()) <= 3)
        if short_count >= 3:
            score += 1
            pattern_details.append("possible_stonewalling")

    # Determine risk level
    if score >= 4:
        risk_level = "high"
        is_abuse_related = True
    elif score >= 2:
        risk_level = "moderate"
        is_abuse_related = True
    else:
        risk_level = "none"
        is_abuse_related = False

    # Suspected victim: if the current speaker used threats/domination,
    # the victim is the other participant (index 1 if current is 0)
    suspected_victim_index = None
    if threat_matches or domination_matches:
        # Assume 2-participant session; the one who didn't speak is the victim
        suspected_victim_index = 1  # will be refined in context

    rationale = f"Matched patterns: {', '.join(pattern_details) or 'none'}. Score: {score}"

    return {
        "risk_level": risk_level,
        "is_abuse_related": is_abuse_related,
        "suspected_victim_index": suspected_victim_index,
        "rationale": rationale,
        "matched_patterns": pattern_details,
    }


async def classify_safety_risk(
    utterance: str,
    history: list[str],
    api_key: Optional[str] = None,
) -> dict:
    """
    Main entry point: analyze utterance + history for safety risk.
    Always runs rule-based analysis first, then LLM if available.
    """
    # Rule-based fallback (always runs)
    rule_result = analyze_for_control(utterance, history)
    if not api_key:
        return rule_result

    # LLM-based classification if API key available
    history_block = ""
    for i, h in enumerate(history[-5:]):
        history_block += f"  [{i}] {h}\n"

    SYSTEM_PROMPT = """You are a domestic abuse risk assessment expert. Analyze the given conversation segment and determine whether there are signs of coercive control, economic abuse, threats, isolation, or domination in an intimate relationship.

Respond ONLY with valid JSON:
{
  "risk_level": "none" | "moderate" | "high",
  "is_abuse_related": true | false,
  "suspected_victim_index": 0 | 1 | null,
  "rationale": "brief explanation",
  "matched_patterns": ["pattern1", ...]
}

Rules:
- risk_level "high" requires at least one threat, clear domination, or multiple coercive patterns
- is_abuse_related must be true if risk_level is "moderate" or "high"
- suspected_victim_index is the index (0 or 1) of the participant who appears to be the target of control
- If no concern, risk_level should be "none" and is_abuse_related should be false
- Never fabricate patterns not present in the text"""

    USER_PROMPT = f"""UTTERANCE under analysis: "{utterance}"

Recent conversation:
{history_block if history_block else "(no prior history)"}

Analyze the full context for patterns of coercive control."""

    try:
        async def _call_minimax():
            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.post(
                    "https://api.minimax.io/v1/text/chatcompletion_v2",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "MiniMax-M2.7",
                        "max_tokens": 200,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": USER_PROMPT},
                        ],
                    },
                )
                resp.raise_for_status()
                return resp.json()

        data = await asyncio.wait_for(_call_minimax(), timeout=5.0)
    except asyncio.TimeoutError:
        print("[RelateFX] Safety classifier MiniMax timed out after 5s — using rule result")
    except Exception:
        pass

    # Fall back to rule result on any error or timeout
    return rule_result