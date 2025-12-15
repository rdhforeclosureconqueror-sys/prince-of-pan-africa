import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import PortalDecolonize from "./pages/PortalDecolonize";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/portal/decolonize" element={<PortalDecolonize />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
