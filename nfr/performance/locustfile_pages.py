import os

from locust import HttpUser, between, events, task
from locust.runners import WorkerRunner

HOST = os.environ.get("LOCUST_HOST", "https://veritas-lab-dev.azurewebsites.net")
P95_TARGET_MS = 200
ERROR_RATE_TARGET = 0.01
PAGES = ["GET /landing", "GET /login"]


class Visitor(HttpUser):
    # A visitor arriving at the site: mostly the landing page, sometimes the login page. No account needed.
    host = HOST
    wait_time = between(1, 3)

    @task(1)
    def login_page(self):
        self.client.get("/login", name="GET /login")


@events.quitting.add_listener
def check_targets(environment, **_):
    if isinstance(environment.runner, WorkerRunner):
        return  # in distributed runs only the master holds the combined statistics
    results = []
    for name in PAGES:
        stats = environment.stats.get(name, "GET")
        p95 = stats.get_response_time_percentile(0.95) or 0
        ok = stats.num_requests > 0 and p95 < P95_TARGET_MS and stats.fail_ratio < ERROR_RATE_TARGET
        results.append(ok)
        print(f"[QR-01a] {name}: requests={stats.num_requests}  p95={p95:.0f} ms  "
              f"error rate={stats.fail_ratio:.2%}  -> {'PASS' if ok else 'FAIL'}")
    total = environment.stats.total
    print(f"[QR-01a] all pages: requests={total.num_requests}  p95={total.get_response_time_percentile(0.95) or 0:.0f} ms  "
          f"error rate={total.fail_ratio:.2%}  (targets: p95 < {P95_TARGET_MS} ms, errors < {ERROR_RATE_TARGET:.0%})  "
          f"-> {'PASS' if all(results) else 'FAIL'}")
    environment.process_exit_code = 0 if all(results) else 1
