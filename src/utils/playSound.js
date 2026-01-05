// ✅ src/utils/playSound.js
export function playSound(type = "achievement") {
  const file = type === "motivate" ? "/sounds/motivate.mp3" : "/sounds/achievement.mp3";
  const audio = new Audio(file);
  audio.volume = 0.5;
  audio.play().catch(() => {});
}
