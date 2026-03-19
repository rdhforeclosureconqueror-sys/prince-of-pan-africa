from __future__ import annotations

from typing import Any

from app.services.leadership_question_map import QUESTION_MAP, ROLE_KEYS, ROLE_LABELS


def _safe_score(value: Any) -> float:
    try:
        parsed = float(value)
    except (ValueError, TypeError):
        parsed = 3.0
    return max(1.0, min(5.0, parsed))


def score_assessment(responses: list[Any]) -> dict[str, Any]:
    bounded = [_safe_score(value) for value in responses[: len(QUESTION_MAP)]]
    if len(bounded) < len(QUESTION_MAP):
        bounded.extend([3.0] * (len(QUESTION_MAP) - len(bounded)))

    raw_scores = {role: 0.0 for role in ROLE_KEYS}
    max_scores = {role: 0.0 for role in ROLE_KEYS}

    for i, answer in enumerate(bounded):
        weights = QUESTION_MAP[i]
        for role in ROLE_KEYS:
            weight = weights.get(role, 0.0)
            raw_scores[role] += answer * weight
            max_scores[role] += 5.0 * weight

    percentages = {
        role: round((raw_scores[role] / max_scores[role]) * 100, 2) if max_scores[role] else 0.0
        for role in ROLE_KEYS
    }

    ranked = sorted(percentages.items(), key=lambda item: item[1], reverse=True)
    roles = {
        "primary": ROLE_LABELS[ranked[0][0]],
        "secondary": ROLE_LABELS[ranked[1][0]],
        "growth": ROLE_LABELS[ranked[-2][0]],
        "shadow": ROLE_LABELS[ranked[-1][0]],
    }

    insights = {
        "primary": f"Your strongest strategic expression is {roles['primary']}. Use this as your execution anchor.",
        "shadow": f"Watch overuse patterns in {roles['shadow']}—this is where blind spots can emerge.",
        "growth": f"Deliberately train {roles['growth']} to increase leadership range and resilience.",
    }

    coaching = (
        f"Lead with {roles['primary']} and stabilize with {roles['secondary']}. "
        f"Develop {roles['growth']} intentionally while monitoring overreliance on {roles['shadow']}."
    )

    return {
        "responses": bounded,
        "percentages": percentages,
        "roles": roles,
        "insights": insights,
        "coaching": coaching,
    }
