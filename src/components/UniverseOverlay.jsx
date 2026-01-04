// ✅ src/components/UniverseOverlay.jsx
import React, { useEffect } from "react";
import "../styles/universe.css";

export default function UniverseOverlay() {
  useEffect(() => {
    const canvas = document.getElementById("universe-canvas");
    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const stars = Array.from({ length: 200 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      z: Math.random() * width,
    }));

    function animate() {
      ctx.fillStyle = "rgba(0, 0, 15, 0.8)";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "rgba(255, 215, 0, 0.8)";

      for (let i = 0; i < stars.length; i++) {
        const s = stars[i];
        s.z -= 2;
        if (s.z <= 0) s.z = width;

        const k = 128.0 / s.z;
        const px = s.x * k + width / 2;
        const py = s.y * k + height / 2;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          const size = (1 - s.z / width) * 2;
          ctx.beginPath();
          ctx.arc(px, py, size, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <canvas id="universe-canvas"></canvas>;
}
