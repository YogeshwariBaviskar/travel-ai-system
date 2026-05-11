# AI-Powered Multi-Agent Travel Planner — Claude Code Guide

## Project Overview

This is a full-stack, multi-agent AI travel planning system. Multiple specialized AI agents collaborate to produce personalized, budget-aware, real-time-adaptive travel itineraries.

## Repository Layout

```
travel-ai-system/
├── frontend-web/        # Next.js 14 (App Router) + Tailwind CSS
├── mobile-app/          # React Native (Expo)
├── backend/
│   ├── api/             # FastAPI routes
│   ├── agents/          # Agent definitions and orchestration
│   ├── services/        # Flight, hotel, map, weather service wrappers
│   └── db/              # SQLAlchemy models + Alembic migrations
├── ai-layer/
│   ├── agents/          # Individual agent implementations
│   ├── memory/          # Vector DB interface (FAISS / Pinecone)
│   └── orchestrator.py  # LangGraph graph definition
├── infra/
│   ├── docker/          # Dockerfiles + docker-compose
│   └── terraform/       # AWS IaC
└── tests/
    ├── unit/
    └── integration/
```

## Tech Stack

| Layer | Technology |
|---|---|
| Web frontend | Next.js 14, Tailwind CSS, Zustand |
| Mobile | React Native (Expo), Zustand |
| Backend API | FastAPI (Python 3.11) |
| Auth | JWT + OAuth2 (Google) |
| Primary DB | PostgreSQL 15 |
| Cache / Queue | Redis 7 |
| AI Orchestration | LangGraph |
| LLM | OpenAI (gpt-5.4-mini default) |
| Vector DB | FAISS (dev) / Pinecone (prod) |
| Flights API | Amadeus |
| Hotels API | Booking.com |
| Maps | Google Maps API |
| Weather | OpenWeather API |
| Container | Docker + docker-compose |
| Cloud | AWS (EC2, RDS, S3, ElastiCache) |
| CI/CD | GitHub Actions |

## Development Commands

```bash
# Start all services locally
docker-compose up --build

# Backend only
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend web only
cd frontend-web && npm run dev

# Run tests
cd backend && pytest tests/ -v
cd frontend-web && npm test

# DB migrations
cd backend && alembic upgrade head

# Lint (backend)
cd backend && ruff check . && mypy .

# Lint (frontend)
cd frontend-web && npm run lint
```

## Agent Descriptions

| Agent | Responsibility |
|---|---|
| PlannerAgent | Decomposes user request into subtasks, orchestrates other agents |
| FlightAgent | Queries Amadeus API, ranks by price/time, returns top options |
| HotelAgent | Queries Booking.com, filters by budget and proximity |
| ExperienceAgent | Builds day-wise attraction/food/event schedule |
| BudgetAgent | Validates total cost, reallocates budget across components |
| CalendarAgent | Reads Google Calendar, blocks unavailable dates |
| NotificationAgent | Schedules reminders, weather alerts, check-in nudges |
| ReplannerAgent | Triggered by disruptions (delay, cancellation, weather) |

## Key Conventions

- All agents implement the `BaseAgent` interface in `ai-layer/agents/base.py`.
- Agents communicate through a shared `TripState` object (LangGraph state node).
- External API calls go through service wrappers in `backend/services/` — never call third-party APIs directly from agents.
- All LLM calls must include prompt caching headers where applicable.
- FastAPI routes are thin: validation only. Business logic lives in `backend/agents/` or `ai-layer/`.
- Use Pydantic v2 models for all request/response schemas.
- PostgreSQL is the source of truth; Redis is ephemeral.
- Secrets via environment variables only — never hardcoded.

## Environment Variables Required

```
# LLM
OPENAI_API_KEY=

# External APIs
AMADEUS_API_KEY=
AMADEUS_API_SECRET=
BOOKING_API_KEY=
GOOGLE_MAPS_API_KEY=
OPENWEATHER_API_KEY=
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/travel_ai
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Vector DB (prod)
PINECONE_API_KEY=
PINECONE_ENV=
```

Copy `.env.example` to `.env` and fill in values before running locally.

## Testing Strategy

- Unit tests for each agent in isolation (mock external calls).
- Integration tests for agent-to-agent flows using real DB (Docker Postgres).
- E2E tests for the full trip-planning flow (Playwright for web).
- Never mock the database in integration tests — use a dedicated test DB.

## OpenAI-Specific Notes

- Default model: `gpt-5.4-mini` for all agents.
- Streaming responses are enabled for user-facing itinerary generation.
- Tool use is enabled: agents call tools (flight search, hotel search) as OpenAI function tools.
