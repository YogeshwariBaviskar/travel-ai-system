"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { removeToken, isAuthenticated } from "@/lib/auth";

export default function Navbar() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  function handleLogout() {
    removeToken();
    router.push("/login");
  }

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <Link href="/" className="text-xl font-bold text-brand-600">
        ✈ TravelAI
      </Link>
      <div className="flex items-center gap-4">
        {mounted && isAuthenticated() && (
          <>
            <Link href="/trips" className="text-sm text-gray-600 hover:text-brand-600">
              My Trips
            </Link>
            <Link
              href="/trips/new"
              className="text-sm bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700"
            >
              Plan a Trip
            </Link>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sign out
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
