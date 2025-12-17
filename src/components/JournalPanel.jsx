import { useState } from "react";
import useLocalMemory from "../hooks/useLocalMemory";

export default function JournalPanel() {
  const currentMonth = new Date().toLocaleString("default", { month: "long" });
  const [journal, setJournal] = useLocalMemory("journalEntries", {});
  const [text, setText] = useState(journal[currentMonth] || "");

  const handleSave = () => {
    const updated = { ...journal, [currentMonth]: text };
    setJournal(updated);
  };

  return (
    <div className="journal-panel">
      <h2>{currentMonth} Journal</h2>
      <textarea
        placeholder="Write your reflection for this month..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button onClick={handleSave}>Save Journal</button>
    </div>
  );
}
