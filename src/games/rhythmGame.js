const LANE_KEYS = ["A", "S", "D", "F", "G"];
const LANE_FREQUENCIES = [261.63, 293.66, 329.63, 392.0, 440.0];

const DIFFICULTY_CONFIG = {
  easy: { label: "Easy", fallMs: 2600, hitWindowMs: 180, densityMultiplier: 0.85 },
  medium: { label: "Medium", fallMs: 2000, hitWindowMs: 125, densityMultiplier: 1 },
  hard: { label: "Hard", fallMs: 1450, hitWindowMs: 85, densityMultiplier: 1.12 },
};

const PATTERNS = [
  {
    id: "mary-little-lamb",
    label: "Mary Had a Little Lamb (PD)",
    source: "public-domain",
    beats: [2, 1, 0, 1, 2, 2, 2, null, 1, 1, 1, null, 2, 4, 4, null],
  },
  {
    id: "ode-to-joy",
    label: "Ode to Joy (PD)",
    source: "public-domain",
    beats: [2, 2, 3, 4, 4, 3, 2, 1, 0, 0, 1, 2, 2, 1, 1, null],
  },
  {
    id: "rb-groove-01",
    label: "R&B Groove 01",
    source: "original",
    beats: [0, null, 2, 1, null, 3, 2, null, 0, 2, 4, null, 3, 2, 1, null],
  },
  {
    id: "neo-soul-pocket-01",
    label: "Neo Soul Pocket 01",
    source: "original",
    beats: [2, null, 4, null, 3, 2, null, 1, null, 0, 2, null, 3, null, 2, 1],
  },
  {
    id: "hip-hop-bounce-01",
    label: "Hip-Hop Bounce 01",
    source: "original",
    beats: [0, null, 0, 2, null, 3, null, 4, 2, null, 1, null, 3, 2, null, 0],
  },
];

function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function createTonePlayer() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const ctx = AudioCtx ? new AudioCtx() : null;

  return {
    play(frequency) {
      if (!ctx) return;
      if (ctx.state === "suspended") {
        ctx.resume().catch(() => {});
      }

      const now = ctx.currentTime;
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.type = "triangle";
      oscillator.frequency.value = frequency;
      gainNode.gain.setValueAtTime(0.0001, now);
      gainNode.gain.exponentialRampToValueAtTime(0.11, now + 0.015);
      gainNode.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      oscillator.start(now);
      oscillator.stop(now + 0.3);
    },
    dispose() {
      if (ctx && ctx.state !== "closed") ctx.close().catch(() => {});
    },
  };
}

function buildNoteTimeline(pattern, bpm, densityMultiplier) {
  const beatMs = 60000 / bpm;
  const timeline = [];

  pattern.beats.forEach((lane, index) => {
    if (lane === null || lane === undefined) return;
    timeline.push({
      lane,
      offsetMs: Math.round(index * beatMs * densityMultiplier),
      status: "pending",
      judged: false,
    });
  });

  return timeline;
}

function getJudgement(deltaMs, hitWindowMs) {
  const abs = Math.abs(deltaMs);
  if (abs > hitWindowMs) return null;
  if (abs <= hitWindowMs * 0.33) return { label: "Perfect", points: 100 };
  if (abs <= hitWindowMs * 0.66) return { label: "Good", points: 70 };
  return { label: "OK", points: 40 };
}

export function mountRhythmGame(container) {
  let score = 0;
  let hits = 0;
  let attempts = 0;
  let combo = 0;
  let rafId = null;
  let chartStartTime = 0;
  let activePatternId = PATTERNS[0].id;
  let activeDifficulty = "easy";
  let tempo = 100;
  let laneFlashUntil = Array(5).fill(0);
  let notes = [];
  let mobileMode = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;

  const tonePlayer = createTonePlayer();

  const section = text("section", "brain-game-module song-keys-screen");
  if (mobileMode) section.classList.add("song-keys-screen--mobile-mode");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Song Keys"), text("p", "", "Strike A/S/D/F/G or tap lane pads as notes cross the hit line."));

  const controls = text("div", "song-keys-controls");
  const songSelect = document.createElement("select");
  PATTERNS.forEach((pattern) => {
    const option = document.createElement("option");
    option.value = pattern.id;
    option.textContent = pattern.label;
    songSelect.append(option);
  });

  const difficultySelect = document.createElement("select");
  Object.entries(DIFFICULTY_CONFIG).forEach(([key, config]) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = config.label;
    difficultySelect.append(option);
  });

  const tempoSelect = document.createElement("select");
  [80, 100, 120, 140].forEach((bpm) => {
    const option = document.createElement("option");
    option.value = String(bpm);
    option.textContent = `${bpm} BPM`;
    tempoSelect.append(option);
  });

  const mobileModeBtn = text("button", "song-keys-mobile-toggle", "Mobile Pad Mode");
  mobileModeBtn.type = "button";
  if (mobileMode) mobileModeBtn.classList.add("is-active");

  controls.append(
    text("label", "song-keys-controls__group", "Song"),
    songSelect,
    text("label", "song-keys-controls__group", "Difficulty"),
    difficultySelect,
    text("label", "song-keys-controls__group", "Tempo"),
    tempoSelect,
    mobileModeBtn,
  );

  const board = text("div", "lane-board");
  const laneColumns = LANE_KEYS.map((key, laneIndex) => {
    const lane = text("div", "lane-board__lane");
    lane.dataset.lane = String(laneIndex);
    lane.append(text("div", "lane-board__label", key));
    board.append(lane);
    return lane;
  });
  const hitLine = text("div", "lane-board__hit-line");
  board.append(hitLine);

  const lanePads = text("div", "song-keys-lane-pads");
  const lanePadButtons = LANE_KEYS.map((key, laneIndex) => {
    const pad = text("button", "song-keys-lane-pad", key);
    pad.type = "button";
    pad.setAttribute("aria-label", `Tap lane ${key}`);

    const onPress = (event) => {
      event.preventDefault();
      handlePress(laneIndex);
    };

    pad.addEventListener("pointerdown", onPress);
    pad.addEventListener("touchstart", onPress, { passive: false });
    pad.addEventListener("click", onPress);
    lanePads.append(pad);
    return pad;
  });

  const feedback = text("p", "brain-game-module__feedback", "Press Start, then play when notes hit the line.");
  const startBtn = text("button", "song-keys-start", "Start Run");
  startBtn.type = "button";

  const stats = text("div", "brain-game-module__stats");
  const levelNode = text("p", "", "Level 1");
  const scoreNode = text("p", "", "Score 0");
  const accuracyNode = text("p", "", "Accuracy 0%");
  stats.append(levelNode, scoreNode, accuracyNode);

  const comboPanel = text("div", "song-keys-score-panel");
  const comboNode = text("p", "", "Combo: 0");
  const patternNode = text("p", "", `Pattern: ${PATTERNS[0].label}`);
  comboPanel.append(comboNode, patternNode);

  section.append(header, controls, board, lanePads, startBtn, comboPanel, stats, feedback);
  container.replaceChildren(section);

  function updateStats() {
    const accuracy = attempts ? Math.round((hits / attempts) * 100) : 0;
    const level = Math.max(1, Math.floor(score / 800) + 1);
    levelNode.textContent = `Level ${level}`;
    scoreNode.textContent = `Score ${score}`;
    accuracyNode.textContent = `Accuracy ${accuracy}%`;
    comboNode.textContent = `Combo: ${combo}`;
  }

  function render(now) {
    const config = DIFFICULTY_CONFIG[activeDifficulty];

    laneColumns.forEach((lane, laneIndex) => {
      const isPressed = laneFlashUntil[laneIndex] > now;
      if (isPressed) {
        lane.classList.add("is-pressed");
        lanePadButtons[laneIndex].classList.add("is-pressed");
      } else {
        lane.classList.remove("is-pressed");
        lanePadButtons[laneIndex].classList.remove("is-pressed");
      }
      lane.querySelectorAll(".falling-note").forEach((noteEl) => noteEl.remove());
    });

    let unresolved = 0;
    notes.forEach((note) => {
      if (note.status === "hit" || note.status === "missed") return;
      unresolved += 1;
      const spawnAt = chartStartTime + note.offsetMs;
      const hitAt = spawnAt + config.fallMs;
      const progress = (now - spawnAt) / config.fallMs;
      if (progress < 0) return;

      if (!note.judged && now - hitAt > config.hitWindowMs) {
        note.status = "missed";
        note.judged = true;
        combo = 0;
        attempts += 1;
        feedback.textContent = "Miss";
        updateStats();
        return;
      }

      if (progress > 1.16) return;

      const noteEl = text("div", "falling-note");
      noteEl.style.top = `${Math.min(progress * 82, 90)}%`;
      laneColumns[note.lane].append(noteEl);
    });

    if (unresolved > 0) {
      rafId = requestAnimationFrame(render);
      return;
    }

    feedback.textContent = "Run complete. Start a new run or switch settings.";
    rafId = null;
  }

  function beginRun() {
    if (rafId) cancelAnimationFrame(rafId);
    const pattern = PATTERNS.find((entry) => entry.id === activePatternId) || PATTERNS[0];
    const config = DIFFICULTY_CONFIG[activeDifficulty];
    notes = buildNoteTimeline(pattern, tempo, config.densityMultiplier);
    chartStartTime = performance.now();
    feedback.textContent = "Go";
    patternNode.textContent = `Pattern: ${pattern.label}`;
    rafId = requestAnimationFrame(render);
  }

  function handlePress(laneIndex) {
    const now = performance.now();
    laneFlashUntil[laneIndex] = now + 120;
    tonePlayer.play(LANE_FREQUENCIES[laneIndex]);

    const config = DIFFICULTY_CONFIG[activeDifficulty];
    const candidate = notes
      .filter((note) => note.lane === laneIndex && !note.judged)
      .map((note) => {
        const hitAt = chartStartTime + note.offsetMs + config.fallMs;
        return { note, delta: now - hitAt };
      })
      .sort((a, b) => Math.abs(a.delta) - Math.abs(b.delta))[0];

    if (!candidate) {
      attempts += 1;
      combo = 0;
      feedback.textContent = "Miss";
      updateStats();
      return;
    }

    const judgement = getJudgement(candidate.delta, config.hitWindowMs);
    attempts += 1;

    if (!judgement) {
      combo = 0;
      feedback.textContent = "Miss";
      if (candidate.delta > config.hitWindowMs) {
        candidate.note.status = "missed";
        candidate.note.judged = true;
      }
      updateStats();
      return;
    }

    candidate.note.status = "hit";
    candidate.note.judged = true;
    hits += 1;
    combo += 1;
    score += judgement.points;
    feedback.textContent = judgement.label;
    updateStats();
  }

  function onKeyDown(event) {
    const pressed = event.key.toUpperCase();
    const laneIndex = LANE_KEYS.indexOf(pressed);
    if (laneIndex === -1) return;
    handlePress(laneIndex);
  }

  songSelect.addEventListener("change", (event) => {
    activePatternId = event.target.value;
    const pattern = PATTERNS.find((entry) => entry.id === activePatternId);
    if (pattern) patternNode.textContent = `Pattern: ${pattern.label}`;
  });
  difficultySelect.addEventListener("change", (event) => {
    activeDifficulty = event.target.value;
  });
  tempoSelect.addEventListener("change", (event) => {
    tempo = Number(event.target.value);
  });
  startBtn.addEventListener("click", beginRun);
  mobileModeBtn.addEventListener("click", () => {
    mobileMode = !mobileMode;
    section.classList.toggle("song-keys-screen--mobile-mode", mobileMode);
    mobileModeBtn.classList.toggle("is-active", mobileMode);
  });

  window.addEventListener("keydown", onKeyDown);
  updateStats();

  return () => {
    if (rafId) cancelAnimationFrame(rafId);
    window.removeEventListener("keydown", onKeyDown);
    tonePlayer.dispose();
    container.replaceChildren();
  };
}
