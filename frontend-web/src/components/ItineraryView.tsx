"use client";

import { useState } from "react";
import type { Trip } from "@/types";

function BudgetBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span>${value.toLocaleString()}</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full">
        <div className="h-1.5 bg-brand-500 rounded-full" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function FlightCard({ flights }: { flights: any }) {
  const recs = flights?.recommendations || [];
  if (!recs.length) return null;
  const top = recs[0];
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
      <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
        ✈️ Flights
      </h3>
      <div className="space-y-3">
        {recs.map((f: any, i: number) => (
          <div
            key={f.flight_id || i}
            className={`p-3 rounded-xl border ${i === 0 ? "border-brand-300 bg-brand-50" : "border-gray-100"}`}
          >
            <div className="flex justify-between items-center">
              <span className="font-semibold text-gray-800">{f.airline}</span>
              <span className="text-brand-700 font-bold">${f.price}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {f.departure?.substring(0, 16)} → {f.arrival?.substring(0, 16)}
            </div>
            <div className="text-xs text-gray-400">
              {f.stops === 0 ? "Non-stop" : `${f.stops} stop(s)`} · {f.duration}
            </div>
            {i === 0 && (
              <div className="mt-1.5 text-xs text-brand-600 font-medium">★ Recommended</div>
            )}
            {f.reason && <p className="text-xs text-gray-500 mt-1 italic">{f.reason}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

function HotelCard({ hotels }: { hotels: any }) {
  const recs = hotels?.recommendations || [];
  if (!recs.length) return null;
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
      <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
        🏨 Hotels
      </h3>
      <div className="space-y-3">
        {recs.map((h: any, i: number) => (
          <div
            key={h.hotel_id || i}
            className={`p-3 rounded-xl border ${h.hotel_id === hotels.recommended_hotel_id ? "border-brand-300 bg-brand-50" : "border-gray-100"}`}
          >
            <div className="flex justify-between items-center">
              <span className="font-semibold text-gray-800">{h.name}</span>
              <span className="text-brand-700 font-bold">${h.price_per_night}/night</span>
            </div>
            <div className="text-xs text-gray-500">{h.area} · Rating: {h.rating}/10</div>
            {h.amenities?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {h.amenities.map((a: string) => (
                  <span key={a} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{a}</span>
                ))}
              </div>
            )}
            {h.hotel_id === hotels.recommended_hotel_id && (
              <div className="mt-1.5 text-xs text-brand-600 font-medium">★ Recommended</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function DayCard({ day }: { day: any }) {
  const slots = [
    { key: "morning", label: "Morning", emoji: "🌅" },
    { key: "afternoon", label: "Afternoon", emoji: "☀️" },
    { key: "evening", label: "Evening", emoji: "🌆" },
  ];
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <h3 className="font-bold text-lg text-gray-900">Day {(day.day_index ?? day.day ?? 0) + (day.day_index !== undefined ? 1 : 0)}</h3>
          {day.theme && <p className="text-xs text-brand-600 font-medium">{day.theme}</p>}
        </div>
        <span className="text-sm text-gray-400">{day.date}</span>
      </div>
      <div className="space-y-4 mb-4">
        {slots.map(({ key, label, emoji }) => {
          const slot = day[key];
          if (!slot) return null;
          return (
            <div key={key} className="flex gap-3">
              <span className="text-lg w-6 shrink-0">{emoji}</span>
              <div className="flex-1">
                <p className="font-medium text-gray-800">{slot.name}</p>
                <p className="text-sm text-gray-500 mt-0.5">{slot.description}</p>
                <div className="flex gap-3 mt-1 text-xs text-gray-400">
                  {slot.start_time && <span>🕐 {slot.start_time}</span>}
                  <span>⏱ {slot.duration_hours}h</span>
                  <span>💵 ${slot.estimated_cost}</span>
                </div>
                {slot.tips && <p className="text-xs text-amber-600 mt-1 italic">{slot.tips}</p>}
              </div>
            </div>
          );
        })}
      </div>
      {day.transport_notes && (
        <p className="text-xs text-gray-400 border-t border-gray-100 pt-3">🚌 {day.transport_notes}</p>
      )}
      {day.daily_total_cost != null && (
        <p className="text-xs text-gray-500 border-t border-gray-100 pt-3 mt-2">
          Daily cost: <strong>${day.daily_total_cost}</strong>
        </p>
      )}
    </div>
  );
}

function BudgetSummary({ budget }: { budget: any }) {
  if (!budget) return null;
  const breakdown = budget.breakdown || {};
  const total = budget.total_budget || 1;
  return (
    <div className={`rounded-2xl p-6 border ${budget.is_within_budget ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
      <h3 className={`font-bold text-lg mb-4 ${budget.is_within_budget ? "text-green-800" : "text-red-800"}`}>
        💰 Budget Analysis {budget.is_within_budget ? "✓" : "⚠️ Over Budget"}
      </h3>
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-600">Estimated total</span>
          <span className="font-bold">${budget.total_estimated_cost?.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Your budget</span>
          <span className="font-bold">${budget.total_budget?.toLocaleString()}</span>
        </div>
      </div>
      {Object.entries(breakdown).map(([k, v]) => (
        <BudgetBar key={k} label={k.charAt(0).toUpperCase() + k.slice(1)} value={v as number} max={total} />
      ))}
      {budget.savings_tips?.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-green-700 mb-1">Savings tips:</p>
          <ul className="space-y-1">
            {budget.savings_tips.map((tip: string, i: number) => (
              <li key={i} className="text-xs text-green-700">• {tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function ItineraryView({ trip, liveUpdate, planningError }: { trip: Trip; liveUpdate?: any; planningError?: string }) {
  const [tab, setTab] = useState<"overview" | "flights" | "hotels" | "budget">("overview");

  if (trip.status === "planning" || trip.status === "replanning") {
    return (
      <div className="text-center py-20 text-gray-400">
        <div className="animate-spin text-4xl mb-4">⚙️</div>
        <p className="text-2xl mb-2">
          {trip.status === "replanning" ? "Replanning your trip…" : "Planning your trip…"}
        </p>
        <p className="text-sm">Our agents are working hard for you.</p>
      </div>
    );
  }

  const activePlan = liveUpdate?.plan || trip.plan;

  if (trip.status === "failed" || !activePlan) {
    const errorMessage = planningError || "Something went wrong while generating your itinerary.";
    return (
      <div className="rounded-2xl border border-red-100 bg-red-50 p-8 text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-xl font-semibold text-red-800 mb-2">Itinerary Planning Failed</p>
        <p className="text-sm text-red-700 mb-6 max-w-md mx-auto">{errorMessage}</p>
        <a
          href="/trips/new"
          className="inline-block bg-brand-600 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-brand-700 transition-colors"
        >
          Plan a New Trip
        </a>
      </div>
    );
  }

  const isMultiAgent = !!(activePlan.flights || activePlan.itinerary);
  const days: any[] = isMultiAgent
    ? (activePlan.itinerary?.days || [])
    : (activePlan.days || []);

  if (liveUpdate?.replan) {
    return (
      <div>
        <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 mb-6">
          <p className="font-semibold text-amber-800">⚠️ Itinerary Updated</p>
          <p className="text-sm text-amber-700 mt-1">{liveUpdate.replan.summary}</p>
          {liveUpdate.replan.changes?.map((c: any, i: number) => (
            <div key={i} className="text-xs text-amber-600 mt-1 border-l-2 border-amber-400 pl-2">
              <strong>{c.component}:</strong> {c.original} → {c.updated}
            </div>
          ))}
        </div>
        {renderContent()}
      </div>
    );
  }

  function renderContent() {
    return (
      <div className="space-y-6">
        {isMultiAgent ? (
          <>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {(["overview", "flights", "hotels", "budget"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                    tab === t ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
            {tab === "overview" && days.map((day, i) => <DayCard key={i} day={day} />)}
            {tab === "flights" && <FlightCard flights={activePlan.flights} />}
            {tab === "hotels" && <HotelCard hotels={activePlan.hotels} />}
            {tab === "budget" && <BudgetSummary budget={activePlan.budget_summary} />}
          </>
        ) : (
          <>
            <div className="bg-gradient-to-r from-brand-600 to-brand-700 text-white rounded-2xl p-8">
              <h1 className="text-3xl font-bold mb-2">{activePlan.title}</h1>
              <p className="text-brand-100 mb-4">{activePlan.summary}</p>
              <div className="flex gap-6 text-sm">
                <span>📅 {activePlan.total_days} days</span>
                <span>💰 ${activePlan.estimated_total_cost?.toLocaleString()}</span>
              </div>
            </div>
            {days.map((day, i) => <DayCard key={i} day={day} />)}
            {activePlan.tips?.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
                <h3 className="font-bold text-amber-800 mb-3">Travel Tips</h3>
                <ul className="space-y-1">
                  {activePlan.tips.map((tip: string, i: number) => (
                    <li key={i} className="text-sm text-amber-700">• {tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  return renderContent();
}
