import React, { useMemo } from "react";
import { FaFacebook, FaTiktok, FaInstagram, FaLink, FaCopy } from "react-icons/fa";

export default function SocialShare({ day, shareText = "", sharePack = "" }) {
  // ✅ Build a clean share link that preserves origin/path and sets ?day=
  const shareUrl = useMemo(() => {
    try {
      const u = new URL(window.location.href);

      // If caller provided day, force it into the URL
      if (typeof day === "number" && !Number.isNaN(day)) {
        u.searchParams.set("day", String(day));
      }

      return u.toString();
    } catch {
      return window.location.href;
    }
  }, [day]);

  const encodedUrl = encodeURIComponent(shareUrl);

  // ✅ Facebook share (works well)
  const facebookHref = `https://facebook.com/sharer/sharer.php?u=${encodedUrl}`;

  // ✅ TikTok / IG: link-share support is limited; we still provide link,
  // but the COPY buttons are the primary “share” mechanics.
  const tiktokHref = `https://www.tiktok.com/upload?lang=en`; // best practical entry point
  const instagramHref = `https://www.instagram.com/`; // IG doesn't accept ?url reliably

  const copyToClipboard = async (text) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      alert("Copied ✅");
    } catch {
      alert("Copy failed (browser blocked).");
    }
  };

  const canCopyText = !!shareText?.trim();
  const canCopyPack = !!sharePack?.trim();

  return (
    <div className="flex flex-wrap items-center gap-3 mt-6">
      {/* ✅ Copy Link */}
      <button
        type="button"
        onClick={() => copyToClipboard(shareUrl)}
        className="px-3 py-2 rounded-lg border border-yellow-700 bg-[#111] hover:bg-[#1a1a1a] text-yellow-200 flex items-center gap-2"
        title="Copy link"
      >
        <FaLink /> Copy Link
      </button>

      {/* ✅ Copy Answer */}
      <button
        type="button"
        disabled={!canCopyText}
        onClick={() => copyToClipboard(shareText)}
        className="px-3 py-2 rounded-lg border border-yellow-700 bg-[#111] hover:bg-[#1a1a1a] text-yellow-200 flex items-center gap-2 disabled:opacity-40"
        title="Copy latest answer"
      >
        <FaCopy /> Copy Answer
      </button>

      {/* ✅ Copy Q + A Pack */}
      <button
        type="button"
        disabled={!canCopyPack}
        onClick={() => copyToClipboard(sharePack)}
        className="px-3 py-2 rounded-lg border border-yellow-700 bg-[#111] hover:bg-[#1a1a1a] text-yellow-200 flex items-center gap-2 disabled:opacity-40"
        title="Copy Q + A pack"
      >
        <FaCopy /> Copy Q + A
      </button>

      {/* ✅ Facebook */}
      <a href={facebookHref} target="_blank" rel="noreferrer" title="Share to Facebook">
        <FaFacebook size={24} className="text-blue-500 hover:text-blue-400" />
      </a>

      {/* ✅ TikTok (open upload; user pastes text/link) */}
      <a href={tiktokHref} target="_blank" rel="noreferrer" title="Open TikTok (paste copied text in caption)">
        <FaTiktok size={24} className="text-gray-100 hover:text-pangreen" />
      </a>

      {/* ✅ Instagram (open IG; user pastes copied text/link) */}
      <a href={instagramHref} target="_blank" rel="noreferrer" title="Open Instagram (paste copied text in caption or bio)">
        <FaInstagram size={24} className="text-pangold hover:text-panred" />
      </a>

      {/* Small helper text (optional, lightweight) */}
      <span className="text-xs text-gray-400">
        Best workflow for TikTok/IG: Copy Answer → paste into caption. Copy Link → add in bio or comments.
      </span>
    </div>
  );
}
