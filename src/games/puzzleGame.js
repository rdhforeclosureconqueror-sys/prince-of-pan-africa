function text(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function shuffled(list) {
  return [...list].sort(() => Math.random() - 0.5);
}

export function mountPuzzleGame(container) {
  let level = 1;
  let score = 0;
  let attempts = 0;
  let solves = 0;
  let imageUrl = "";
  let selectedIndex = null;
  let gridSize = 3;
  let pieces = [];

  const section = text("section", "brain-game-module image-puzzle-screen");
  const header = text("header", "brain-game-module__header");
  header.append(text("h3", "", "Puzzle"), text("p", "", "Upload an image, then rebuild it by swapping shuffled pieces."));

  const controls = text("div", "image-puzzle-controls");
  const uploadLabel = text("label", "", "Upload image");
  const uploadInput = document.createElement("input");
  uploadInput.type = "file";
  uploadInput.accept = "image/*";

  const gridLabel = text("label", "", "Grid size");
  const gridSelect = document.createElement("select");
  [3, 4, 5].forEach((value) => {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = `${value} x ${value}`;
    gridSelect.append(option);
  });

  const shuffleBtn = text("button", "", "Shuffle");
  shuffleBtn.type = "button";
  const resetBtn = text("button", "", "Reset Board");
  resetBtn.type = "button";

  controls.append(uploadLabel, uploadInput, gridLabel, gridSelect, shuffleBtn, resetBtn);

  const board = text("div", "image-puzzle-board");
  const feedback = text("p", "brain-game-module__feedback", "Upload an image to begin.");

  const stats = text("div", "brain-game-module__stats");
  const levelNode = text("p", "", "Level 1");
  const scoreNode = text("p", "", "Score 0");
  const accuracyNode = text("p", "", "Accuracy 0%");
  stats.append(levelNode, scoreNode, accuracyNode);

  section.append(header, controls, board, stats, feedback);
  container.replaceChildren(section);

  function updateStats() {
    level = Math.max(1, Math.floor(solves / 2) + 1);
    const accuracy = attempts ? Math.round((solves / attempts) * 100) : 0;
    levelNode.textContent = `Level ${level}`;
    scoreNode.textContent = `Score ${score}`;
    accuracyNode.textContent = `Accuracy ${accuracy}%`;
  }

  function isSolved(list) {
    return list.every((pieceValue, index) => pieceValue === index);
  }

  function buildSolvedPieces(size) {
    return Array.from({ length: size * size }, (_, index) => index);
  }

  function startPuzzleRound() {
    if (!imageUrl) return;
    pieces = buildSolvedPieces(gridSize);
    selectedIndex = null;
    pieces = shuffled(pieces);
    if (isSolved(pieces)) {
      const first = pieces[0];
      pieces[0] = pieces[1];
      pieces[1] = first;
    }
    attempts += 1;
    feedback.textContent = "Puzzle shuffled. Tap/click two tiles to swap.";
    renderBoard();
    updateStats();
  }

  function markSolvedIfComplete() {
    if (!isSolved(pieces)) return;
    solves += 1;
    score += gridSize * 150;
    feedback.textContent = "Solved! Upload another image or reshuffle for a new run.";
    updateStats();
  }

  function renderBoard() {
    board.replaceChildren();

    if (!imageUrl) {
      board.append(text("p", "image-puzzle-placeholder", "No image loaded."));
      return;
    }

    board.style.gridTemplateColumns = `repeat(${gridSize}, minmax(0, 1fr))`;

    pieces.forEach((pieceValue, index) => {
      const tile = text("button", "image-puzzle-tile");
      tile.type = "button";
      tile.style.backgroundImage = `url(${imageUrl})`;
      tile.style.backgroundSize = `${gridSize * 100}% ${gridSize * 100}%`;

      const pieceRow = Math.floor(pieceValue / gridSize);
      const pieceCol = pieceValue % gridSize;
      tile.style.backgroundPosition = `${(pieceCol / (gridSize - 1 || 1)) * 100}% ${(pieceRow / (gridSize - 1 || 1)) * 100}%`;

      if (selectedIndex === index) tile.classList.add("is-selected");

      tile.addEventListener("click", () => {
        if (selectedIndex === null) {
          selectedIndex = index;
          renderBoard();
          return;
        }

        if (selectedIndex === index) {
          selectedIndex = null;
          renderBoard();
          return;
        }

        const next = [...pieces];
        const hold = next[selectedIndex];
        next[selectedIndex] = next[index];
        next[index] = hold;
        pieces = next;
        selectedIndex = null;
        renderBoard();
        markSolvedIfComplete();
      });

      board.append(tile);
    });
  }

  function resetPuzzle() {
    selectedIndex = null;
    pieces = imageUrl ? buildSolvedPieces(gridSize) : [];
    feedback.textContent = imageUrl ? "Board reset to solved state. Shuffle to play." : "Upload an image to begin.";
    renderBoard();
  }

  uploadInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    if (!file) return;

    imageUrl = URL.createObjectURL(file);
    pieces = buildSolvedPieces(gridSize);
    feedback.textContent = "Image uploaded. Press Shuffle to start the puzzle.";
    renderBoard();
    updateStats();
  });

  gridSelect.addEventListener("change", (event) => {
    gridSize = Number(event.target.value);
    resetPuzzle();
  });

  shuffleBtn.addEventListener("click", startPuzzleRound);
  resetBtn.addEventListener("click", resetPuzzle);

  renderBoard();
  updateStats();

  return () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    container.replaceChildren();
  };
}
