from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.models import Society, SocietyMembership, SocietyInstitutionalProfile, SocietyTrustTask, SocietyContainer
from app.services.institution_intelligence import generate_institution_intelligence
from app.services.opportunity_intelligence import generate_opportunity_intelligence
from app.services.society_intelligence import generate_society_intelligence

READ_ONLY_WARNING = "Read-only generated model: Predictive Intelligence does not write records, execute workflows, create appointments, assign members, send notifications, or persist predictions."


def _confidence_from_score(score: int, missing: list[str], evidence: list[str]) -> str:
    basis = round(mean([score, min(100, len(evidence) * 18), 100 - min(80, len(missing) * 12)]))
    return "substantial" if basis >= 75 else "developing" if basis >= 45 else "limited"


def _trend(score: int, missing: list[str]) -> dict[str, str]:
    if missing and score == 0:
        return {"label": "Unknown", "why": "No usable current or historical evidence exists for this forecast."}
    if score >= 85:
        return {"label": "Rapid Growth", "why": f"Current deterministic score is {score}, above the rapid-growth threshold of 85."}
    if score >= 70:
        return {"label": "Improving", "why": f"Current deterministic score is {score}, above the improving threshold of 70."}
    if score >= 45:
        return {"label": "Stable", "why": f"Current deterministic score is {score}, between 45 and 69; evidence does not justify improvement or decline."}
    if score >= 25:
        return {"label": "Declining", "why": f"Current deterministic score is {score}, below the healthy threshold of 45."}
    return {"label": "Rapid Decline", "why": f"Current deterministic score is {score}, below the rapid-decline threshold of 25."}


def _severity(probability: int) -> str:
    return "critical" if probability >= 85 else "high" if probability >= 70 else "moderate" if probability >= 45 else "low"


def _prediction(*, pid: str, title: str, typ: str, score: int, inverse: bool = False, timeframe: str = "30 days", evidence: list[str] | None = None, missing: list[str] | None = None, assumptions: list[str] | None = None, members: list[int] | None = None, roles: list[str] | None = None, societies: list[int] | None = None, institutions: list[int] | None = None, opportunities: list[str] | None = None) -> dict[str, Any]:
    score = max(0, min(100, round(score)))
    probability = 100 - score if inverse else score
    evidence = evidence or []
    missing = missing or []
    trend = _trend(score, missing)
    return {
        "id": pid,
        "title": title,
        "prediction_type": typ,
        "probability": probability,
        "confidence": _confidence_from_score(score, missing, evidence),
        "timeframe": timeframe,
        "trend": trend["label"],
        "trend_explanation": trend["why"],
        "severity": _severity(probability if inverse else 100 - probability if typ.endswith("risk") else probability),
        "evidence": evidence,
        "missing_evidence": missing,
        "assumptions": assumptions or ["No future action is assumed.", "Existing records remain the only evidence source.", "No machine learning, randomness, or external data is used."],
        "explanation": f"{title}: probability {probability}% from current score {score}. {trend['why']}",
        "related_members": members or [],
        "related_roles": roles or [],
        "related_societies": societies or [],
        "related_institutions": institutions or [],
        "related_opportunities": opportunities or [],
        "requires_manual_review": True,
        "no_workflow_executed": True,
    }


def generate_predictive_intelligence(db: Session, *, society_id: int | None = None, include_debug: bool = False) -> dict[str, Any]:
    societies = db.query(Society).filter(Society.id == society_id).all() if society_id else db.query(Society).all()
    if society_id and not societies:
        raise ValueError("Society not found")
    predictions: list[dict[str, Any]] = []
    debug: dict[str, Any] = {"societies": []}
    for society in societies:
        si = generate_society_intelligence(db, society_id=society.id, include_debug=include_debug)
        ii = generate_institution_intelligence(db, institution_id=society.id, include_debug=include_debug)
        oi = generate_opportunity_intelligence(db, society_id=society.id, include_debug=include_debug)
        s = si["scores"]
        memberships = db.query(SocietyMembership).filter_by(society_id=society.id, status="active").all()
        profiles = db.query(SocietyInstitutionalProfile).filter_by(society_id=society.id).all()
        tasks = db.query(SocietyTrustTask).filter_by(society_id=society.id).all()
        containers = db.query(SocietyContainer).filter_by(society_id=society.id).all()
        member_ids = [m.user_id for m in memberships]
        base = {"societies": [society.id], "institutions": [society.id]}
        mk = lambda k: s[k]
        predictions += [
            _prediction(pid=f"society-{society.id}-member-growth", title="Member growth likely if evidence remains on track", typ="member_growth", score=mk("member_growth")["score"], evidence=mk("member_growth")["evidence"], missing=mk("member_growth")["missing_evidence"], members=member_ids, **base),
            _prediction(pid=f"society-{society.id}-leadership-readiness", title="Leadership readiness forecast", typ="leadership_readiness", score=mk("leadership_coverage")["score"], evidence=mk("leadership_coverage")["evidence"], missing=mk("leadership_coverage")["missing_evidence"], members=member_ids, roles=si.get("missing_roles", []), **base),
            _prediction(pid=f"society-{society.id}-assessment-completion", title="Assessment completion likelihood", typ="assessment_completion_likelihood", score=mk("assessment_completion")["score"], evidence=mk("assessment_completion")["evidence"], missing=mk("assessment_completion")["missing_evidence"], members=member_ids, **base),
            _prediction(pid=f"society-{society.id}-participation-trend", title="Participation trend forecast", typ="participation_trend", score=mk("participation_score")["score"], evidence=mk("participation_score")["evidence"], missing=mk("participation_score")["missing_evidence"], members=member_ids, **base),
            _prediction(pid=f"society-{society.id}-trust-trend", title="Trust trend forecast", typ="trust_trend", score=mk("trust_score")["score"], evidence=mk("trust_score")["evidence"], missing=mk("trust_score")["missing_evidence"], **base),
            _prediction(pid=f"society-{society.id}-knowledge-growth", title="Knowledge growth forecast", typ="knowledge_growth", score=mk("knowledge_coverage")["score"], evidence=mk("knowledge_coverage")["evidence"], missing=mk("knowledge_coverage")["missing_evidence"], **base),
            _prediction(pid=f"society-{society.id}-business-ready-30", title="Business readiness within 30 days", typ="business_readiness", score=mk("business_readiness")["score"], timeframe="30 days", evidence=mk("business_readiness")["evidence"], missing=mk("business_readiness")["missing_evidence"], members=[p.user_id for p in profiles if p.current_projects_json], **base),
            _prediction(pid=f"society-{society.id}-burnout-risk", title="Burnout risk if volunteer capacity stays low", typ="burnout_risk", score=mk("volunteer_capacity")["score"], inverse=True, evidence=mk("volunteer_capacity")["evidence"], missing=mk("volunteer_capacity")["missing_evidence"], members=member_ids, **base),
            _prediction(pid=f"society-{society.id}-container-failure", title="Container failure risk", typ="container_failure_risk", score=mk("first_100_days_progress")["score"], inverse=True, evidence=mk("first_100_days_progress")["evidence"], missing=mk("first_100_days_progress")["missing_evidence"], **base),
            _prediction(pid=f"society-{society.id}-institution-stability", title="Institution stability forecast", typ="institution_stability", score=ii["institution_health"]["score"], evidence=ii["institution_health"].get("evidence", []), missing=ii.get("missing_evidence", []), **base),
            _prediction(pid=f"society-{society.id}-opportunity-urgency", title="Opportunities becoming urgent", typ="opportunity_urgency", score=oi["overall_priority"]["score"], evidence=oi.get("evidence", []), missing=oi.get("missing_evidence", []), opportunities=[o["id"] for o in oi.get("opportunities", [])[:8]], **base),
        ]
        if include_debug:
            debug["societies"].append({"society_intelligence": si, "institution_intelligence": ii, "opportunity_intelligence": oi, "containers_read": [c.id for c in containers], "tasks_read": [t.id for t in tasks]})
    predictions.sort(key=lambda p: (-p["probability"], p["prediction_type"], p["id"]))
    improving = [p for p in predictions if p["trend"] in {"Improving", "Rapid Growth"}]
    declining = [p for p in predictions if p["trend"] in {"Declining", "Rapid Decline"}]
    risks = [p for p in predictions if "risk" in p["prediction_type"] or p["severity"] in {"high", "critical"}]
    return {"ok": True, "prediction_model": "deterministic_read_only", "warnings": [READ_ONLY_WARNING, "All predictions require human review; no workflow was executed."], "overall_forecast": {"societies_reviewed": len(societies), "prediction_count": len(predictions), "confidence": _confidence_from_score(round(mean([p["probability"] for p in predictions])) if predictions else 0, [], predictions[:5])}, "predictions": predictions, "dashboard": {"high_confidence_predictions": [p for p in predictions if p["confidence"] == "substantial"], "improving_trends": improving, "declining_trends": declining, "emerging_risks": risks, "future_opportunities": [p for p in predictions if "opportunity" in p["prediction_type"]], "leadership_forecast": [p for p in predictions if "leadership" in p["prediction_type"]], "institution_forecast": [p for p in predictions if "institution" in p["prediction_type"]], "business_forecast": [p for p in predictions if "business" in p["prediction_type"]], "trust_forecast": [p for p in predictions if "trust" in p["prediction_type"]], "container_forecast": [p for p in predictions if "container" in p["prediction_type"]]}, "debug": debug if include_debug else None}
