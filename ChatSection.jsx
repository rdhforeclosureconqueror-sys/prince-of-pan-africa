import React, { useState } from "react";
import { speakMufasa } from "../../utils/mufasaVoice";

export default function ChatSection() {
  const [message, setMessage] = useState("");
  const [log, setLog] = useState([]);

  const sendChat = () => {
    if (!message.trim()) return;
    setLog([...log, { sender: "user", text: message }]);
    speakMufasa("Let’s keep your focus strong, my friend.");
    setMessage("");
  };

  return (
    <div className="panel chat-panel">
      <h2>Mufasa Chat</h2>
      <div className="chat-log">
        {log.map((m, i) => (
          <div key={i} className={`chat-msg ${m.sender}`}>
            {m.text}
          </div>
        ))}
      </div>
      <div className="chat-input">
        <input
          type="text"
          placeholder="Ask or speak to your coach..."
          value={message}
          onChange={e => setMessage(e.target.value)}
        />
        <button onClick={sendChat}>Ask</button>
      </div>
    </div>
  );
}
