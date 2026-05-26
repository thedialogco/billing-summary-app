import { useState } from "react";
import Settings from "./pages/Settings";
import Generate from "./pages/Generate";

type Tab = "generate" | "settings";

export default function App() {
  const [tab, setTab] = useState<Tab>("generate");

  return (
    <div className="min-h-screen bg-brand-50">
      <header className="bg-brand-700 shadow-md">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-white">Billing Summary Generator</span>
          </div>
          <nav className="flex gap-1">
            {(["generate", "settings"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  tab === t
                    ? "bg-white text-brand-700"
                    : "text-white/70 hover:text-white hover:bg-brand-800"
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
