import useLocalMemory from "../hooks/useLocalMemory";

export default function CalendarPanel() {
  const currentMonth = new Date().toLocaleString("default", { month: "long" });
  const [historyData] = useLocalMemory("monthlyHistory", {
    month: currentMonth,
    highlights: [
      "1865: The 13th Amendment was ratified, abolishing slavery.",
      "1955: The Montgomery Bus Boycott began this month.",
      "1987: The first Pan-African Congress in Africa was held in Ghana.",
    ],
  });

  return (
    <div className="calendar-panel">
      <h2>{historyData.month} in Black History</h2>
      <ul>
        {historyData.highlights.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
