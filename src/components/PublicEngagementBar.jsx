import React, { useState } from "react";
import { api } from "../api/api";

const CANONICAL_ORIGIN = "https://SimbaWaUjamaa.com";

function visitorId() {
  const key = "swu_visitor_id";
  let id = window.localStorage?.getItem(key);
  if (!id) {
    id = `visitor-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    window.localStorage?.setItem(key, id);
  }
  return id;
}

function canonicalShareTarget(path = window.location.pathname + window.location.search) {
  return `${CANONICAL_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

export default function PublicEngagementBar({ contentType, contentId, title, text = "Explore Simba wa Ujamaa", path }) {
  const [liked, setLiked] = useState(false);
  const [notice, setNotice] = useState("");

  async function share() {
    const fallbackUrl = canonicalShareTarget(path);
    let shareUrl = fallbackUrl;
    try {
      const created = await api("/audiobooks/shares", {
        method: "POST",
        body: JSON.stringify({ content_type: contentType, content_id: String(contentId), target_url: fallbackUrl, visitor_id: visitorId() }),
      });
      shareUrl = created.share_url || fallbackUrl;
    } catch (err) {
      console.info("[PublicEngagementBar] share tracking unavailable; using canonical link", err);
    }

    const payload = { title: title || "Simba wa Ujamaa", text, url: shareUrl };
    try {
      if (navigator.share) {
        await navigator.share(payload);
        setNotice("Share link created.");
      } else {
        await navigator.clipboard.writeText(shareUrl);
        setNotice("Share link copied.");
      }
    } catch (err) {
      if (err?.name !== "AbortError") setNotice("Share was not completed.");
    }
  }

  return (
    <div className="public-engagement-bar" aria-label="Public content actions">
      <button type="button" onClick={() => setLiked((value) => !value)}>{liked ? "❤️ Liked" : "♡ Like"}</button>
      <button type="button" disabled title="Coming soon">💬 Comment</button>
      <button type="button" disabled title="Coming soon">⭐ Save</button>
      <button type="button" onClick={share}>📤 Share</button>
      {notice && <span>{notice}</span>}
    </div>
  );
}
