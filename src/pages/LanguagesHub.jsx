import "../styles/languages.css";

export default function LanguagesHub() {
  return (
    <main className="languages-shell">
      <section className="languages-panel cosmic-readable-shell">
        <h1>Languages</h1>
        <p>Choose a language module:</p>

        <div className="languages-grid">
          <a href="/languages/swahili.html" className="language-card">Swahili • Lesson of the Day →</a>
          <a href="/languages/yoruba.html" className="language-card">Yoruba • Lesson of the Day →</a>
        </div>
      </section>
    </main>
  );
}
