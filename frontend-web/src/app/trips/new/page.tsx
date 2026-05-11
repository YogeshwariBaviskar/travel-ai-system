"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import TripForm from "@/components/TripForm";

export default function NewTripPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Plan a New Trip</h1>
      <p className="text-gray-500 mb-8">
        Tell the AI where you want to go and it will build a full itinerary for you.
      </p>
      <TripForm />
    </div>
  );
}
