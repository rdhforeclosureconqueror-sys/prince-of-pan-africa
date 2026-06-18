from __future__ import annotations

import asyncio

import pytest

from app.services.discord_bridge import (
    format_black_economics_post,
    load_black_economics_facts,
    select_daily_fact,
)


def test_black_economics_fact_post_uses_official_curated_dataset():
    facts = load_black_economics_facts()
    fact = select_daily_fact()
    assert len(facts) >= 365
    assert fact in facts
    assert "discord_post" in fact
    assert "source_key" in fact

    post = format_black_economics_post(fact, include_sources=True)

    assert "Black Economics Fact #" in post
    assert "💡 Try it today:" in post
    assert "📚 Source:" in post


def test_discord_bridge_skips_posts_without_token(monkeypatch):
    from app.services.discord_bridge import DiscordBridge

    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.setenv("DISCORD_BLACK_ECONOMICS_CHANNEL_ID", "123")

    bridge = DiscordBridge()

    assert bridge.configured is False
    assert asyncio.run(bridge.post_daily_black_economics()) is False


def test_regional_trigger_detects_new_orleans_south_message(monkeypatch):
    from app.services import discord_bridge as module
    from app.services.discord_bridge import DiscordBridge

    monkeypatch.setenv("DISCORD_SOUTH_CHANNEL_ID", "south123")
    monkeypatch.setitem(module.REGIONAL_CHANNELS, "south123", "south")
    bridge = DiscordBridge()

    should_reply, region = bridge.should_respond_to_regional_message({
        "channel_id": "south123",
        "content": "test, I’m from New Orleans",
        "author": {"bot": False},
    })

    assert should_reply is True
    assert region == "south"
    assert "Welcome to the South Region" in bridge.build_regional_prompt("south")
    assert "New Orleans" in bridge.build_regional_prompt("south")


def test_regional_trigger_ignores_bot_messages(monkeypatch):
    from app.services import discord_bridge as module
    from app.services.discord_bridge import DiscordBridge

    monkeypatch.setitem(module.REGIONAL_CHANNELS, "south123", "south")
    bridge = DiscordBridge()

    should_reply, region = bridge.should_respond_to_regional_message({
        "channel_id": "south123",
        "content": "I am from New Orleans",
        "author": {"bot": True},
    })

    assert should_reply is False
    assert region is None
