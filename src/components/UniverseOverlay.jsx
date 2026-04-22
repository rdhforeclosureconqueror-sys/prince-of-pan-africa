import React, { useEffect } from "react";
import "../styles/universe.css";

export default function UniverseOverlay() {
  useEffect(() => {
    const canvas = document.getElementById("universe-canvas");
    if (!canvas) return () => {};

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return () => {};

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const memoryClass = Number(navigator.deviceMemory || 4);
    const cpuClass = Number(navigator.hardwareConcurrency || 4);

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    const maxDim = Math.max(width, height);

    const performanceFactor = prefersReducedMotion ? 0.3 : Math.min(1, (memoryClass + cpuClass / 4) / 4);
    const baseStars = width < 768 ? 90 : 170;
    const starCount = Math.max(50, Math.floor(baseStars * performanceFactor));
    const speed = prefersReducedMotion ? 0.4 : 1.25;

    const stars = Array.from({ length: starCount }, () => ({
      x: (Math.random() - 0.5) * maxDim,
      y: (Math.random() - 0.5) * maxDim,
      z: Math.random() * maxDim,
    }));

    let frameId;
    function animate() {
      ctx.fillStyle = "rgba(2, 6, 18, 0.1)";
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < stars.length; i += 1) {
        const s = stars[i];
        s.z -= speed;
        if (s.z <= 1) s.z = maxDim;

        const perspective = 160 / s.z;
        const px = s.x * perspective + width / 2;
        const py = s.y * perspective + height / 2;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          const glow = 1 - s.z / maxDim;
          const size = Math.max(0.4, glow * 2.1);
          const alpha = Math.min(0.75, 0.12 + glow * 0.7);

          ctx.fillStyle = `rgba(255, 231, 160, ${alpha})`;
          ctx.beginPath();
          ctx.arc(px, py, size, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      frameId = requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      if (frameId) cancelAnimationFrame(frameId);
    };
  }, []);

  return <canvas id="universe-canvas" aria-hidden="true"></canvas>;
}
