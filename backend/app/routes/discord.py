from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.services.discord_bridge import discord_bridge, format_black_economics_post, select_daily_fact, select_random_fact

router = APIRouter(prefix="/discord", tags=["Discord Bridge"])


def _require_internal_key(x_internal_api_key: str | None) -> None:
    expected = os.getenv("INTERNAL_API_KEY", "").strip() or os.getenv("SIMBA_INTERNAL_API_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Internal Discord bridge key is not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API key")


class DailyFactPayload(BaseModel):
    random_fact: bool = False
    include_sources: bool = False
    dry_run: bool = False


class RegionalPromptPayload(BaseModel):
    channel_id: str = Field(min_length=1, max_length=128)
    force: bool = False


@router.get("/health")
def discord_bridge_health():
    return {
        "ok": True,
        "bot_configured": discord_bridge.configured,
        "channels": {key: bool(discord_bridge.channel_id(key)) for key in ("verification", "celebrations", "bot_log", "black_economics", "north", "south", "east", "west")},
    }


@router.post("/black-economics/daily")
async def post_black_economics_daily(payload: DailyFactPayload, x_internal_api_key: str | None = Header(default=None, alias="X-Internal-Api-Key")):
    _require_internal_key(x_internal_api_key)
    fact = select_random_fact() if payload.random_fact else select_daily_fact()
    content = format_black_economics_post(fact, include_sources=payload.include_sources)
    if payload.dry_run:
        return {"ok": True, "posted": False, "dry_run": True, "content": content}
    posted = await discord_bridge.post_channel("black_economics", content)
    return {"ok": posted, "posted": posted}


@router.post("/regional/prompt")
async def post_regional_prompt(payload: RegionalPromptPayload, x_internal_api_key: str | None = Header(default=None, alias="X-Internal-Api-Key")):
    _require_internal_key(x_internal_api_key)
    posted = await discord_bridge.maybe_post_regional_prompt(payload.channel_id, probability=1.0 if payload.force else 0.2)
    return {"ok": True, "posted": posted}
