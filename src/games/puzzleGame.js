const PUZZLES = [
  { prompt: "I have keys but no locks. What am I?", answer: "keyboard" },
  { prompt: "What gets sharper the more you use your mind?", answer: "memory" },
  { prompt: "I connect thoughts but I am not a chain. What am I?", answer: "pattern" },
];

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value) node.textContent = value;
  return node;
}

export function mountPuzzleGame(container) {
  let index = 0;
  let score = 0;
  let attempts = 0;

  const section = text("section", "brain-game-module");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Puzzle"), text("p", "", "Decode quick brain riddles."));

  const prompt = text("p", "brain-game-module__prompt", PUZZLES[index].prompt);
  const recall = text("div", "brain-game-module__recall");
  const input = document.createElement("input");
  input.placeholder = "Your answer";
  const button = text("button", "", "Submit");
  button.type = "button";
  recall.append(input, button);

  const stats = text("div", "brain-game-module__stats");
  const levelNode = text("p", "", "Level 1");
  const scoreNode = text("p", "", "Score 0");
  const accuracyNode = text("p", "", "Accuracy 0%");
  stats.append(levelNode, scoreNode, accuracyNode);

  const feedback = text("p", "brain-game-module__feedback", "Solve to unlock rewards.");

  section.append(header, prompt, recall, stats, feedback);
  container.replaceChildren(section);

  const updateStats = () => {
    const level = Math.floor(score / 2) + 1;
    const accuracy = attempts ? Math.round((score / attempts) * 100) : 0;
    levelNode.textContent = `Level ${level}`;
    scoreNode.textContent = `Score ${score}`;
    accuracyNode.textContent = `Accuracy ${accuracy}%`;
    prompt.textContent = PUZZLES[index].prompt;
  };

  button.addEventListener("click", () => {
    const guess = input.value.trim().toLowerCase();
    if (!guess) return;

    attempts += 1;
    const active = PUZZLES[index];
    if (guess === active.answer) {
      score += 1;
      feedback.textContent = "🎁 Reward unlocked: Insight Badge";
      index = (index + 1) % PUZZLES.length;
      input.value = "";
    } else {
      feedback.textContent = `Not yet. Hint: answer starts with “${active.answer[0].toUpperCase()}”.`;
    }

    updateStats();
  });

  return () => {
    container.replaceChildren();
  };
}
