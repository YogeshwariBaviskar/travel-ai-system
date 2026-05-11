# AI-Powered Multi-Agent Travel Planner — Project Plan

## Vision

Build a production-grade, multi-agent AI travel planning system where specialized agents collaborate in real time to create, optimize, and adapt travel itineraries. The system targets FAANG-level engineering quality: observable, testable, deployed, and demonstrably scalable.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│         Next.js Web App          React Native Mobile         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                           │
│   Auth (JWT/OAuth)  │  Trip API  │  Webhook Receivers        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               Agent Orchestration Layer (LangGraph)          │
│                                                              │
│  PlannerAgent ──► FlightAgent                                │
│       │       ──► HotelAgent                                 │
│       │       ──► ExperienceAgent                            │
│       │       ──► BudgetAgent                                │
│       │       ──► CalendarAgent                              │
│       └─────────► NotificationAgent                          │
│                                                              │
│  ReplannerAgent (triggered on disruption events)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Shared State & Storage                     │
│   TripState (in-flight)  │  Vector DB  │  PostgreSQL  │ Redis│
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    External APIs                             │
│  Amadeus  │  Booking.com  │  Google Maps  │  OpenWeather     │
│  Google Calendar  │  Twilio/FCM (notifications)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Specifications

### PlannerAgent
- **Input:** Raw user request (destination, dates, budget, preferences)
- **Output:** Structured `TripPlan` object with subtask assignments
- **Model:** `gpt-5.4-mini`
- **Tools:** None — orchestrates other agents via LangGraph graph

### FlightAgent
- **Input:** Origin, destination, date range, budget ceiling
- **Output:** Top 3 flight options with price, duration, layovers
- **Model:** `gpt-5.4-mini`
- **Tools:** `search_flights` (Amadeus API wrapper)

### HotelAgent
- **Input:** City, check-in/out, budget per night, preferred area
- **Output:** Top 3 hotel options with amenities and proximity score
- **Model:** `gpt-5.4-mini`
- **Tools:** `search_hotels` (Booking.com API wrapper)

### ExperienceAgent
- **Input:** Destination, days, interests, dietary restrictions
- **Output:** Day-by-day schedule (attractions, meals, transport)
- **Model:** `gpt-5.4-mini`
- **Tools:** `get_attractions` (Google Maps), `get_events` (Eventbrite)

### BudgetAgent
- **Input:** All cost components from other agents
- **Output:** Total cost breakdown, reallocation suggestions if over budget
- **Model:** `gpt-5.4-mini`
- **Tools:** None — pure calculation over structured data

### CalendarAgent
- **Input:** User ID, trip date range
- **Output:** Conflict list, confirmed available windows
- **Tools:** `read_google_calendar` (OAuth2 scoped)

### NotificationAgent
- **Input:** Finalized trip plan, user notification preferences
- **Output:** Scheduled notification queue
- **Tools:** `schedule_push` (FCM), `schedule_sms` (Twilio)

### ReplannerAgent
- **Input:** Current trip plan + disruption event (delay, cancellation, weather)
- **Output:** Updated trip plan with minimal changes
- **Model:** `gpt-5.4-mini`
- **Trigger:** Webhook from flight status API, weather alert, or user manual trigger

---

## Data Models

### Core PostgreSQL Tables

```
users           — id, email, name, google_id, preferences (JSONB), created_at
trips           — id, user_id, title, status, raw_request, plan (JSONB), created_at
trip_flights    — id, trip_id, provider_ref, details (JSONB), price, booked_at
trip_hotels     — id, trip_id, provider_ref, details (JSONB), price, booked_at
itinerary_days  — id, trip_id, day_index, activities (JSONB)
notifications   — id, trip_id, type, scheduled_at, sent_at, payload (JSONB)
```

### TripState (LangGraph in-memory)

```python
class TripState(TypedDict):
    user_id: str
    request: TripRequest
    flights: list[FlightOption]
    hotels: list[HotelOption]
    itinerary: list[DayPlan]
    budget_summary: BudgetSummary
    calendar_conflicts: list[DateRange]
    notifications: list[NotificationTask]
    errors: list[AgentError]
    status: Literal["planning", "complete", "replanning", "failed"]
```

---

## Phase Roadmap

### Phase 1 — Foundation (Week 1–2) ✅
**Goal:** Runnable skeleton end-to-end with a single agent.

- [x] Initialize monorepo with directory structure
- [x] Set up `docker-compose` (Postgres, Redis, FastAPI, Next.js)
- [x] Implement User auth (Google OAuth2 + JWT)
- [x] Build `PlannerAgent` (Claude tool-use, structured itinerary output)
- [x] Create `/api/trips` CRUD endpoints
- [x] Build basic Next.js UI: trip input form → display itinerary
- [x] Write unit tests for PlannerAgent
- [x] Set up GitHub Actions CI (lint + test on PR)

**Deliverable:** User can log in, submit a trip request, and see a mock AI-generated itinerary.

---

### Phase 2 — Multi-Agent Orchestration (Week 3–4) ✅
**Goal:** Real agent collaboration with LangGraph.

- [x] Implement `BaseAgent` interface (`ai-layer/agents/base.py`)
- [x] Implement `FlightAgent` + Amadeus API wrapper (`backend/services/flight_service.py`)
- [x] Implement `HotelAgent` + Booking.com API wrapper (`backend/services/hotel_service.py`)
- [x] Implement `ExperienceAgent` + Google Maps wrapper (`backend/services/maps_service.py`)
- [x] Implement `BudgetAgent` (uses claude-haiku-4-5 for cost)
- [x] Wire all agents into LangGraph graph with `TripState` (`ai-layer/orchestrator.py`)
- [x] Add shared vector memory (FAISS) for preference context (`ai-layer/memory/vector_store.py`)
- [x] Streaming itinerary output via Server-Sent Events (`/api/trips/stream/{id}`)
- [x] Integration tests: full trip-planning flow against test DB

**Deliverable:** System generates a real, multi-component itinerary from live APIs.

---

### Phase 3 — Real-Time Adaptation (Week 5–6) ✅
**Goal:** Dynamic replanning on disruptions.

- [x] Implement `ReplannerAgent` (`ai-layer/agents/replanner_agent.py`)
- [x] Set up webhook receiver for flight status updates (`backend/api/routes/webhooks.py`)
- [x] Weather alert integration (`backend/services/weather_service.py`)
- [x] `CalendarAgent` + Google Calendar OAuth scope (`ai-layer/agents/calendar_agent.py`)
- [x] `NotificationAgent` + FCM push notifications (`ai-layer/agents/notification_agent.py`)
- [x] WebSocket endpoint for real-time plan updates pushed to frontend (`backend/api/routes/ws.py`)
- [x] Frontend: live plan update UI with diff highlighting + PlanningProgress component

**Deliverable:** Simulated flight delay auto-updates the itinerary and notifies the user.

---

### Phase 4 — Mobile App (Week 7–8) ✅
**Goal:** Feature-complete React Native app.

- [x] Initialize Expo project with expo-router (`mobile-app/`)
- [x] Auth flow (Google OAuth via Expo AuthSession) (`mobile-app/app/(auth)/login.tsx`)
- [x] Trip list + detail screens (`mobile-app/app/(tabs)/trips.tsx`, `mobile-app/app/trip/[id].tsx`)
- [x] New trip form with interest selector (`mobile-app/app/(tabs)/new-trip.tsx`)
- [x] Map-based itinerary view (Google Maps SDK)
- [x] Push notifications (Expo Notifications + FCM) (`mobile-app/src/lib/notifications.ts`)
- [x] Sync with backend via shared API client (`mobile-app/src/lib/api.ts`)
- [x] Zustand state management (`mobile-app/src/lib/store.ts`)

**Deliverable:** iOS/Android app with full trip planning and notifications.

---

### Phase 5 — Production & Polish (Week 9–10) ✅
**Goal:** Live deployment, observability, resume showcase.

- [x] Terraform: VPC, RDS, ElastiCache, ECS, S3, ALB (`infra/terraform/`)
- [x] Deploy to AWS with CI/CD pipeline (GitHub Actions → ECR → ECS) (`.github/workflows/ci.yml`)
- [x] Add observability: structured logging (structlog), metrics (Prometheus) (`backend/api/main.py`)
- [x] Preference learning: FAISS vector store, user context injected into planning
- [x] "Explain my plan" endpoint (`/api/trips/{id}/explain`)
- [x] Packing list generator (`ai-layer/agents/packing_agent.py`)
- [x] Load test (Locust): 100 concurrent users (`tests/load/locustfile.py`)

**Deliverable:** Live public URL, architecture diagram, demo video.

---

## Advanced / Differentiating Features

| Feature | Description | Phase |
|---|---|---|
| Conversational editing | "Make day 2 more relaxed" modifies only that day | 2 |
| Real-time replanning | Flight delay → auto-adjust entire itinerary | 3 |
| Calendar-aware planning | Skip dates blocked in Google Calendar | 3 |
| Group trip collaboration | Multiple users co-edit one trip (CRDT) | 5 |
| Preference learning | ML personalization from past trips | 5 |
| Travel Copilot Mode | Side-by-side chat + structured UI | 2 |
| Cultural tips | Per-destination cultural context injected into itinerary | 2 |
| AI food recommender | Dietary filter + local specialty awareness | 2 |
| Offline mode | Cached itineraries available without connectivity | 4 |
| Decision transparency | "Why did the AI choose this hotel?" | 5 |

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Itinerary generation latency (p95) | < 8 seconds |
| API uptime | 99.5% |
| Auth token expiry | 60 minutes (refresh token: 30 days) |
| Max concurrent users (MVP) | 100 |
| Test coverage (backend) | ≥ 80% |
| Mobile crash-free rate | ≥ 99% |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Amadeus free tier rate limits | High | Medium | Cache flight results in Redis (TTL 10 min) |
| LLM latency spikes | Medium | High | Stream responses; show partial itinerary |
| Google OAuth scope rejection | Low | High | Request minimal scopes; fallback to manual date entry |
| Budget overrun on LLM API costs | Medium | Medium | Use Haiku for cheap agents; cache system prompts |
| External API schema changes | Low | Medium | Versioned service wrappers with integration tests |

---

## Interview Talking Points

1. **Agent collaboration design** — why each agent is separate (single responsibility, independent scaling, parallel execution in LangGraph)
2. **State management** — `TripState` as the single source of truth across agents, persisted to PostgreSQL on completion
3. **Real-time replanning** — event-driven architecture (webhook → Redis queue → ReplannerAgent → WebSocket push)
4. **Consistent model** — all agents use `gpt-5.4-mini` via the OpenAI API for uniform capability and cost
5. **Observability** — every agent call emits a trace span; dashboards show per-agent latency and error rates
6. **Cost optimization** — `gpt-5.4-mini` balances capability and cost across all agents
