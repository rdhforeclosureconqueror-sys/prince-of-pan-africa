import React, { useState } from "react";
import CalendarSection from "../components/Fitness/CalendarSection";
import ChatSection from "../components/Fitness/ChatSection";
import NutritionSection from "../components/Fitness/NutritionSection";
import ProgressCharts from "../components/Fitness/ProgressCharts";
import MufasaCoach from "./MufasaCoach";
import "../styles/FitnessPage.css";

export default function FitnessPage() {
  const [showCoach, setShowCoach] = useState(false);

  // Launches full-screen MufasaCoach
  const launchCoachSession = () => {
    setShowCoach(true);
    const elem = document.documentElement;
    if (elem.requestFullscreen) elem.requestFullscreen();
  };

  return (
    <div className="fitness-dashboard galaxy-bg">
      {!showCoach ? (
        <>
          <header className="dashboard-header">
            <h1>Pan-African Virtual Wellness Platform</h1>
            <p className="tagline">
              The world’s first Pan-African virtual fitness platform powered by Ma’at 2.0
            </p>
          </header>

          <div className="dashboard-grid">
            {/* LEFT SIDE */}
            <div className="dashboard-left">
              <CalendarSection />
              <div className="panel session-launcher">
                <h2>Start Training</h2>
                <p>
                  When ready, activate your AI coach for real-time movement tracking and
                  encouragement.
                </p>
                <button className="start-btn" onClick={launchCoachSession}>
                  Launch Mufasa Coach 🦁
                </button>
              </div>
            </div>

            {/* RIGHT SIDE */}
            <div className="dashboard-right">
              <ChatSection />
              <NutritionSection />
              <ProgressCharts />
            </div>
          </div>
        </>
      ) : (
        <MufasaCoach onExit={() => setShowCoach(false)} />
      )}
    </div>
  );
}
