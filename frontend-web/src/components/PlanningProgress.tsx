"use client";

import { useEffect, useState } from "react";

interface ProgressEvent {
  stage: string;
  message: string;
}

interface PlanningError {
  error: string;
  code?: string;
}

const STAGES = ["context", "flights", "hotels", "experience", "budget", "finalizing"];
const STAGE_LABELS: Record<string, string> = {
  context: "User Context",
  flights: "Flight Search",
  hotels: "Hotel Search",
  experience: "Itinerary",
  budget: "Budget",
  finalizing: "Finalizing",
};
const STAGE_ICONS: Record<string, string> = {
  context: "🧠",
  flights: "✈️",
  hotels: "🏨",
  experience: "🗺️",
  budget: "💰",
  finalizing: "✨",
};

const ERROR_TITLES: Record<string, string> = {
  quota_exceeded: "API Credits Exhausted",
  rate_limit: "Rate Limit Reached",
  auth_error: "API Key Invalid",
  timeout: "Request Timed Out",
  connection_error: "Connection Failed",
  service_unavailable: "Service Unavailable",
  planning_failed: "Planning Failed",
  unknown_error: "Unexpected Error",
};

const ERROR_HINTS: Record<string, string> = {
  quota_exceeded: "Top up your OpenAI account at platform.openai.com/account/billing, then try again.",
  rate_limit: "OpenAI is throttling requests. Wait 60 seconds before retrying.",
  auth_error: "The server's OpenAI API key is misconfigured. Contact your administrator.",
  timeout: "The AI service was slow to respond. Retrying usually resolves this.",
  connection_error: "Check that the backend service is running and can reach the internet.",
  service_unavailable: "The multi-agent orchestrator could not be loaded. Check the backend logs.",
  planning_failed: "Try adjusting your destination, dates, or budget and create a new trip.",
  unknown_error: "An unexpected error occurred on the server. Please try again.",
};

export default function PlanningProgress({
  tripId,
  onComplete,
  onError,
}: {
  tripId: string;
  onComplete?: () => void;
  onError?: (err: PlanningError) => void;
}) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [currentStage, setCurrentStage] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<PlanningError | null>(null);

  useEffect(() => {
    if (!tripId) return;
    const token = localStorage.getItem("travel_ai_token");
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const sse = new EventSource(`${apiBase}/api/trips/stream/${tripId}?token=${token}`);

    sse.addEventListener("progress", (e) => {
      const data = JSON.parse(e.data) as ProgressEvent;
      setCurrentStage(data.stage);
      setEvents((prev) => [...prev, data]);
    });

    sse.addEventListener("complete", () => {
      setDone(true);
      sse.close();
      onComplete?.();
    });

    sse.addEventListener("error", (e: any) => {
      const data: PlanningError = e.data ? JSON.parse(e.data) : { error: "Planning failed unexpectedly." };
      setError(data);
      sse.close();
      onError?.(data);
    });

    return () => sse.close();
  }, [tripId]);

  if (error) {
    const code = error.code ?? "unknown_error";
    const title = ERROR_TITLES[code] ?? "Planning Failed";
    const hint = ERROR_HINTS[code] ?? ERROR_HINTS.unknown_error;
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl mt-0.5">⚠️</span>
          <div className="flex-1">
            <p className="font-semibold text-red-800 text-base">{title}</p>
            <p className="text-sm text-red-700 mt-1">{error.error}</p>
            <p className="text-xs text-red-600 mt-2 italic">{hint}</p>
            <a
              href="/trips/new"
              className="inline-block mt-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
            >
              Try a New Trip
            </a>
          </div>
        </div>
      </div>
    );
  }

  if (done) return null;

  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-4">AI Agents Working…</h3>
      <div className="space-y-2">
        {STAGES.map((stage) => {
          const completed = events.some((e) => e.stage === stage);
          const active = currentStage === stage && !done;
          return (
            <div key={stage} className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${active ? "bg-brand-50" : ""}`}>
              <span className="text-lg w-6">{STAGE_ICONS[stage]}</span>
              <span className={`text-sm flex-1 ${completed ? "text-gray-400 line-through" : active ? "text-brand-700 font-medium" : "text-gray-500"}`}>
                {STAGE_LABELS[stage]}
              </span>
              {completed && !active && <span className="text-green-500 text-sm">✓</span>}
              {active && (
                <span className="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
