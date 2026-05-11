"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { isAuthenticated, getToken } from "@/lib/auth";
import ItineraryView from "@/components/ItineraryView";
import PlanningProgress from "@/components/PlanningProgress";
import type { Trip } from "@/types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export default function TripDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [liveUpdate, setLiveUpdate] = useState<any>(null);
  const [planningError, setPlanningError] = useState<{ error: string; code?: string } | null>(null);
  const [wsStatus, setWsStatus] = useState<"connected" | "disconnected" | "idle">("idle");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    const tripId = params.id as string;
    api.trips
      .get(tripId)
      .then((t) => {
        setTrip(t);
        connectWebSocket(tripId);
      })
      .catch(() => router.push("/trips"))
      .finally(() => setLoading(false));

    return () => wsRef.current?.close();
  }, [params.id, router]);

  function connectWebSocket(tripId: string) {
    const token = getToken() || "";
    const ws = new WebSocket(`${WS_BASE}/trips/${tripId}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.event === "replan") {
        setLiveUpdate(data);
        setTrip((prev) => prev ? { ...prev, status: "complete" } : prev);
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);

    ws.onclose = () => {
      clearInterval(ping);
      setWsStatus("disconnected");
    };
  }

  async function handleDelete() {
    if (!trip || !confirm("Delete this trip?")) return;
    setDeleting(true);
    setDeleteError("");
    try {
      await api.trips.delete(trip.id);
      router.push("/trips");
    } catch {
      setDeleteError("Failed to delete trip. Please try again.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleExplain() {
    if (!trip) return;
    try {
      const explanation = await fetch(`/api/trips/${trip.id}/explain`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      }).then((r) => r.json());
      alert(JSON.stringify(explanation, null, 2));
    } catch {
      alert("Could not load explanation.");
    }
  }

  if (loading) {
    return <div className="text-center py-20 text-gray-400">Loading itinerary…</div>;
  }

  if (!trip) return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <Link href="/trips" className="text-sm text-brand-600 hover:underline">
          ← Back to My Trips
        </Link>
        <div className="flex items-center gap-4">
          {wsStatus === "connected" && (
            <span className="text-xs text-green-500 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              Live
            </span>
          )}
          {trip.status === "complete" && (
            <button
              onClick={handleExplain}
              className="text-sm text-brand-600 hover:underline"
            >
              Why this plan?
            </button>
          )}
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="text-sm text-red-500 hover:text-red-700 disabled:opacity-50"
            >
              {deleting ? "Deleting…" : "Delete Trip"}
            </button>
            {deleteError && <p className="text-xs text-red-500">{deleteError}</p>}
          </div>
        </div>
      </div>

      {trip.status === "planning" && (
        <div className="mb-6">
          <PlanningProgress
            tripId={trip.id}
            onComplete={() => api.trips.get(trip.id).then(setTrip)}
            onError={(err) => {
              setPlanningError(err);
              setTrip((prev) => prev ? { ...prev, status: "failed" } : prev);
            }}
          />
        </div>
      )}

      {liveUpdate && (
        <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 mb-6">
          <p className="font-semibold text-amber-800">⚠️ Your plan has been updated</p>
          <p className="text-sm text-amber-700 mt-1">{liveUpdate.replan?.summary}</p>
        </div>
      )}

      <ItineraryView trip={trip} liveUpdate={liveUpdate} planningError={planningError?.error} />
    </div>
  );
}
