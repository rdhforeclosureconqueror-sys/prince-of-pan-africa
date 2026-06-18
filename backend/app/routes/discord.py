from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Callable, Awaitable

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_permission
from app.services.discord_bridge import discord_bridge, format_black_economics_post, select_daily_fact, select_random_fact

router = APIRouter(prefix="/discord", tags=["Discord Bridge"])

REGIONS = ("north", "south", "east", "west")


def _require_internal_key(x_internal_api_key: str | None) -> bool:
    expected = os.getenv("INTERNAL_API_KEY", "").strip() or os.getenv("SIMBA_INTERNAL_API_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Internal Discord bridge key is not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API key")
    return True


def require_discord_admin_or_internal(permission_name: str = "admin:read_dashboard"):
    permission_dependency = require_permission(permission_name)

    def _require(request: Request, x_internal_api_key: str | None = Header(default=None, alias="X-Internal-Api-Key"), db: Session = Depends(get_db)):
        if x_internal_api_key:
            return _require_internal_key(x_internal_api_key)
        return permission_dependency(request, db)

    return _require


class DailyFactPayload(BaseModel):
    random_fact: bool = False
    include_sources: bool = False
    dry_run: bool = False


def _preview(content: str) -> str:
    return content[:300] + ("…" if len(content) > 300 else "")


def _response(*, ok: bool, action: str, target_channel: str | None, content: str = "", posted: bool = False, dry_run: bool = False, error: str | None = None) -> dict:
    return {
        "ok": ok,
        "success": ok,
        "action": action,
        "posted": posted,
        "dry_run": dry_run,
        "target_channel": target_channel,
        "message_preview": _preview(content) if content else "",
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _post_action(action: str, key: str, content_factory: Callable[[], str] | Callable[[], Awaitable[str]], *, dry_run: bool = False) -> dict:
    content = content_factory()
    if hasattr(content, "__await__"):
        content = await content  # type: ignore[assignment]
    target = discord_bridge.safe_channel_label(key)
    if dry_run:
        result = _response(ok=True, action=action, target_channel=target, content=content, posted=False, dry_run=True)
        await discord_bridge.log_action(action=action, target_channel=target, success=True, status="dry_run")
        return result
    posted = await discord_bridge.post_channel(key, str(content), action=action)
    return _response(ok=posted, action=action, target_channel=target, content=str(content), posted=posted, error=None if posted else "Discord post failed or channel/bot is not configured")


@router.get("/health")
def discord_bridge_health(_: object = Depends(require_discord_admin_or_internal())):
    return {
        "ok": True,
        "bot_configured": discord_bridge.configured,
        "gateway_listener": discord_bridge.gateway_status(),
        "channels": {key: bool(discord_bridge.channel_id(key)) for key in ("verification", "celebrations", "bot_log", "black_economics", *REGIONS)},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/black-economics/daily")
async def post_black_economics_daily(payload: DailyFactPayload | None = None, _: object = Depends(require_discord_admin_or_internal())):
    payload = payload or DailyFactPayload()
    fact = select_random_fact() if payload.random_fact else select_daily_fact()
    content = format_black_economics_post(fact, include_sources=payload.include_sources)
    return await _post_action("black_economics_daily", "black_economics", lambda: content, dry_run=payload.dry_run)


@router.post("/black-economics/dry-run")
async def dry_run_black_economics(_: object = Depends(require_discord_admin_or_internal())):
    fact = select_daily_fact()
    content = format_black_economics_post(fact, include_sources=False)
    return await _post_action("black_economics_dry_run", "black_economics", lambda: content, dry_run=True)


async def _regional(region: str) -> dict:
    content = discord_bridge.build_regional_prompt(region)
    return await _post_action(f"regional_{region}", region, lambda: content)


for _region in REGIONS:
    async def endpoint(region=_region, _: object = Depends(require_discord_admin_or_internal())):
        return await _regional(region)
    router.add_api_route(f"/regional/{_region}", endpoint, methods=["POST"], name=f"post_regional_{_region}")


@router.post("/test/verification-request")
async def test_verification_request(_: object = Depends(require_discord_admin_or_internal())):
    content = "🦁 **Test Verification Request**\nAdmin-triggered Discord bridge test. No STAR is awarded by this message."
    return await _post_action("test_verification_request", "verification", lambda: content)


@router.post("/test/celebration")
async def test_celebration(_: object = Depends(require_discord_admin_or_internal())):
    content = "🎉 **Test Celebration**\nSimba Bot can post to community celebrations."
    return await _post_action("test_celebration", "celebrations", lambda: content)


@router.post("/test/bot-log")
async def test_bot_log(_: object = Depends(require_discord_admin_or_internal())):
    content = "🛡️ **Test Bot Log Message**\nSafe admin-triggered bot-log test."
    return await _post_action("test_bot_log", "bot_log", lambda: content)


class RegionalPromptPayload(BaseModel):
    channel_id: str
    force: bool = False


@router.post("/regional/prompt")
async def post_regional_prompt(payload: RegionalPromptPayload, _: object = Depends(require_discord_admin_or_internal())):
    posted = await discord_bridge.maybe_post_regional_prompt(payload.channel_id, probability=1.0 if payload.force else 0.2)
    return {"ok": True, "posted": posted, "timestamp": datetime.now(timezone.utc).isoformat()}
