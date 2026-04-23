import React, { useEffect, useMemo, useRef, useState } from "react";
import { mountRhythmGame } from "../games/rhythmGame";
import { mountSightGame } from "../games/sightGame";
import { mountPuzzleGame } from "../games/puzzleGame";
import "../styles/brainTraining.css";

const GAME_TABS = [
  { id: "rhythm", label: "Song Keys", mount: mountRhythmGame },
  { id: "sight", label: "Visual Memory", mount: mountSightGame },
  { id: "puzzle", label: "Picture Puzzle", mount: mountPuzzleGame },
];

function readStats(root) {
  if (!root) return { level: "-", stars: "0", accuracy: "0%" };
  const statNodes = root.querySelectorAll(".brain-game-module__stats p");
  const level = statNodes[0]?.textContent?.replace("Level", "").trim() ?? "-";
  const stars = statNodes[1]?.textContent?.replace("Score", "").trim() ?? "0";
  const accuracy = statNodes[2]?.textContent?.replace("Accuracy", "").trim() ?? "0%";
  return { level, stars, accuracy };
}

export default function BrainTraining() {
  const [activeTab, setActiveTab] = useState("rhythm");
  const [statsByGame, setStatsByGame] = useState({
    rhythm: { level: "1", stars: "0", accuracy: "0%" },
    sight: { level: "1", stars: "0", accuracy: "0%" },
    puzzle: { level: "1", stars: "0", accuracy: "0%" },
  });

  const gameHosts = {
    rhythm: useRef(null),
    sight: useRef(null),
    puzzle: useRef(null),
  };

  useEffect(() => {
    const cleanups = [];
    const observers = [];

    GAME_TABS.forEach(({ id, mount }) => {
      const host = gameHosts[id].current;
      if (!host) return;

      cleanups.push(mount(host));

      const observeTarget = host;
      const observer = new MutationObserver(() => {
        setStatsByGame((prev) => ({
          ...prev,
          [id]: readStats(host),
        }));
      });

      observer.observe(observeTarget, {
        childList: true,
        subtree: true,
        characterData: true,
      });

      observers.push(observer);
      setStatsByGame((prev) => ({ ...prev, [id]: readStats(host) }));
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
      cleanups.forEach((cleanup) => cleanup?.());
    };
  }, []);

  const activeStats = useMemo(() => statsByGame[activeTab] ?? { level: "-", stars: "0", accuracy: "0%" }, [statsByGame, activeTab]);
  const activeGameLabel = GAME_TABS.find((tab) => tab.id === activeTab)?.label ?? "-";

  return (
    <main className="brain-training-shell">
      <section className="brain-training-panel">
        <header className="brain-training-panel__header">
          <h1>Brain Training Suite</h1>
          <p>Train rhythm, visual memory, and puzzle logic with progressive challenge rounds.</p>
        </header>

        <div className="brain-training-layout">
          <aside className="brain-training-sidebar">
            <section className="brain-training-block">
              <h2>Choose a profile</h2>
              <p>Choose your focus path before starting a round.</p>
            </section>

            <article className="brain-training-profile-card">
              <h3>Starter</h3>
              <p>Balanced pacing and guided prompts for warm-up sessions.</p>
              <span>Best for first-time players</span>
            </article>

            <article className="brain-training-profile-card brain-training-profile-card--accent">
              <h3>Challenge</h3>
              <p>Faster cycles and memory pressure to push score growth.</p>
              <span>Best for streak building</span>
            </article>

            <section className="brain-training-block brain-training-block--summary">
              <h3>Profile summary</h3>
              <p>Feedback updates live as you play each game module.</p>
              <ul>
                <li>Active profile: Focused Challenger</li>
                <li>Session note: Keep a steady response rhythm</li>
              </ul>
            </section>

            <button type="button" className="brain-training-reset-btn">
              Reset all games
            </button>
          </aside>

          <section className="brain-training-main">
            <nav className="brain-training-tabs" aria-label="Brain training games">
              {GAME_TABS.map((tab) => (
                <button
                  type="button"
                  key={tab.id}
                  className={`brain-training-tab ${activeTab === tab.id ? "is-active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </nav>

            <section className="brain-training-stat-row" aria-label="Current game stats">
              <article className="brain-training-stat-card">
                <p>Current level</p>
                <strong>{activeStats.level}</strong>
              </article>
              <article className="brain-training-stat-card">
                <p>Stars earned</p>
                <strong>{activeStats.stars}</strong>
              </article>
              <article className="brain-training-stat-card">
                <p>Accuracy</p>
                <strong>{activeStats.accuracy}</strong>
              </article>
              <article className="brain-training-stat-card">
                <p>Active game</p>
                <strong>{activeGameLabel}</strong>
              </article>
            </section>

            <section className="brain-training-active-panel">
              {GAME_TABS.map((tab) => (
                <div
                  key={tab.id}
                  className={`brain-training-card ${activeTab === tab.id ? "is-visible" : "is-hidden"}`}
                  ref={gameHosts[tab.id]}
                  aria-hidden={activeTab !== tab.id}
                />
              ))}
            </section>
          </section>
        </div>
      </section>
    </main>
  );
}
