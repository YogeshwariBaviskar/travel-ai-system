export interface User {
  id: string;
  email: string;
  name: string;
}

export interface ActivityDetail {
  name: string;
  description: string;
  duration_hours: number;
  estimated_cost: number;
}

export interface DayPlan {
  day: number;
  date: string;
  location: string;
  morning: ActivityDetail;
  afternoon: ActivityDetail;
  evening: ActivityDetail;
  accommodation: {
    name: string;
    area: string;
    cost_per_night: number;
  };
}

export interface TripPlan {
  title: string;
  summary: string;
  total_days: number;
  estimated_total_cost: number;
  currency: string;
  days: DayPlan[];
  tips: string[];
}

export interface Trip {
  id: string;
  title: string;
  status: "planning" | "replanning" | "complete" | "failed";
  raw_request: CreateTripRequest | null;
  plan: TripPlan | null;
  created_at: string;
}

export interface CreateTripRequest {
  destination: string;
  start_date: string;
  end_date: string;
  budget: number;
  interests: string[];
  num_travelers: number;
}
