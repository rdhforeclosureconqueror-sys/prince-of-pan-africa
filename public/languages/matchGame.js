(function initReusableMatchGame(global){
  function shuffle(items){
    const copy = Array.isArray(items) ? [...items] : [];
    for(let i = copy.length - 1; i > 0; i -= 1){
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function buildMatchRound(words){
    const usable = (Array.isArray(words) ? words : [])
      .filter((w) => w && w.swahili && w.english)
      .slice(0, 6);

    const cards = usable.flatMap((w, index) => {
      const pairId = `pair-${index}`;
      return [
        { id: `${pairId}-a`, pairId, text: w.swahili, type: 'source' },
        { id: `${pairId}-b`, pairId, text: w.english, type: 'target' },
      ];
    });

    return shuffle(cards);
  }

  function initMatchGame({ containerId, words, onComplete } = {}){
    const root = document.getElementById(containerId);
    if(!root){
      console.warn(`initMatchGame: container #${containerId} not found.`);
      return null;
    }

    const state = {
      cards: buildMatchRound(words),
      flipped: [],
      matched: new Set(),
      locked: false,
      completed: false,
    };

    function render(){
      const totalPairs = state.cards.length / 2;
      const matchedPairs = state.matched.size;
      const progress = `${matchedPairs}/${totalPairs}`;

      root.innerHTML = `
        <div class="match-shell">
          <div class="match-head">
            <h3 class="section-title" style="margin:0">Word Match</h3>
            <div class="pill">Progress: <b>${progress}</b></div>
          </div>
          <div class="note" style="margin-bottom:12px">
            Match each African language word with its English meaning.
          </div>
          <div class="match-grid" role="list">
            ${state.cards.map((card) => {
              const isMatched = state.matched.has(card.pairId);
              const isFlipped = state.flipped.includes(card.id);
              const visible = isMatched || isFlipped;
              return `
                <button
                  type="button"
                  class="match-card ${visible ? 'is-visible' : ''} ${isMatched ? 'is-matched' : ''}"
                  data-card-id="${card.id}"
                >
                  <span>${visible ? card.text : '• • •'}</span>
                </button>
              `;
            }).join('')}
          </div>
          <div class="match-footer">
            <div class="status" data-state="${state.completed ? 'playing' : 'ready'}">
              ${state.completed ? '✅ Match complete. Lesson unlocked.' : 'Flip two cards to find a pair.'}
            </div>
            <button type="button" class="btn gold" data-match-reset>↻ New Round</button>
          </div>
        </div>
      `;

      root.querySelectorAll('[data-card-id]').forEach((btn) => {
        btn.addEventListener('click', () => handleFlip(btn.getAttribute('data-card-id')));
      });

      root.querySelector('[data-match-reset]')?.addEventListener('click', resetRound);
    }

    function resetRound(){
      state.cards = buildMatchRound(words);
      state.flipped = [];
      state.matched.clear();
      state.locked = false;
      state.completed = false;
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
        state.flipped = [];

        if(state.matched.size === state.cards.length / 2){
          state.completed = true;
          if(typeof onComplete === 'function') onComplete();
        }

        render();
        return;
      }

      state.locked = true;
      setTimeout(() => {
        state.flipped = [];
        state.locked = false;
        render();
      }, 650);
    }

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
