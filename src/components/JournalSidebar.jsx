import React, { useState } from "react";

export default function JournalSidebar() {
  const [note, setNote] = useState(localStorage.getItem("journal") || "");

  const saveNote = () => {
    localStorage.setItem("journal", note);
    alert("Journal saved.");
  };

  return (
    <aside className="w-80 bg-[#111] border-r border-gray-800 p-4 flex flex-col">
      <h2 className="text-lg font-semibold text-pangold mb-2">Journal</h2>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        className="flex-1 bg-[#000] border border-gray-700 text-gray-200 rounded p-2"
      />
      <button
        onClick={saveNote}
        className="bg-pangreen mt-2 py-2 rounded text-black font-semibold"
      >
        Save
      </button>
    </aside>
  );
}
