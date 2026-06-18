from __future__ import annotations

import asyncio

import pytest

from app.services.discord_bridge import (
    format_black_economics_post,
    load_black_economics_facts,
    select_daily_fact,
)


def test_black_economics_fact_post_uses_curated_seed_and_discussion_question():
    facts = load_black_economics_facts()
    fact = select_daily_fact()
    assert fact in facts

    post = format_black_economics_post(fact, include_sources=True)

    assert "Daily Black Economics Builder" in post
    assert "**History Fact:**" in post
    assert "**Practical Lesson:**" in post
    assert "**Discussion Question:**" in post
    assert "https://simbawaujamaa.com/library" in post


def test_discord_bridge_skips_posts_without_token(monkeypatch):
    from app.services.discord_bridge import DiscordBridge

    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.setenv("DISCORD_BLACK_ECONOMICS_CHANNEL_ID", "123")

    bridge = DiscordBridge()

    assert bridge.configured is False
    assert asyncio.run(bridge.post_daily_black_economics()) is False
