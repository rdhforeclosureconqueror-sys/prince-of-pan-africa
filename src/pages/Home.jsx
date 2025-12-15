import VoiceControls from '../components/VoiceControls'
import JournalSidebar from '../components/JournalSidebar'
import '../styles/theme.css'

export default function Home() {
  return (
    <div className="app-container">
      <JournalSidebar />
      <main className="chat-area">
        <div className="chat-header">
          <h1>Prince of Pan-Africa</h1>
          <p>Every month is Black History. Powered by Mufasa.</p>
        </div>

        <div className="chat-window">
          <div id="chat-output"></div>
        </div>

        <VoiceControls />
      </main>
    </div>
  )
}
