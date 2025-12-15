import React from "react";
import { FaFacebook, FaTiktok, FaInstagram } from "react-icons/fa";

export default function SocialShare() {
  const shareUrl = window.location.href;
  return (
    <div className="flex gap-3 mt-6">
      <a href={`https://facebook.com/sharer/sharer.php?u=${shareUrl}`} target="_blank" rel="noreferrer">
        <FaFacebook size={24} className="text-blue-500 hover:text-blue-400" />
      </a>
      <a href={`https://www.tiktok.com/share?url=${shareUrl}`} target="_blank" rel="noreferrer">
        <FaTiktok size={24} className="text-gray-100 hover:text-pangreen" />
      </a>
      <a href={`https://www.instagram.com/?url=${shareUrl}`} target="_blank" rel="noreferrer">
        <FaInstagram size={24} className="text-pangold hover:text-panred" />
      </a>
    </div>
  );
}
