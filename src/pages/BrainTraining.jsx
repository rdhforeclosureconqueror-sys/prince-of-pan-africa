import React, { useEffect, useRef } from "react";
import { mountRhythmGame } from "../games/rhythmGame";
import { mountSightGame } from "../games/sightGame";
import { mountPuzzleGame } from "../games/puzzleGame";
import "../styles/brainTraining.css";

export default function BrainTraining() {
  const rhythmRef = useRef(null);
  const sightRef = useRef(null);
  const puzzleRef = useRef(null);

  useEffect(() => {
    const cleanups = [];

    if (rhythmRef.current) {
      cleanups.push(mountRhythmGame(rhythmRef.current));
    }
    if (sightRef.current) {
      cleanups.push(mountSightGame(sightRef.current));
    }
    if (puzzleRef.current) {
      cleanups.push(mountPuzzleGame(puzzleRef.current));
    }

    return () => cleanups.forEach((cleanup) => cleanup?.());
  }, []);

  return (
    <main className="brain-training-shell">
      <section className="brain-training-panel">
        <header className="brain-training-panel__header">
          <h1>Brain Training Suite</h1>
          <p>Train rhythm, visual memory, and puzzle logic with progressive challenge rounds.</p>
        </header>

        <div className="brain-training-grid">
          <div className="brain-training-card" ref={rhythmRef} />
          <div className="brain-training-card" ref={sightRef} />
          <div className="brain-training-card" ref={puzzleRef} />
        </div>
      </section>
    </main>
  );
}
