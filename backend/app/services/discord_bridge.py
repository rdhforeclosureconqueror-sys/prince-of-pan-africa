from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import websockets
except ModuleNotFoundError:  # pragma: no cover
    websockets = None

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - dependency is installed in production requirements
    httpx = None

LABOR_CATEGORIES = {
    "learning": "Learning Labor",
    "community": "Community Labor",
    "growth": "Growth Labor",
    "builder": "Builder Labor",
}
VERIFICATIONS_REQUIRED = 3

logger = logging.getLogger("simba.discord")

DISCORD_API_BASE = "https://discord.com/api/v10"
LIBRARY_URL = "https://simbawaujamaa.com/library"

CHANNEL_ENV = {
    "welcome": "DISCORD_WELCOME_CHANNEL_ID",
    "verification": "DISCORD_VERIFY_CHANNEL_ID",
    "announcements": "DISCORD_ANNOUNCEMENTS_CHANNEL_ID",
    "celebrations": "DISCORD_CELEBRATIONS_CHANNEL_ID",
    "bot_log": "DISCORD_BOT_LOG_CHANNEL_ID",
    "north": "DISCORD_NORTH_CHANNEL_ID",
    "south": "DISCORD_SOUTH_CHANNEL_ID",
    "east": "DISCORD_EAST_CHANNEL_ID",
    "west": "DISCORD_WEST_CHANNEL_ID",
    "black_economics": "DISCORD_BLACK_ECONOMICS_CHANNEL_ID",
}

REGIONAL_CHANNELS = {
    os.getenv("DISCORD_NORTH_CHANNEL_ID", "").strip(): "north",
    os.getenv("DISCORD_SOUTH_CHANNEL_ID", "").strip(): "south",
    os.getenv("DISCORD_EAST_CHANNEL_ID", "").strip(): "east",
    os.getenv("DISCORD_WEST_CHANNEL_ID", "").strip(): "west",
}
REGIONAL_CHANNELS.pop("", None)

REGIONAL_PROMPTS = {
    "north": "Northern Black communities built churches, schools, mutual-aid networks, newspapers, and business corridors even under pressure. Which institution should your city rebuild first?",
    "south": "New Orleans and the wider South hold deep Black cultural and economic history, from mutual-aid societies to Black business networks, land cooperatives, freedom schools, and community institutions. Which Black community institution in your city do you think should be rebuilt first?",
    "east": "Eastern Black communities organized docks, churches, publishers, schools, and neighborhood economies into durable freedom networks. What would you want young people in your area to learn from that legacy?",
    "west": "Western Black communities built newspapers, churches, civic clubs, and business districts while creating new migration-era freedom spaces. What kind of cooperative business would serve your region now?",
}

REGIONAL_TRIGGER_TERMS = ("i’m from", "i'm from", "i am from", "from", "test", "new orleans", "atlanta", "houston", "memphis", "detroit", "chicago", "philadelphia", "baltimore", "oakland", "los angeles")

BLACK_ECONOMICS_FACTS_FILE = "black_economics_365_facts.json"
BLACK_ECONOMICS_SOURCES_FILE = "black_economics_sources.json"

REQUIRED_FACT_FIELDS = {"id", "title", "discord_post", "source_key"}


def _validate_black_economics_fact(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    if not REQUIRED_FACT_FIELDS.issubset(item):
        return None
    if not str(item.get("discord_post", "")).strip():
        return None
    return item


def _extract_black_economics_facts(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        data = data.get("facts", [])
    if not isinstance(data, list):
        return []
    return [fact for item in data if (fact := _validate_black_economics_fact(item))]


def validate_black_economics_dataset(facts: list[dict[str, Any]], sources: dict[str, Any]) -> None:
    if len(facts) < 365:
        raise ValueError("Black Economics dataset must contain at least 365 usable daily posts")
    missing_sources = sorted({str(fact["source_key"]) for fact in facts if str(fact["source_key"]) not in sources})
    if missing_sources:
        raise ValueError(f"Black Economics dataset references missing source keys: {', '.join(missing_sources[:5])}")


def _data_dir() -> Path:
    return Path(os.getenv("BLACK_ECONOMICS_FACT_DIR", Path(__file__).resolve().parents[2] / "data"))


def load_black_economics_facts() -> list[dict[str, Any]]:
    path = _data_dir() / BLACK_ECONOMICS_FACTS_FILE
    with path.open("r", encoding="utf-8") as handle:
        facts = _extract_black_economics_facts(json.load(handle))
    validate_black_economics_dataset(facts, load_black_economics_sources())
    return facts


def load_black_economics_sources() -> dict[str, Any]:
    path = _data_dir() / BLACK_ECONOMICS_SOURCES_FILE
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {str(item.get("id")): item for item in data if isinstance(item, dict) and item.get("id")}
    if isinstance(data, dict):
        return data
    raise ValueError("Black Economics sources must be a JSON object or list of source objects")


def select_daily_fact(day: datetime | None = None) -> dict[str, Any]:
    facts = load_black_economics_facts()
    key = (day or datetime.now(timezone.utc)).date().isoformat()
    index = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % len(facts)
    return facts[index]


def select_random_fact() -> dict[str, Any]:
    return random.choice(load_black_economics_facts())


def format_black_economics_post(fact: dict[str, Any], *, include_sources: bool = False) -> str:
    lines = [str(fact["discord_post"]).strip()]
    if include_sources:
        sources = load_black_economics_sources()
        source = sources.get(str(fact.get("source_key")), {})
        citation = source.get("citation") or source.get("title")
        if citation:
            lines.append(f"📚 Source: {citation}")
    return "\n\n".join(lines)


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class DiscordBridge:
    def __init__(self) -> None:
        self.token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        self.guild_id = os.getenv("DISCORD_GUILD_ID", "").strip()
        self._gateway_running = False
        self._last_regional_reply: dict[str, float] = {}

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def channel_id(self, key: str) -> str | None:
        value = os.getenv(CHANNEL_ENV[key], "").strip()
        return value or None

    def safe_channel_label(self, key: str) -> str:
        channel_id = self.channel_id(key)
        return f"{key} ({channel_id[-4:]})" if channel_id else key

    async def log_action(self, *, action: str, target_channel: str, success: bool, status: str, error: str | None = None) -> bool:
        timestamp = datetime.now(timezone.utc).isoformat()
        safe_error = (error or "").replace(self.token, "[redacted]") if self.token else (error or "")
        logger.info("Discord action=%s target_channel=%s success=%s status=%s timestamp=%s error=%s", action, target_channel, success, status, timestamp, safe_error)
        if action == "bot_log_post":
            return True
        if not self.configured or not self.channel_id("bot_log"):
            return False
        content = f"🛡️ **Simba Bot action**\naction: `{action}`\ntarget: `{target_channel}`\nsuccess: `{success}`\nstatus: `{status}`\ntime: `{timestamp}`"
        if safe_error:
            content += f"\nerror: `{safe_error[:300]}`"
        return await self.post_channel("bot_log", content, action="bot_log_post")

    async def post_channel(self, key: str, content: str, *, allowed_mentions: dict | None = None, action: str = "post_channel") -> bool:
        channel_id = self.channel_id(key)
        if not self.configured or not channel_id:
            logger.info("Discord post skipped; bot token or channel %s is not configured", key)
            await self.log_action(action=action, target_channel=self.safe_channel_label(key), success=False, status="not_configured")
            return False
        if httpx is None:
            logger.warning("Discord post failed for channel %s: httpx unavailable", key)
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                    headers={"Authorization": f"Bot {self.token}", "Content-Type": "application/json"},
                    json={"content": content[:1900], "allowed_mentions": allowed_mentions or {"parse": []}},
                )
                response.raise_for_status()
            await self.log_action(action=action, target_channel=self.safe_channel_label(key), success=True, status=str(response.status_code))
            return True
        except Exception as exc:
            logger.warning("Discord post failed for channel %s: %s", key, exc.__class__.__name__)
            await self.log_action(action=action, target_channel=self.safe_channel_label(key), success=False, status="exception", error=exc.__class__.__name__)
            return False

    async def log_error(self, message: str) -> bool:
        if not self.configured or not self.channel_id("bot_log"):
            return False
        safe = message.replace(self.token, "[redacted]") if self.token else message
        if httpx is None:
            logger.warning("Discord bot-log post skipped: httpx unavailable")
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{DISCORD_API_BASE}/channels/{self.channel_id('bot_log')}/messages",
                    headers={"Authorization": f"Bot {self.token}", "Content-Type": "application/json"},
                    json={"content": f"⚠️ **Simba Bot diagnostic**\n{safe[:1600]}", "allowed_mentions": {"parse": []}},
                )
            return True
        except Exception:
            logger.warning("Discord bot-log post failed")
            return False

    async def post_verification_request(self, activity: Any, display_name: str) -> bool:
        meta = _value(activity, "metadata_", {}) or _value(activity, "metadata", {}) or {}
        activity_type = str(_value(activity, "activity_type", "community_labor")).replace("_", " ").title()
        points = _value(activity, "participation_points", 0)
        request_id = _value(activity, "id")
        content = "\n".join([
            "🦁 **New Community Labor Exchange Verification Request**",
            f"**Member:** {display_name}",
            f"**Labor Category:** {meta.get('labor_category_label') or LABOR_CATEGORIES.get(meta.get('labor_category'), 'Community Labor')}",
            f"**Activity Type:** {activity_type}",
            f"**Reward Rules:** {VERIFICATIONS_REQUIRED} community confirmations unlock {points} STAR for the contributor. First verifier earns 3 STAR; follow-up verifiers earn 1 STAR.",
            "**Instructions:** Review the proof, confirm only honest completed work on SimbaWaUjamaa.com, and remember: Discord helps discuss verification, but the website awards STAR and Community Trust.",
            f"**Request ID:** {request_id}",
        ])
        if meta.get("proof_url"):
            content += f"\n**Proof:** {meta['proof_url']}"
        return await self.post_channel("verification", content)

    async def post_verification_completion(self, activity: Any, display_name: str, trust_score: int | None = None) -> bool:
        trust_line = f" Community Trust is now {trust_score}." if trust_score is not None else " Community Trust has been updated by the backend."
        activity_type = str(_value(activity, "activity_type", "community labor")).replace("_", " ")
        star_award = _value(activity, "star_award", 0)
        content = f"🎉 **Community Labor Verified!**\n\n{display_name}'s {activity_type} received {VERIFICATIONS_REQUIRED} confirmations. {star_award} STAR awarded by SimbaWaUjamaa.com.{trust_line}"
        return await self.post_channel("celebrations", content)

    async def post_daily_black_economics(self, *, include_sources: bool = False, random_fact: bool = False) -> bool:
        fact = select_random_fact() if random_fact else select_daily_fact()
        return await self.post_channel("black_economics", format_black_economics_post(fact, include_sources=include_sources))

    def build_regional_prompt(self, region: str) -> str:
        return f"🦁 **Welcome to the {region.title()} Region — Black Mega Cities Reflection**\n\n{REGIONAL_PROMPTS[region]}\n\n📚 Explore more: {LIBRARY_URL}"

    async def maybe_post_regional_prompt(self, channel_id: str, *, probability: float = 0.2) -> bool:
        region = REGIONAL_CHANNELS.get(str(channel_id))
        if not region or random.random() > probability:
            return False
        return await self.post_channel(region, self.build_regional_prompt(region), action=f"regional_trigger_{region}")

    def gateway_status(self) -> dict[str, Any]:
        return {
            "enabled": os.getenv("DISCORD_GATEWAY_LISTENER_ENABLED", "true").lower() not in {"0", "false", "no"},
            "running": self._gateway_running,
            "websockets_available": websockets is not None,
        }

    def should_respond_to_regional_message(self, payload: dict[str, Any]) -> tuple[bool, str | None]:
        if payload.get("author", {}).get("bot"):
            return False, None
        channel_id = str(payload.get("channel_id", ""))
        region = REGIONAL_CHANNELS.get(channel_id)
        content = str(payload.get("content", "")).lower()
        if not region or not any(term in content for term in REGIONAL_TRIGGER_TERMS):
            return False, region
        now = time.monotonic()
        if now - self._last_regional_reply.get(channel_id, 0) < int(os.getenv("DISCORD_REGIONAL_TRIGGER_COOLDOWN_SECONDS", "60")):
            return False, region
        self._last_regional_reply[channel_id] = now
        return True, region

    async def handle_gateway_message_create(self, payload: dict[str, Any]) -> bool:
        should_reply, region = self.should_respond_to_regional_message(payload)
        if not should_reply or not region:
            return False
        return await self.post_channel(region, self.build_regional_prompt(region), action=f"regional_live_trigger_{region}")

    async def run_gateway_listener(self) -> None:
        if os.getenv("DISCORD_GATEWAY_LISTENER_ENABLED", "true").lower() in {"0", "false", "no"}:
            logger.info("Discord gateway listener disabled by DISCORD_GATEWAY_LISTENER_ENABLED")
            return
        if not self.configured or websockets is None:
            logger.warning("Discord gateway listener unavailable: token_configured=%s websockets_available=%s", self.configured, websockets is not None)
            return
        self._gateway_running = True
        while True:
            try:
                async with websockets.connect("wss://gateway.discord.gg/?v=10&encoding=json") as ws:
                    hello = json.loads(await ws.recv())
                    interval = hello.get("d", {}).get("heartbeat_interval", 45000) / 1000
                    await ws.send(json.dumps({"op": 2, "d": {"token": self.token, "intents": 33280, "properties": {"os": "linux", "browser": "simba", "device": "simba"}}}))

                    async def heartbeat():
                        while True:
                            await asyncio.sleep(interval)
                            await ws.send(json.dumps({"op": 1, "d": None}))

                    heartbeat_task = asyncio.create_task(heartbeat())
                    try:
                        async for raw in ws:
                            event = json.loads(raw)
                            if event.get("t") == "MESSAGE_CREATE":
                                await self.handle_gateway_message_create(event.get("d", {}))
                    finally:
                        heartbeat_task.cancel()
            except Exception as exc:
                self._gateway_running = False
                logger.warning("Discord gateway listener reconnecting after %s", exc.__class__.__name__)
                await self.log_action(action="gateway_listener", target_channel="regional_channels", success=False, status="reconnect", error=exc.__class__.__name__)
                await asyncio.sleep(30)
                self._gateway_running = True


discord_bridge = DiscordBridge()

async def run_daily_black_economics_loop() -> None:
    if os.getenv("DISCORD_DAILY_FACT_LOOP_ENABLED", "true").lower() in {"0", "false", "no"}:
        return
    while True:
        now = datetime.now(timezone.utc)
        if now.hour == int(os.getenv("DISCORD_DAILY_FACT_UTC_HOUR", "14")):
            await discord_bridge.post_daily_black_economics(include_sources=os.getenv("DISCORD_FACT_DEBUG_SOURCES", "false").lower() == "true")
            await asyncio.sleep(3600)
        await asyncio.sleep(900)
