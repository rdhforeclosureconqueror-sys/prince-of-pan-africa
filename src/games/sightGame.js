const SYMBOLS = {
  easy: ["◆", "●", "▲", "■"],
  medium: ["◆", "◇", "●", "○", "▲", "■"],
  hard: ["◆", "◇", "◈", "●", "○", "◉", "▲", "△", "■", "▣"],
};

const COLORS = {
  easy: [
    { name: "Slate Blue", value: "#435f9f" },
    { name: "Teal", value: "#2a6a72" },
    { name: "Graphite", value: "#364252" },
    { name: "Plum", value: "#5a4b78" },
  ],
  medium: [
    { name: "Steel", value: "#4a5f7b" },
    { name: "Navy", value: "#304a6e" },
    { name: "Ash Blue", value: "#51657a" },
    { name: "Ocean", value: "#3d5f7c" },
  ],
  hard: [
    { name: "Deep Navy", value: "#2f4460" },
    { name: "Midnight Blue", value: "#2d4861" },
    { name: "Storm Blue", value: "#334e67" },
    { name: "Ink Blue", value: "#324866" },
  ],
};

const BORDER_STYLES = ["double", "solid", "dashed"];
const ACCENT_MARKS = ["•", "✦", "✶"];

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function pickRandom(list) {
  return list[Math.floor(Math.random() * list.length)];
}

function buildCard(difficulty) {
  const color = pickRandom(COLORS[difficulty]);
  const symbol = pickRandom(SYMBOLS[difficulty]);

  if (difficulty === "easy") {
    return {
      code: String(100 + Math.floor(Math.random() * 900)),
      color,
      symbol,
    };
  }

  if (difficulty === "medium") {
    return {
      code: String(1000 + Math.floor(Math.random() * 9000)),
      color,
      symbol,
      borderStyle: Math.random() > 0.5 ? pickRandom(BORDER_STYLES) : null,
    };
  }

  const alphanumeric = Math.random() > 0.45;
  const code = alphanumeric
    ? `${String.fromCharCode(65 + Math.floor(Math.random() * 26))}${Math.floor(100 + Math.random() * 900)}`
    : String(1000 + Math.floor(Math.random() * 9000));

  return {
    code,
    color,
    symbol,
    borderStyle: pickRandom(BORDER_STYLES),
    accentMark: pickRandom(ACCENT_MARKS),
  };
}

function shuffled(list) {
  return [...list].sort(() => Math.random() - 0.5);
}

function buildQuestions(card, difficulty) {
  const questions = [];

  const codeChoices = shuffled([
    card.code,
    `${card.code.split("").reverse().join("")}`,
    `${card.code}`.replace(/\d/, (digit) => `${(Number(digit) + 1) % 10}`),
  ]).slice(0, 3);

  questions.push({
    prompt: "Which code did you see?",
    answer: card.code,
    choices: Array.from(new Set(codeChoices)),
  });

  const colorPool = COLORS[difficulty].map((entry) => entry.name);
  const colorChoices = shuffled([card.color.name, ...colorPool.filter((name) => name !== card.color.name).slice(0, 2)]);
  questions.push({
    prompt: "Which color was the card?",
    answer: card.color.name,
    choices: colorChoices,
  });

  const symbolChoices = shuffled([
    card.symbol,
    ...SYMBOLS[difficulty].filter((symbol) => symbol !== card.symbol).slice(0, 2),
  ]);
  questions.push({
    prompt: "Which symbol appeared in the center?",
    answer: card.symbol,
    choices: symbolChoices,
  });

  if (card.borderStyle) {
    questions.push({
      prompt: "Which border style was used?",
      answer: card.borderStyle,
      choices: shuffled([card.borderStyle, ...BORDER_STYLES.filter((entry) => entry !== card.borderStyle).slice(0, 2)]),
    });
  }

  if (card.accentMark) {
    questions.push({
      prompt: "Which accent mark was shown?",
      answer: card.accentMark,
      choices: shuffled([card.accentMark, ...ACCENT_MARKS.filter((entry) => entry !== card.accentMark)]),
    });
  }

  return questions;
}

export function mountSightGame(container) {
  let level = 1;
  let score = 0;
  let attempts = 0;
  let difficulty = "easy";
  let revealSeconds = 4;
  let currentRoundId = 0;
  let revealTimeout = null;
  let activeCard = null;

  const section = text("section", "brain-game-module sight-memory-screen");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Sight Memory"), text("p", "", "Study one card, then answer from memory."));

  const controls = text("div", "sight-memory-controls");
  const difficultySelect = document.createElement("select");
  ["easy", "medium", "hard"].forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value[0].toUpperCase() + value.slice(1);
    difficultySelect.append(option);
  });

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

  controls.append(
    text("label", "", "Difficulty"),
    difficultySelect,
    text("label", "", "Reveal Timer"),
    revealSelect,
    startBtn,
    resetBtn,
  );

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

  function renderCard(card) {
    const cardNode = text("article", "memory-card");
    cardNode.style.background = `linear-gradient(160deg, ${card.color.value}, #1b263a)`;
    cardNode.style.borderStyle = card.borderStyle || "solid";

    cardNode.append(text("p", "memory-card__code", card.code), text("p", "memory-card__symbol", card.symbol));
    if (card.accentMark) {
      cardNode.append(text("span", "memory-card__accent", card.accentMark));
    }

    stage.replaceChildren(cardNode);
  }

  function renderQuestions(roundId) {
    if (roundId !== currentRoundId || !activeCard) return;
    stage.replaceChildren(text("div", "memory-card-placeholder", "Card hidden"));

    const questionList = text("div", "question-panel__list");
    const questions = buildQuestions(activeCard, difficulty);
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
              feedback.textContent = "Round complete: keep observing details.";
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
    activeCard = buildCard(difficulty);
    questionPanel.replaceChildren();
    renderCard(activeCard);

    const roundId = currentRoundId;
    feedback.textContent = "Study the card.";

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
    activeCard = null;
    stage.replaceChildren(text("div", "memory-card-placeholder", "Round reset"));
    questionPanel.replaceChildren();
    feedback.textContent = "Reset complete. Start a new round.";
    updateStats();
  }

  difficultySelect.addEventListener("change", (event) => {
    difficulty = event.target.value;
  });

  revealSelect.addEventListener("change", (event) => {
    revealSeconds = Number(event.target.value);
  });

  startBtn.addEventListener("click", startRound);
  resetBtn.addEventListener("click", resetAll);

  stage.replaceChildren(text("div", "memory-card-placeholder", "One card will appear here."));
  updateStats();

  return () => {
    invalidateRound();
    container.replaceChildren();
  };
}
