import React from "react";

export default function CalendarSection() {
  return (
    <div className="panel calendar-panel">
      <h2>Workout Calendar</h2>
      <p>Gold = today | Green = workout days</p>
      <div id="calendar-widget">
        {/* You can integrate react-calendar or FullCalendar here */}
      </div>
    </div>
  );
}
