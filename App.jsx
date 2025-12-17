import { BrowserRouter, Routes, Route } from "react-router-dom";
import MufasaShell from "./layouts/MufasaShell";
import Home from "./pages/Home";
import CalendarPanel from "./components/CalendarPanel";
import JournalPanel from "./components/JournalPanel";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MufasaShell />}>
          <Route path="/" element={<Home />} />
          <Route path="/calendar" element={<CalendarPanel />} />
          <Route path="/journal" element={<JournalPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
