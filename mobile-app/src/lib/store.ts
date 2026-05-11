import { create } from "zustand";

interface User {
  id: string;
  email: string;
  name: string;
}

interface Trip {
  id: string;
  title: string;
  status: string;
  raw_request?: Record<string, unknown>;
  plan?: Record<string, unknown>;
  agent_state?: Record<string, unknown>;
  created_at: string;
}

interface AppState {
  user: User | null;
  trips: Trip[];
  token: string | null;
  setUser: (user: User | null) => void;
  setTrips: (trips: Trip[]) => void;
  setToken: (token: string | null) => void;
  addTrip: (trip: Trip) => void;
  removeTrip: (id: string) => void;
}

export const useStore = create<AppState>((set) => ({
  user: null,
  trips: [],
  token: null,
  setUser: (user) => set({ user }),
  setTrips: (trips) => set({ trips }),
  setToken: (token) => set({ token }),
  addTrip: (trip) => set((s) => ({ trips: [trip, ...s.trips] })),
  removeTrip: (id) => set((s) => ({ trips: s.trips.filter((t) => t.id !== id) })),
}));
