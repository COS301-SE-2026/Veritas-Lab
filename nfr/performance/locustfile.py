import os
import re

import requests
from gevent.lock import Semaphore
from locust import HttpUser, between, events, task
from locust.runners import WorkerRunner

HOST = os.environ.get("LOCUST_HOST", "https://veritas-lab-dev.azurewebsites.net")
P95_TARGET_MS = 200
ERROR_RATE_TARGET = 0.01
ENDPOINT = "GET /api/getCases"
SESSION = {}
LOGIN_LOCK = Semaphore()


def session_cookie(host):
    with LOGIN_LOCK:
        if "cookie" not in SESSION:
            token = os.environ.get("LOCUST_TOKEN", "").strip().strip('"')
            if not token:
                resp = requests.post(f"{host}/api/login", timeout=30,
                                     json={"email": os.environ["LOCUST_EMAIL"], "password": os.environ["LOCUST_PASSWORD"]})
                match = re.search(r"JWT_token=([^;]+)", resp.headers.get("set-cookie", ""))
                if not match:
                    raise RuntimeError(f"Login failed: HTTP {resp.status_code}")
                token = match.group(1)
            SESSION["cookie"] = f"JWT_token={token}"
    return SESSION["cookie"]


class DashboardUser(HttpUser):
    host = HOST
    wait_time = between(1, 3)  # think time between requests, like a person using the dashboard

    def on_start(self):
        self.cookie = session_cookie(self.host)

    @task
    def get_cases(self):
        self.client.get("/api/getCases", headers={"Cookie": self.cookie}, name=ENDPOINT)


@events.quitting.add_listener
def check_targets(environment, **_):
    if isinstance(environment.runner, WorkerRunner):
        return  # in distributed runs only the master holds the combined statistics
    stats = environment.stats.get(ENDPOINT, "GET")
    p95 = stats.get_response_time_percentile(0.95) or 0
    error_rate = stats.fail_ratio
    passed = stats.num_requests > 0 and p95 < P95_TARGET_MS and error_rate < ERROR_RATE_TARGET
    print(f"\n[QR-01b] requests={stats.num_requests}  p95={p95:.0f} ms (target < {P95_TARGET_MS} ms)  "
          f"error rate={error_rate:.2%} (target < {ERROR_RATE_TARGET:.0%})  -> {'PASS' if passed else 'FAIL'}")
    environment.process_exit_code = 0 if passed else 1
