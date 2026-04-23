const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ";
const DIGITS = "0123456789";
const COLOR_POOL = [
  { name: "Black", value: "#111827", isDefault: true },
  { name: "Red", value: "#cf2f2f" },
  { name: "Blue", value: "#2d61d6" },
  { name: "Green", value: "#1d8a4a" },
  { name: "Purple", value: "#7a3fd1" },
];

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function pickRandom(list) {
  return list[Math.floor(Math.random() * list.length)];
}

function shuffle(list) {
  return [...list].sort(() => Math.random() - 0.5);
}

function randomLetter() {
  return ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
}

function randomDigit() {
  return DIGITS[Math.floor(Math.random() * DIGITS.length)];
}

function ordinal(position) {
  const mod10 = position % 10;
  const mod100 = position % 100;
  if (mod10 === 1 && mod100 !== 11) return `${position}st`;
  if (mod10 === 2 && mod100 !== 12) return `${position}nd`;
  if (mod10 === 3 && mod100 !== 13) return `${position}rd`;
  return `${position}th`;
}

function buildCharacterLine(level) {
  const totalCount = Math.max(3, Math.min(9, 3 + Math.floor((level - 1) / 2)));
  const lettersCount = Math.max(1, Math.floor(totalCount / 2));
  const digitsCount = totalCount - lettersCount;

  const tokens = [];
  for (let i = 0; i < lettersCount; i += 1) tokens.push({ value: randomLetter(), kind: "letter" });
  for (let i = 0; i < digitsCount; i += 1) tokens.push({ value: randomDigit(), kind: "number" });

  const ordered = shuffle(tokens);
  const colorableIndexes = shuffle(ordered.map((_, index) => index));
  const coloredCount = Math.min(Math.max(1, Math.floor(totalCount / 3)), 3);
  const coloredIndexes = new Set(colorableIndexes.slice(0, coloredCount));

  return ordered.map((token, index) => {
    const color = coloredIndexes.has(index) ? pickRandom(COLOR_POOL.filter((entry) => !entry.isDefault)) : COLOR_POOL[0];
    return {
      ...token,
      position: index + 1,
      colorName: color.name,
      colorValue: color.value,
    };
  });
}

function buildQuestions(memoryLine) {
  const questions = [];
  const byPosition = memoryLine;
  const letters = memoryLine.filter((entry) => entry.kind === "letter");
  const numbers = memoryLine.filter((entry) => entry.kind === "number");

  const first = byPosition[0];
  const third = byPosition[2] || byPosition[byPosition.length - 1];
  const last = byPosition[byPosition.length - 1];

  questions.push({
    prompt: "What was the first character?",
    answer: first.value,
    choices: shuffle([first.value, randomLetter(), randomDigit()]),
  });

  questions.push({
    prompt: `What was the ${ordinal(third.position)} character?`,
    answer: third.value,
    choices: shuffle([third.value, randomLetter(), randomDigit()]),
  });

  if (letters.length > 0) {
    const firstLetter = letters[0];
    questions.push({
      prompt: "What was the first letter?",
      answer: firstLetter.value,
      choices: shuffle([firstLetter.value, randomLetter(), randomLetter()]),
    });
  }

  if (numbers.length > 0) {
    const lastNumber = numbers[numbers.length - 1];
    questions.push({
      prompt: "What was the last number?",
      answer: lastNumber.value,
      choices: shuffle([lastNumber.value, randomDigit(), randomDigit()]),
    });
  }

  questions.push({
    prompt: `What color was the ${ordinal(third.position)} character?`,
    answer: third.colorName,
    choices: shuffle([third.colorName, "Red", "Blue", "Green", "Purple", "Black"]).slice(0, 3),
  });

  questions.push({
    prompt: "What color was the last character?",
    answer: last.colorName,
    choices: shuffle([last.colorName, "Red", "Blue", "Green", "Purple", "Black"]).slice(0, 3),
  });

  return questions.slice(0, 5);
}

export function mountSightGame(container) {
  let level = 1;
  let score = 0;
  let attempts = 0;
  let revealSeconds = 4;
  let currentRoundId = 0;
  let revealTimeout = null;
  let activeLine = null;

  const section = text("section", "brain-game-module sight-memory-screen");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Sight Memory"), text("p", "", "Memorize one line of characters: identity, order, and color."));

  const controls = text("div", "sight-memory-controls");
  const revealSelect = document.createElement("select");
  [3, 4, 5, 7].forEach((seconds) => {
    const option = document.createElement("option");
    option.value = String(seconds);
    option.textContent = `${seconds}s reveal`;
    revealSelect.append(option);
  });

  const startBtn = text("button", "", "Start Round");
  startBtn.type = "button";
  const resetBtn = text("button", "", "Reset");
  resetBtn.type = "button";

  controls.append(text("label", "", "Reveal Timer"), revealSelect, startBtn, resetBtn);

  const stage = text("div", "memory-card-stage");
  const questionPanel = text("div", "question-panel");
  const feedback = text("p", "brain-game-module__feedback", "Press Start Round to begin.");

  const stats = text("div", "brain-game-module__stats");
  const levelNode = text("p", "", "Level 1");
  const scoreNode = text("p", "", "Score 0");
  const accuracyNode = text("p", "", "Accuracy 0%");
  stats.append(levelNode, scoreNode, accuracyNode);

  section.append(header, controls, stage, questionPanel, stats, feedback);
  container.replaceChildren(section);

  function clearRevealTimer() {
    if (revealTimeout) {
      clearTimeout(revealTimeout);
      revealTimeout = null;
    }
  }

  function invalidateRound() {
    currentRoundId += 1;
    clearRevealTimer();
  }

  function updateStats() {
    const accuracy = attempts ? Math.round((score / attempts) * 100) : 0;
    levelNode.textContent = `Level ${level}`;
    scoreNode.textContent = `Score ${score}`;
    accuracyNode.textContent = `Accuracy ${accuracy}%`;
  }

  function renderCard(memoryLine) {
    const cardNode = text("article", "memory-card memory-card--minimal");
    const row = text("p", "memory-card__character-row");

    memoryLine.forEach((entry) => {
      const token = text("span", "memory-card__character", entry.value);
      token.style.color = entry.colorValue;
      token.dataset.kind = entry.kind;
      row.append(token);
    });

    cardNode.append(row);
    stage.replaceChildren(cardNode);
  }

  function renderQuestions(roundId) {
    if (roundId !== currentRoundId || !activeLine) return;
    stage.replaceChildren(text("div", "memory-card-placeholder", "Card hidden"));

    const questionList = text("div", "question-panel__list");
    const questions = buildQuestions(activeLine);
    let correctCount = 0;

    questions.forEach((question) => {
      const row = text("div", "question-panel__item");
      row.append(text("p", "", question.prompt));

      const options = text("div", "question-panel__options");
      question.choices.forEach((choice) => {
        const optionBtn = text("button", "", String(choice));
        optionBtn.type = "button";
        optionBtn.addEventListener("click", () => {
          if (optionBtn.dataset.locked) return;
          optionBtn.dataset.locked = "true";
          attempts += 1;

          if (choice === question.answer) {
            score += 1;
            correctCount += 1;
            optionBtn.classList.add("is-correct");
          } else {
            optionBtn.classList.add("is-wrong");
          }

          row.querySelectorAll("button").forEach((button) => {
            button.disabled = true;
            if (button.textContent === String(question.answer)) button.classList.add("is-correct");
          });

          updateStats();

          if (questionList.querySelectorAll("button:not([disabled])").length === 0) {
            if (correctCount >= Math.ceil(questions.length * 0.7)) {
              level += 1;
              feedback.textContent = "Round complete: strong recall.";
            } else {
              feedback.textContent = "Round complete: keep observing order and color.";
            }
            updateStats();
          }
        });
        options.append(optionBtn);
      });

      row.append(options);
      questionList.append(row);
    });

    questionPanel.replaceChildren(questionList);
    feedback.textContent = "Answer from memory.";
  }

  function startRound() {
    invalidateRound();
    activeLine = buildCharacterLine(level);
    questionPanel.replaceChildren();
    renderCard(activeLine);

    const roundId = currentRoundId;
    feedback.textContent = "Study the line.";

    revealTimeout = setTimeout(() => {
      if (roundId !== currentRoundId) return;
      renderQuestions(roundId);
    }, revealSeconds * 1000);
  }

  function resetAll() {
    invalidateRound();
    level = 1;
    score = 0;
    attempts = 0;
    activeLine = null;
    stage.replaceChildren(text("div", "memory-card-placeholder", "Round reset"));
    questionPanel.replaceChildren();
    feedback.textContent = "Reset complete. Start a new round.";
    updateStats();
  }

  revealSelect.addEventListener("change", (event) => {
    revealSeconds = Number(event.target.value);
  });

  startBtn.addEventListener("click", startRound);
  resetBtn.addEventListener("click", resetAll);

  stage.replaceChildren(text("div", "memory-card-placeholder", "One memory line will appear here."));
  updateStats();

  return () => {
    invalidateRound();
    container.replaceChildren();
  };
}
