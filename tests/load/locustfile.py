"""Locust load test: simulates 100 concurrent users planning trips."""
import json
import random
from locust import HttpUser, TaskSet, task, between, events


DESTINATIONS = ["Paris, France", "Tokyo, Japan", "New York, USA", "Rome, Italy", "Barcelona, Spain"]
INTERESTS = ["Culture", "Food", "Art", "Adventure", "History"]


class TripPlanningTasks(TaskSet):
    token: str = ""

    def on_start(self):
        # Reuse a shared test token for load tests
        self.token = self.user.token

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(3)
    def list_trips(self):
        self.client.get("/api/trips/", headers=self._auth_headers(), name="/api/trips/ [GET]")

    @task(1)
    def create_trip_single_agent(self):
        """Lightweight trip creation using single PlannerAgent (no live LLM in load test)."""
        dest = random.choice(DESTINATIONS)
        interests = random.sample(INTERESTS, 2)
        payload = {
            "destination": dest,
            "start_date": "2026-08-01",
            "end_date": "2026-08-06",
            "budget": random.randint(1500, 5000),
            "interests": interests,
            "num_travelers": random.randint(1, 3),
            "use_multi_agent": False,
        }
        with self.client.post(
            "/api/trips/",
            json=payload,
            headers=self._auth_headers(),
            name="/api/trips/ [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 201, 422):
                resp.failure(f"Unexpected status: {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def get_trip(self):
        trip_id = getattr(self.user, "last_trip_id", None)
        if not trip_id:
            return
        self.client.get(
            f"/api/trips/{trip_id}",
            headers=self._auth_headers(),
            name="/api/trips/{id} [GET]",
        )


class TravelAIUser(HttpUser):
    tasks = [TripPlanningTasks]
    wait_time = between(1, 3)
    token: str = ""
    last_trip_id: str = ""

    def on_start(self):
        # For real load tests, obtain a token from the API.
        # Here we use an env-injected test token.
        import os
        self.token = os.getenv("LOAD_TEST_JWT", "test-token")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test started. Target: 100 concurrent users, ramp-up 60s")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print(f"\n=== Load Test Summary ===")
    print(f"Requests: {stats.num_requests}")
    print(f"Failures: {stats.num_failures}")
    print(f"Median response: {stats.median_response_time}ms")
    print(f"p95 response:    {stats.get_response_time_percentile(0.95)}ms")
    print(f"Failure rate:    {stats.fail_ratio * 100:.1f}%")
