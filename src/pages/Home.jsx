import { useState } from 'react'
import VoiceControls from '../components/VoiceControls'
import JournalSidebar from '../components/JournalSidebar'
import '../styles/theme.css'
import { sendChatMessage } from '../api/mufasaClient'

export default function Home() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim()) return
    const newMessage = { role: 'user', text: input }
    setMessages([...messages, newMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await sendChatMessage(input)
      const replyText = response.reply || response.answer || '🦁 Mufasa is thinking...'
      setMessages((prev) => [...prev, { role: 'assistant', text: replyText }])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: '⚠️ Error: Mufasa could not be reached.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <JournalSidebar />

      <main className="chat-area">
        <div className="chat-header">
          <h1>Prince of Pan-Africa</h1>
          <p>Every month is Black History. Powered by Mufasa.</p>
        </div>

        <div className="chat-window" id="chat-output">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`chat-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              {msg.text}
            </div>
          ))}
          {loading && <div className="chat-bubble assistant">🦁 Mufasa is responding...</div>}
        </div>

        <div className="chat-input-area">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Speak or type your question to Mufasa..."
          />
          <button className="send-btn" onClick={handleSend}>
            Send
          </button>
        </div>

        <VoiceControls />
      </main>
    </div>
  )
}
