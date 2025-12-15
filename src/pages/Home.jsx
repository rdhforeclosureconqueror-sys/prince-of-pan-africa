import React from "react";
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="text-center py-12 px-6">
      <h1 className="text-4xl font-bold text-pangold mb-6">
        PRINCE OF PAN-AFRICA
      </h1>
      <p className="text-gray-300 mb-8">
        Explore portals of Black history, language, and wisdom. <br />
        Every month is Black History.
      </p>
      <div className="flex flex-col gap-4 items-center">
        <Link
          to="/portal/decolonize"
          className="bg-panred hover:bg-pangreen text-white px-6 py-3 rounded-lg font-semibold"
        >
          Enter Portal: Decolonize the Mind
        </Link>
      </div>
    </div>
  );
}
