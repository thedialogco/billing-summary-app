import { useState } from "react";
import Settings from "./pages/Settings";
import Generate from "./pages/Generate";

type Tab = "generate" | "settings";

export default function App() {
  const [tab, setTab] = useState<Tab>("generate");

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded">BSG</div>
            <span className="font-semibold text-gray-800">Billing Summary Generator</span>
          </div>
          <nav className="flex gap-1">
            {(["generate", "settings"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  tab === t
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                }`}
              >
                {t === "generate" ? "Generate" : "Settings"}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {tab === "generate" ? <Generate /> : <Settings />}
      </main>
    </div>
  );
}
