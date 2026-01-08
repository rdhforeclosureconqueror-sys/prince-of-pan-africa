import React, { useState } from "react";
import CalendarSection from "../components/Fitness/CalendarSection";
import ChatSection from "../components/Fitness/ChatSection";
import NutritionSection from "../components/Fitness/NutritionSection";
import ProgressCharts from "../components/Fitness/ProgressCharts";
import MufasaSessionLauncher from "../components/Fitness/MufasaSessionLauncher";
import MufasaCoach from "./MufasaCoach";
import "../styles/FitnessPage.css";

export default function FitnessPage() {
  const [showCoach, setShowCoach] = useState(false);

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
            {/* Left Column */}
            <div className="dashboard-left">
              <CalendarSection />
              <MufasaSessionLauncher onLaunch={() => setShowCoach(true)} />
            </div>

            {/* Right Column */}
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
