const SYMBOLS = ["🟥", "🟩", "🟨", "⬛", "◆", "●", "▲", "■"];

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value) node.textContent = value;
  return node;
}

function randomSequence(level) {
  const length = Math.min(3 + level, 8);
  return Array.from({ length }, () => SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)]);
}

export function mountSightGame(container) {
  let level = 1;
  let score = 0;
  let attempts = 0;
  let revealSeconds = 2;
  let sequence = randomSequence(1);
  let roundId = 0;
  let memoryTimer = null;

  const section = text("section", "brain-game-module");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Sight Memory"), text("p", "", "Set reveal time, memorize the stimulus, then recall."));

  const memoryPanel = text("div", "brain-game-module__memory");
  const controlWrap = text("div", "brain-game-module__memory-controls");
  const controlLabel = text("p", "brain-game-module__control-label", `Reveal time: ${revealSeconds}s`);
  const control = text("label", "brain-game-module__control");
  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = "1";
  slider.max = "5";
  slider.value = String(revealSeconds);
  control.append(slider);
  controlWrap.append(controlLabel, control);

  const stage = text("div", "brain-game-module__target");
  const answerArea = text("div", "brain-game-module__memory-answer");
  const stats = text("div", "brain-game-module__stats");
  const levelNode = text("p", "", "Level 1");
  const scoreNode = text("p", "", "Score 0");
  const accuracyNode = text("p", "", "Accuracy 0%");
  stats.append(levelNode, scoreNode, accuracyNode);
  const feedback = text("p", "brain-game-module__feedback", "Focus, then type symbols in order (no spaces).");

  memoryPanel.append(controlWrap, stage, answerArea);
  section.append(header, memoryPanel, stats, feedback);
  container.replaceChildren(section);

  const clearMemoryTimer = () => {
    if (memoryTimer) {
      clearTimeout(memoryTimer);
      memoryTimer = null;
    }
  };

  const updateStats = () => {
    const accuracy = attempts ? Math.round((score / attempts) * 100) : 0;
    levelNode.textContent = `Level ${level}`;
    scoreNode.textContent = `Score ${score}`;
    accuracyNode.textContent = `Accuracy ${accuracy}%`;
    controlLabel.textContent = `Reveal time: ${revealSeconds}s`;
  };

  const switchToRecall = () => {
    const recall = text("div", "brain-game-module__recall");
    const input = document.createElement("input");
    input.placeholder = "Type the pattern";
    const button = text("button", "", "Submit Recall");
    button.type = "button";
    recall.append(input, button);
    answerArea.replaceChildren(recall);

    button.addEventListener("click", () => {
      attempts += 1;
      const guess = input.value.trim();
      const answer = sequence.join("");
      if (guess === answer) {
        score += 1;
        level = Math.floor(score / 3) + 1;
        feedback.textContent = "✅ Sharp recall! Level advancing.";
      } else {
        feedback.textContent = `❌ Pattern was ${answer}. Reset and sharpen.`;
      }
      updateStats();
      startRound(level);
    });
  };

  const startRound = (roundLevel = level) => {
    clearMemoryTimer();
    roundId += 1;
    const currentRound = roundId;

    sequence = randomSequence(roundLevel);
    stage.textContent = sequence.join(" ");
    answerArea.replaceChildren();

    memoryTimer = setTimeout(() => {
      if (roundId !== currentRound) return;
      switchToRecall();
    }, revealSeconds * 1000);
  };

  slider.addEventListener("input", (event) => {
    revealSeconds = Number(event.target.value);
    updateStats();
  });

  updateStats();
  startRound(1);

  return () => {
    clearMemoryTimer();
    container.replaceChildren();
  };
}
