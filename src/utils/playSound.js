// src/utils/playSound.js
const motivateSounds = [
  "/sounds/you_got_this.mp3",
  "/sounds/keep_pushing.mp3",
  "/sounds/excellent_work.mp3",
];

export function playSound(type = "achievement") {
  let file = "/sounds/achievement.mp3";
  if (type === "motivate") {
    file = motivateSounds[Math.floor(Math.random() * motivateSounds.length)];
  }
  const audio = new Audio(file);
  audio.volume = 0.5;
  audio.play().catch(() => {});
}
