import React, { useState } from "react";

export default function NutritionSection() {
  const [entries, setEntries] = useState([]);
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState(null);

  const handleSubmit = e => {
    e.preventDefault();
    if (!text && !photo) return;
    const entry = { text, photo: photo ? URL.createObjectURL(photo) : null, date: new Date() };
    setEntries([entry, ...entries]);
    setText("");
    setPhoto(null);
  };

  return (
    <div className="panel nutrition-panel">
      <h2>Food & Journal</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          placeholder="Describe your meal or how you feel..."
          value={text}
          onChange={e => setText(e.target.value)}
        />
        <input type="file" accept="image/*" onChange={e => setPhoto(e.target.files[0])} />
        <button type="submit">Log Entry</button>
      </form>
      <div className="nutrition-log">
        {entries.map((e, i) => (
          <div key={i} className="nutrition-entry">
            {e.photo && <img src={e.photo} alt="meal" />}
            <p>{e.text}</p>
            <span>{e.date.toLocaleDateString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
