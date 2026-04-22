(function initReusableMatchGame(global){
  const GRID_SIZE_OPTIONS = [
    { value: '3x4', label: '3x4', pairs: 6, columns: 3 },
    { value: '3x5', label: '3x5', pairs: 7, columns: 3 },
    { value: '3x6', label: '3x6', pairs: 9, columns: 3 },
  ];

  function shuffle(items){
    const copy = Array.isArray(items) ? [...items] : [];
    for(let i = copy.length - 1; i > 0; i -= 1){
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function extractSourceWord(word){
    if(!word || typeof word !== 'object') return '';
    return word.swahili || word.yoruba || word.word || '';
  }

  function buildMatchRound(words, gridSize = '3x4'){
    const config = GRID_SIZE_OPTIONS.find((opt) => opt.value === gridSize) || GRID_SIZE_OPTIONS[0];
    const usable = (Array.isArray(words) ? words : [])
      .filter((w) => w && extractSourceWord(w) && w.english)
      .slice(0, config.pairs);

    const cards = usable.flatMap((w, index) => {
      const pairId = `pair-${index}`;
      const sourceText = extractSourceWord(w);
      return [
        {
          id: `${pairId}-a`,
          pairId,
          type: 'source',
          primary: sourceText,
          secondary: w.helper || w.pronunciation || w.english,
          hint: w.english,
        },
        {
          id: `${pairId}-b`,
          pairId,
          type: 'target',
          primary: w.english,
          secondary: sourceText,
          hint: sourceText,
        },
      ];
    });

    return {
      cards: shuffle(cards),
      config,
    };
  }

  function initMatchGame({ containerId, words, onComplete, onProgress, onBackToLesson, onFeedback, title = 'Word Match', instructions = 'Match each African language word with its English meaning.' } = {}){
    const root = document.getElementById(containerId);
    if(!root){
      console.warn(`initMatchGame: container #${containerId} not found.`);
      return null;
    }

    const state = {
      gridSize: GRID_SIZE_OPTIONS[0].value,
      cards: [],
      config: GRID_SIZE_OPTIONS[0],
      flipped: [],
      matched: new Set(),
      locked: false,
      completed: false,
      streak: 0,
      bestStreak: 0,
      focusMode: false,
      pulseCardId: '',
      shakeCardIds: [],
      statusMessage: 'Flip two cards to find a pair.',
      statusTone: 'playing',
    };

    function emitProgress(){
      if(typeof onProgress === 'function'){
        onProgress({
          gridSize: state.gridSize,
          matchedPairs: state.matched.size,
          totalPairs: state.cards.length / 2,
          completed: state.completed,
        });
      }
    }

    function updateStatus(message, tone = 'playing'){
      state.statusMessage = message;
      state.statusTone = tone;
    }

    function rebuildRound(){
      const round = buildMatchRound(words, state.gridSize);
      state.cards = round.cards;
      state.config = round.config;
      state.flipped = [];
      state.matched.clear();
      state.locked = false;
      state.completed = false;
      state.streak = 0;
      state.bestStreak = 0;
      state.pulseCardId = '';
      state.shakeCardIds = [];
      updateStatus('Flip two cards to find a pair.', 'playing');
      emitProgress();
    }

    function render(){
      const totalPairs = state.cards.length / 2;
      const matchedPairs = state.matched.size;
      const progress = `${matchedPairs}/${totalPairs}`;

      root.innerHTML = `
        <div class="match-shell">
          <div class="match-head">
            <h3 class="section-title" style="margin:0">${title}</h3>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <div class="pill">Progress: <b>${progress}</b></div>
              <div class="pill">Streak: <b>${state.streak}</b></div>
            </div>
          </div>
          ${state.focusMode ? '' : `<div class="note" style="margin-bottom:12px">${instructions}</div>`}
          <div class="match-head" style="margin-bottom:12px">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span class="mini" style="font-size:12px;color:var(--muted)">Grid size:</span>
              ${GRID_SIZE_OPTIONS.map((opt) => `
                <button type="button" class="btn ${state.gridSize === opt.value ? 'gold' : ''}" data-grid-size="${opt.value}" style="padding:8px 12px;min-height:36px">${opt.label}</button>
              `).join('')}
            </div>
            <button type="button" class="btn ${state.focusMode ? 'green' : ''}" data-match-focus>
              ${state.focusMode ? '🎯 Focus Mode: On' : '🎯 Focus Mode'}
            </button>
          </div>
          ${state.focusMode ? '' : `
            <div class="note" style="margin-bottom:12px">
              Tap cards to reveal. Main label appears first, helper line appears below for clarity.
            </div>
          `}
          <div class="match-grid" role="list" style="grid-template-columns:repeat(${state.config.columns},minmax(0,1fr));">
            ${state.cards.map((card) => {
              const isMatched = state.matched.has(card.pairId);
              const isFlipped = state.flipped.includes(card.id);
              const visible = isMatched || isFlipped;
              const isPulse = state.pulseCardId === card.id;
              const isShake = state.shakeCardIds.includes(card.id);
              return `
                <button
                  type="button"
                  class="match-card ${visible ? 'is-visible' : ''} ${isMatched ? 'is-matched' : ''} ${isPulse ? 'is-pulse' : ''} ${isShake ? 'is-mismatch' : ''}"
                  data-card-id="${card.id}"
                >
                  <span class="match-primary">${visible ? card.primary : '• • •'}</span>
                  <span class="match-secondary">${visible ? card.secondary : 'Tap to reveal'}</span>
                </button>
              `;
            }).join('')}
          </div>
          <div class="match-footer">
            <div class="status" data-state="${state.statusTone}">
              ${state.statusMessage}
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <button type="button" class="btn gold" data-match-reset>↻ New Round</button>
              <button type="button" class="btn" data-match-back>← Back to Lesson</button>
            </div>
          </div>
        </div>
      `;

      root.querySelectorAll('[data-card-id]').forEach((btn) => {
        btn.addEventListener('click', () => handleFlip(btn.getAttribute('data-card-id')));
      });

      root.querySelector('[data-match-reset]')?.addEventListener('click', resetRound);
      root.querySelector('[data-match-focus]')?.addEventListener('click', () => {
        state.focusMode = !state.focusMode;
        if(typeof onFeedback === 'function') onFeedback({ type: 'focus', enabled: state.focusMode });
        render();
      });
      root.querySelector('[data-match-back]')?.addEventListener('click', () => {
        if(state.focusMode && typeof onFeedback === 'function'){
          onFeedback({ type: 'focus', enabled: false });
        }
        state.focusMode = false;
        if(typeof onBackToLesson === 'function') onBackToLesson();
      });
      root.querySelectorAll('[data-grid-size]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const next = btn.getAttribute('data-grid-size');
          if(!next || next === state.gridSize) return;
          state.gridSize = next;
          rebuildRound();
          render();
        });
      });
    }

    function resetRound(){
      rebuildRound();
      render();
    }

    function handleFlip(cardId){
      if(state.locked || state.completed || state.flipped.includes(cardId)) return;
      const card = state.cards.find((c) => c.id === cardId);
      if(!card || state.matched.has(card.pairId)) return;

      state.flipped.push(cardId);
      render();

      if(state.flipped.length < 2) return;

      const [aId, bId] = state.flipped;
      const a = state.cards.find((c) => c.id === aId);
      const b = state.cards.find((c) => c.id === bId);

      if(!a || !b){
        state.flipped = [];
        render();
        return;
      }

      if(a.pairId === b.pairId){
        state.matched.add(a.pairId);
        state.streak += 1;
        state.bestStreak = Math.max(state.bestStreak, state.streak);
        state.pulseCardId = b.id;
        state.shakeCardIds = [];
        state.flipped = [];
        const streakLabel = state.streak >= 3 ? 'On fire' : state.streak === 2 ? 'Nice' : 'Good job';
        updateStatus(`✅ ${streakLabel}! Match found: ${a.hint}`, 'ready');
        if(typeof onFeedback === 'function') onFeedback({ type: 'match', text: 'Good job', streak: state.streak, comboLabel: streakLabel });

        if(state.matched.size === state.cards.length / 2){
          state.completed = true;
          updateStatus('✅ Perfect round! Match complete. Lesson unlocked.', 'ready');
          if(typeof onFeedback === 'function') onFeedback({ type: 'perfect', text: 'Perfect', streak: state.streak });
          if(typeof onComplete === 'function') onComplete();
        }
        emitProgress();
        render();
        setTimeout(() => {
          state.pulseCardId = '';
          render();
        }, 220);
        return;
      }

      state.locked = true;
      state.streak = 0;
      state.shakeCardIds = [a.id, b.id];
      state.pulseCardId = '';
      updateStatus('❌ Try again — those cards do not match.', 'loading');
      if(typeof onFeedback === 'function') onFeedback({ type: 'mismatch', text: 'Try again', streak: 0 });
      render();
      setTimeout(() => {
        state.flipped = [];
        state.locked = false;
        state.shakeCardIds = [];
        updateStatus('Flip two cards to find a pair.', 'playing');
        render();
      }, 650);
    }

    rebuildRound();
    render();

    return {
      refresh(nextWords){
        words = nextWords;
        resetRound();
      },
      destroy(){
        root.innerHTML = '';
      }
    };
  }

  global.initMatchGame = initMatchGame;
  global.buildMatchRound = buildMatchRound;
  global.shuffle = shuffle;
})(window);
