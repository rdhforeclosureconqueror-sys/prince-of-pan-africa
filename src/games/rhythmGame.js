const KEYS = ["A", "S", "D", "F"];
const REWARDS = ["🔥 Hot streak!", "⭐ Precision rising!", "🏆 Song key master!"];

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value) node.textContent = value;
  return node;
}

export function mountRhythmGame(container) {
  let score = 0;
  let attempts = 0;
  let targetKey = KEYS[Math.floor(Math.random() * KEYS.length)];

  const section = text("section", "brain-game-module");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Song Keys"), text("p", "", "Tap A/S/D/F to match the beat prompt."));

  const target = text("div", "brain-game-module__target", `Hit: ${targetKey}`);
  const stats = text("div", "brain-game-module__stats");
  const levelNode = text("p", "", "Level 1");
  const scoreNode = text("p", "", "Score 0");
  const accuracyNode = text("p", "", "Accuracy 0%");
  stats.append(levelNode, scoreNode, accuracyNode);

  const feedback = text("p", "brain-game-module__feedback", "Press the matching key to start your rhythm round.");
  section.append(header, target, stats, feedback);
  container.replaceChildren(section);

  const updateStats = () => {
    const level = Math.floor(score / 5) + 1;
    const accuracy = attempts ? Math.round((score / attempts) * 100) : 0;
    levelNode.textContent = `Level ${level}`;
    scoreNode.textContent = `Score ${score}`;
    accuracyNode.textContent = `Accuracy ${accuracy}%`;
    target.textContent = `Hit: ${targetKey}`;
  };

  const onKeyDown = (event) => {
    const pressed = event.key.toUpperCase();
    if (!KEYS.includes(pressed)) return;

    attempts += 1;
    if (pressed === targetKey) {
      score += 1;
      feedback.textContent = REWARDS[score % REWARDS.length];
    } else {
      feedback.textContent = `Missed beat. Wanted ${targetKey}, got ${pressed}.`;
    }

    targetKey = KEYS[Math.floor(Math.random() * KEYS.length)];
    updateStats();
  };

  window.addEventListener("keydown", onKeyDown);

  return () => {
    window.removeEventListener("keydown", onKeyDown);
    container.replaceChildren();
  };
}
