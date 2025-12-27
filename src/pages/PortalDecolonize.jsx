import React, { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import VoiceControls from "../components/VoiceControls";
import JournalSidebar from "../components/JournalSidebar";
import SocialShare from "../components/SocialShare";
import { DECLO30 } from "../data/portals/decolo30";

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function PortalDecolonize() {
  const query = useQuery();

  const initialDay = Math.min(
    Math.max(parseInt(query.get("day") || "1", 10), 1),
    30
  );

  const [day, setDay] = useState(initialDay);

  useEffect(() => {
    // If user enters from Library with ?day=6 etc.
    setDay(initialDay);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialDay]);

  const lesson = DECLO30.find((d) => d.day === day);

  const formattedForVoice = lesson
    ? `${lesson.title}\n\n${lesson.hook}\n\nCORE:\nL1: ${lesson.core.L1}\n\nL2: ${lesson.core.L2}\n\nL3: ${lesson.core.L3}\n\nPRACTICE: ${lesson.practice}\n\nJOURNAL: ${lesson.journal}\n\nMINI-Q: ${lesson.miniQ}\n\nRESUME_CODE=${lesson.resume}`
    : "Lesson not found.";

  return (
    <div className="flex min-h-screen bg-panblack text-white">
      <JournalSidebar />

      <main className="flex-1 p-4 md:p-8 overflow-y-auto">
        <h1 className="text-2xl md:text-3xl font-bold text-pangold mb-2">
          Portal: Decolonize the Mind
        </h1>

        <div className="flex flex-wrap items-center gap-3 mb-6">
          <p className="text-gray-400">Day {day} of 30</p>

          <div className="flex gap-2">
            <button
              onClick={() => setDay((d) => Math.max(1, d - 1))}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-[#111] hover:bg-[#1a1a1a]"
            >
              ← Prev
            </button>

            <button
              onClick={() => setDay((d) => Math.min(30, d + 1))}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-[#111] hover:bg-[#1a1a1a]"
            >
              Next →
            </button>
          </div>
        </div>

        {!lesson ? (
          <div className="p-4 border border-gray-700 rounded-lg bg-[#111]">
            ⚠️ Lesson not loaded yet. Add Day {day} into src/data/portals/decolo30.js
          </div>
        ) : (
          <div className="p-4 md:p-6 border border-gray-700 rounded-lg bg-[#111]">
            <h2 className="text-xl md:text-2xl font-bold text-pangold">
              {lesson.title}
            </h2>

            <p className="mt-3 text-gray-200 leading-relaxed">
              <span className="font-bold text-pangold">HOOK: </span>
              {lesson.hook}
            </p>

            <div className="mt-5 space-y-3">
              <div>
                <div className="font-bold text-pangold">CORE (L1/L2/L3)</div>
                <div className="mt-2 space-y-2 text-gray-200 leading-relaxed">
                  <p><span className="font-bold">L1: </span>{lesson.core.L1}</p>
                  <p><span className="font-bold">L2: </span>{lesson.core.L2}</p>
                  <p><span className="font-bold">L3: </span>{lesson.core.L3}</p>
                </div>
              </div>

              <div>
                <div className="font-bold text-pangold">PRACTICE</div>
                <p className="mt-2 text-gray-200 leading-relaxed">{lesson.practice}</p>
              </div>

              <div>
                <div className="font-bold text-pangold">JOURNAL PROMPT</div>
                <p className="mt-2 text-gray-200 leading-relaxed">{lesson.journal}</p>
              </div>

              <div>
                <div className="font-bold text-pangold">MINI-Q</div>
                <p className="mt-2 text-gray-200 leading-relaxed">{lesson.miniQ}</p>
              </div>

              <div className="mt-4 text-xs text-gray-400">
                RESUME_CODE={lesson.resume}
              </div>
            </div>
          </div>
        )}

        <div className="mt-8">
          <VoiceControls text={formattedForVoice} />
          <SocialShare />
        </div>
      </main>
    </div>
  );
}
