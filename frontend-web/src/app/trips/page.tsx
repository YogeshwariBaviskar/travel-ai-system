"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { Trip } from "@/types";

function TripCard({ trip }: { trip: Trip }) {
  const statusColor =
    trip.status === "complete"
      ? "bg-green-100 text-green-700"
      : trip.status === "failed"
      ? "bg-red-100 text-red-700"
      : "bg-yellow-100 text-yellow-700";

  return (
    <Link href={`/trips/${trip.id}`}>
      <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-bold text-gray-900">{trip.title}</h3>
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor}`}>
            {trip.status}
          </span>
        </div>
        {trip.raw_request && (
          <p className="text-sm text-gray-500 mb-1">
            {trip.raw_request.start_date} → {trip.raw_request.end_date} ·{" "}
            {trip.raw_request.num_travelers} traveler(s)
          </p>
        )}
        {trip.plan && (
          <p className="text-sm text-gray-400">
            Est. {trip.plan.currency} ${trip.plan.estimated_total_cost?.toLocaleString()}
          </p>
        )}
        <p className="text-xs text-gray-300 mt-3">
          {new Date(trip.created_at).toLocaleDateString()}
        </p>
      </div>
    </Link>
  );
}

export default function TripsPage() {
  const router = useRouter();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      setLoading(false);
      return;
    }
    api.trips
      .list()
      .then(setTrips)
      .catch((err: Error) => {
        if (err.message === "401" || err.message.includes("Unauthorized") || err.message.includes("Invalid token")) {
          router.push("/login");
        } else {
          setError("Failed to load trips. Please try again.");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return <div className="text-center py-20 text-gray-400">Loading your trips…</div>;
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={() => { setError(""); setLoading(true); api.trips.list().then(setTrips).catch(() => setError("Failed to load trips.")).finally(() => setLoading(false)); }}
          className="text-brand-600 font-medium hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Trips</h1>
        <Link
          href="/trips/new"
          className="bg-brand-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-brand-700 transition-colors"
        >
          + Plan New Trip
        </Link>
      </div>

      {trips.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-xl mb-4">No trips yet</p>
          <Link href="/trips/new" className="text-brand-600 font-medium hover:underline">
            Plan your first trip →
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {trips.map((t) => (
            <TripCard key={t.id} trip={t} />
          ))}
        </div>
      )}
    </div>
  );
}
