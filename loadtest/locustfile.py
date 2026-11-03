import random

from locust import HttpUser, between, task

SEEDED_USERS = [
    {"email": f"user{i}@example.com", "password": "Password123!"} for i in range(1, 6)
]
EVENT_TYPES = ["order", "payment", "delivery"]


class NotificationUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        creds = random.choice(SEEDED_USERS)
        response = self.client.post(
            "/auth/login",
            data={"username": creds["email"], "password": creds["password"]},
        )
        token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def simulate_event(self) -> None:
        event_type = random.choice(EVENT_TYPES)
        self.client.post(f"/simulate/{event_type}", name="/simulate/[type]")

    @task(2)
    def list_notifications(self) -> None:
        # Split stats by the X-Cache header so Redis hits and Postgres misses
        # show up as separate rows with their own latency.
        with self.client.get("/notifications", catch_response=True) as response:
            cache_status = response.headers.get("X-Cache", "UNKNOWN")
            response.request_meta["name"] = f"/notifications [{cache_status}]"

    @task(1)
    def list_events(self) -> None:
        self.client.get("/events")
