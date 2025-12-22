export default function LanguagesHub() {
  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ color: "#f5c542" }}>Languages</h1>
      <p style={{ color: "#f5e6b3" }}>Choose a language module:</p>

      <div style={{ display: "grid", gap: 12, maxWidth: 460 }}>
        <a href="/languages/swahili.html" style={cardStyle}>Swahili • Lesson of the Day →</a>
        <a href="/languages/yoruba.html" style={cardStyle}>Yoruba • Lesson of the Day →</a>
      </div>
    </div>
  );
}

const cardStyle = {
  padding: 14,
  borderRadius: 14,
  border: "1px solid #b7791f",
  background: "rgba(0,0,0,0.5)",
  color: "#f5e6b3",
  textDecoration: "none",
};
