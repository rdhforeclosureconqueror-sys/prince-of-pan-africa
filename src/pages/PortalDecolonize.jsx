import React, { useState } from "react";
import axios from "axios";
import VoiceControls from "../components/VoiceControls";
import JournalSidebar from "../components/JournalSidebar";
import SocialShare from "../components/SocialShare";

const MUFASA_API = "https://mufasa-knowledge-bank.onrender.com";

export default function PortalDecolonize() {
  const [day, setDay] = useState(1);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchLesson = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${MUFASA_API}/portal/start`, {
        portal_id: "DECLO30"
      });
      setResponse(res.data.response);
    } catch (err) {
      setResponse("⚠️ Error loading the portal lesson. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-panblack text-white">
      <JournalSidebar />

      <main className="flex-1 p-8 overflow-y-auto">
        <h1 className="text-3xl font-bold text-pangold mb-4">
          Portal: Decolonize the Mind
        </h1>
        <p className="text-gray-400 mb-6">Day {day} of 30</p>

        <button
          onClick={fetchLesson}
          className="bg-panred px-6 py-2 rounded-lg mb-6 hover:bg-pangreen"
        >
          Load Lesson
        </button>

        {loading ? (
          <p className="text-gray-400">Loading...</p>
        ) : (
          <div
            className="p-4 border border-gray-700 rounded-lg bg-[#111]"
            dangerouslySetInnerHTML={{ __html: response }}
          />
        )}

        <div className="mt-8">
          <VoiceControls text={response} />
          <SocialShare />
        </div>
      </main>
    </div>
  );
}
