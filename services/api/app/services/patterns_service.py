"""
Pattern Insights Service — Analyzes reflection history for recurring themes.

This is a read-only analysis service. It does NOT:
- Use LLM calls
- Store patterns in the database
- Give advice or recommendations
- Make diagnoses

Pattern types:
- recurring_emotion: Same emotion keyword appears across 2+ reflections
- recurring_need: Same need keyword appears across 2+ reflections
- conflict_context: Topic/keyword cluster across 2+ reflections

Language rule: always gentle, observational, never diagnostic.
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import Counter


# ─── Emotion / Need keyword dictionaries ──────────────────────────────────────

EMOTION_KEYWORDS = {
    "frustrated", "frustration", "angry", "anger", "hurt", "hurts",
    "sad", "sadness", "anxious", "anxiety", "worried", "worries",
    "scared", "fear", "dismissed", "dismiss", "ignored", "ignore",
    "overwhelmed", "overwhelm", "exhausted", "confused", "confusion",
    "hopeless", "hopelessness", "alone", "lonely", "rejected",
    "disappointed", "disappointment", "resentful", "resentment",
    "inadequate", "not enough", "invisible", "unseen",
}

NEEDS_KEYWORDS = {
    "clarity", "certainty", "understanding", "validation",
    "support", "supportive", "respect", "respectful",
    "recognition", "acknowledgment", "apology", "apologies",
    "space", "time", "control", "autonomy", "safety",
    "connection", "closeness", "intimacy", "affection",
    "fairness", "fair", "equality", "balance",
    "privacy", "independence", "freedom",
}

CONFLICT_CONTEXT_KEYWORDS = {
    "money": "Money and finances",
    "finances": "Money and finances",
    "budget": "Money and finances",
    "spending": "Money and finances",
    "debt": "Money and finances",
    "chores": "Home and chores",
    "cleaning": "Home and chores",
    "housework": "Home and chores",
    "tasks": "Home and chores",
    "kids": "Parenting",
    "children": "Parenting",
    "parenting": "Parenting",
    "work": "Work and career",
    "career": "Work and career",
    "job": "Work and career",
    "communications": "Communication and trust",
    "communication": "Communication and trust",
    "trust": "Communication and trust",
    "honesty": "Communication and trust",
    "family": "Family and in-laws",
    "in-laws": "Family and in-laws",
    "intimacy": "Intimacy and closeness",
    "sex": "Intimacy and closeness",
    "planning": "Planning and decisions",
    "schedule": "Planning and decisions",
    "future": "Planning and decisions",
}


# ─── Data models ────────────────────────────────────────────────────────────────

@dataclass
class PatternInsight:
    type: str  # recurring_emotion | recurring_need | conflict_context
    insight: str  # Human-readable, gentle observation
    occurrences: int  # How many reflections this appeared in
    examples: list[str] = field(default_factory=list)  # Specific instances
    confidence: str = "medium"  # low | medium | high
    # For emotion/need types
    keywords: list[str] = field(default_factory=list)
    # For conflict context
    context_label: Optional[str] = None


@dataclass
class PatternsResult:
    patterns: list[PatternInsight]
    total_reflections_analyzed: int
    requires_minimum: int = 3
    cache_ttl_seconds: int = 3600


# ─── Analysis logic ─────────────────────────────────────────────────────────────

def _normalize(text: str) -> list[str]:
    """Tokenize and normalize text to lowercase words."""
    if not text:
        return []
    # Split on whitespace, strip punctuation
    words = []
    for w in text.lower().split():
        w = w.strip(".,!?;:\"'()[]{}")
        if w and len(w) > 2:
            words.append(w)
    return words


def _detect_emotions(reflection_dict: dict) -> list[str]:
    """Extract emotion keywords from reflection fields."""
    fields = [
        reflection_dict.get("feelings", ""),
        reflection_dict.get("situation", ""),
        reflection_dict.get("interpretation", ""),
    ]
    words = []
    for f in fields:
        words.extend(_normalize(f))
    # Check which emotion keywords are present
    found = []
    for word in words:
        if word in EMOTION_KEYWORDS:
            found.append(word)
    return found


def _detect_needs(reflection_dict: dict) -> list[str]:
    """Extract need keywords from reflection fields."""
    fields = [
        reflection_dict.get("needs", ""),
        reflection_dict.get("desired_outcome", ""),
        reflection_dict.get("message_draft", ""),
    ]
    words = []
    for f in fields:
        words.extend(_normalize(f))
    found = []
    for word in words:
        if word in NEEDS_KEYWORDS:
            found.append(word)
    return found


def _detect_conflict_context(reflection_dict: dict) -> list[str]:
    """Extract conflict context keywords."""
    fields = [
        reflection_dict.get("situation", ""),
        reflection_dict.get("interpretation", ""),
    ]
    words = []
    for f in fields:
        words.extend(_normalize(f))
    found = []
    for word in words:
        if word in CONFLICT_CONTEXT_KEYWORDS:
            found.append(word)
    return found


def _build_insight(type: str, keyword_group: list[str], label: str, occurrences: int, total: int) -> PatternInsight:
    """Build a gentle insight string from detected keywords."""
    unique_keywords = list(set(keyword_group))

    if type == "recurring_emotion":
        # Group by emotional cluster
        emotion_clusters = {
            "rejected": ("Feeling dismissed or not valued", "dismissed, ignored, rejected, unheard"),
            "overwhelmed": ("Feeling stretched or overextended", "overwhelmed, exhausted, stretched"),
            "anxious": ("Feeling uncertain or worried", "anxious, worried, scared, fear"),
            "hurt": ("Feeling hurt or unseen", "hurt, alone, lonely, invisible"),
        }
        for cluster_key, (insight_text, examples) in emotion_clusters.items():
            if cluster_key in unique_keywords:
                confidence = "high" if occurrences >= 3 else "medium" if occurrences >= 2 else "low"
                return PatternInsight(
                    type=type,
                    insight=f"You've mentioned feeling {cluster_key} in several reflections.",
                    occurrences=occurrences,
                    keywords=unique_keywords[:5],
                    confidence=confidence,
                )
        # Fallback generic
        confidence = "high" if occurrences >= 3 else "medium" if occurrences >= 2 else "low"
        return PatternInsight(
            type=type,
            insight="You've mentioned some recurring emotional themes across your reflections.",
            occurrences=occurrences,
            keywords=unique_keywords[:5],
            confidence=confidence,
        )

    elif type == "recurring_need":
        need_clusters = {
            "clarity": "You often seem to want clarity before starting difficult conversations.",
            "respect": "Recognition and respect for your perspective appears to matter deeply to you.",
            "support": "You're often looking for support or partnership in challenging moments.",
            "space": "You sometimes need space or time before engaging in difficult topics.",
            "fairness": "Fairness and balance in shared responsibilities comes up for you.",
        }
        for cluster_key, insight_text in need_clusters.items():
            if cluster_key in unique_keywords:
                confidence = "high" if occurrences >= 3 else "medium" if occurrences >= 2 else "low"
                return PatternInsight(
                    type=type,
                    insight=insight_text,
                    occurrences=occurrences,
                    keywords=unique_keywords[:5],
                    confidence=confidence,
                )
        confidence = "high" if occurrences >= 3 else "medium" if occurrences >= 2 else "low"
        return PatternInsight(
            type=type,
            insight="Some patterns around what you need have been showing up across your reflections.",
            occurrences=occurrences,
            keywords=unique_keywords[:5],
            confidence=confidence,
        )

    else:  # conflict_context
        context_labels = set(CONFLICT_CONTEXT_KEYWORDS.get(k, k) for k in unique_keywords)
        label_str = " and ".join(sorted(context_labels)[:2])
        confidence = "low" if occurrences == 2 else "medium" if occurrences >= 3 else "low"
        prefix = "This may be showing up" if confidence == "low" else "These topics"
        return PatternInsight(
            type=type,
            insight=f"{prefix} tend to feel more emotionally charged — like {label_str} conversations.",
            occurrences=occurrences,
            keywords=unique_keywords[:5],
            context_label=label_str,
            confidence=confidence,
        )


def analyze_user_patterns(reflections: list[dict]) -> PatternsResult:
    """
    Analyze a list of reflection dicts for recurring themes.
    
    Each reflection dict should have decrypted field values:
    - situation, feelings, interpretation, needs, desired_outcome, message_draft
    
    Returns PatternsResult with pattern insights.
    Requires at least 3 completed reflections.
    """
    MINIMUM = 3
    
    if len(reflections) < MINIMUM:
        return PatternsResult(
            patterns=[],
            total_reflections_analyzed=len(reflections),
            requires_minimum=MINIMUM,
        )

    # Collect per-reflection detections
    emotion_per_ref = [_detect_emotions(r) for r in reflections]
    needs_per_ref = [_detect_needs(r) for r in reflections]
    context_per_ref = [_detect_conflict_context(r) for r in reflections]

    patterns: list[PatternInsight] = []

    # ── Recurring emotions ─────────────────────────────────────────────────────
    # Count how many reflections each emotion keyword appears in
    emotion_counts: Counter = Counter()
    for emotions in emotion_per_ref:
        seen_in_ref = set()
        for e in emotions:
            if e not in seen_in_ref:
                emotion_counts[e] += 1
                seen_in_ref.add(e)
    
    for emotion, count in emotion_counts.most_common(5):
        if count >= 2:  # At least 2 reflections
            # Collect example contexts (first word of situation field)
            examples = []
            for r, emotions in zip(reflections, emotion_per_ref):
                if emotion in emotions:
                    sit = r.get("situation", "")[:80]
                    if sit:
                        examples.append(sit)
            insight = _build_insight("recurring_emotion", [emotion], "", count, len(reflections))
            insight.examples = examples[:3]
            patterns.append(insight)

    # ── Recurring needs ────────────────────────────────────────────────────────
    needs_counts: Counter = Counter()
    for needs in needs_per_ref:
        seen_in_ref = set()
        for n in needs:
            if n not in seen_in_ref:
                needs_counts[n] += 1
                seen_in_ref.add(n)
    
    for need, count in needs_counts.most_common(5):
        if count >= 2:
            examples = []
            for r, needs in zip(reflections, needs_per_ref):
                if need in needs:
                    sit = r.get("situation", "")[:80]
                    if sit:
                        examples.append(sit)
            insight = _build_insight("recurring_need", [need], "", count, len(reflections))
            insight.examples = examples[:3]
            patterns.append(insight)

    # ── Conflict context ──────────────────────────────────────────────────────
    context_counts: Counter = Counter()
    for contexts in context_per_ref:
        seen_in_ref = set()
        for c in contexts:
            if c not in seen_in_ref:
                context_counts[c] += 1
                seen_in_ref.add(c)
    
    for context, count in context_counts.most_common(5):
        if count >= 2:
            examples = []
            for r, contexts in zip(reflections, context_per_ref):
                if context in contexts:
                    sit = r.get("situation", "")[:80]
                    if sit:
                        examples.append(sit)
            insight = _build_insight("conflict_context", [context], CONFLICT_CONTEXT_KEYWORDS.get(context, context) or "", count, len(reflections))
            insight.examples = examples[:3]
            patterns.append(insight)

    # Sort by confidence then occurrences
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    patterns.sort(key=lambda p: (confidence_order.get(p.confidence, 2), -p.occurrences))

    # Limit to top 5 patterns
    return PatternsResult(
        patterns=patterns[:5],
        total_reflections_analyzed=len(reflections),
        requires_minimum=MINIMUM,
    )