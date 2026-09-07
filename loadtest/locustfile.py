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
        self.client.get("/notifications")

    @task(1)
    def list_events(self) -> None:
        self.client.get("/events")
