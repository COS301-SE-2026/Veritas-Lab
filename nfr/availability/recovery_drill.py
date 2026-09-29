"""
QR-06 Recovery drill: measures how long Veritas Lab takes to serve requests again after a forced restart.

Health probe (no account needed):
  POST /api/login with an email that does not exist -> 401 proves the frontend proxy, the backend
  and the database all answer; anything else (5xx, 404, timeout) counts as DOWN.
  GET /landing -> 200 proves the frontend serves pages.

Steps: start the script, click Restart on the Dev App Service in the Azure portal, confirm,
then press Enter. It polls every 5 s and stops after 3 healthy probes in a row.

Target: healthy again within 300 s of the restart.

Run from the repo root with the drill number (1, 2 or 3):
  Backend/venv/Scripts/python.exe nfr/availability/recovery_drill.py 1
"""
import csv
import sys
import time
from datetime import datetime, timezone

import httpx

BASE = "https://veritas-lab-dev.azurewebsites.net"
INTERVAL, NEEDED_OK, GIVE_UP, TARGET = 5, 3, 15 * 60, 300
DRILL = sys.argv[1] if len(sys.argv) > 1 else "1"
CSV_PATH = f"Docs/Demo_4/evidence/QR-06-drill-{DRILL}.csv"
PROBE_LOGIN = {"email": "nfr-probe@example.com", "password": "Probe-Password-123!"}


def probe(client):
    try:
        api = client.post(f"{BASE}/api/login", json=PROBE_LOGIN).status_code
    except httpx.HTTPError:
        api = "no-response"
    try:
        web = client.get(f"{BASE}/landing").status_code
    except httpx.HTTPError:
        web = "no-response"
    return api == 401 and web == 200, api, web


def stamp(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M:%S UTC")


with httpx.Client(timeout=10) as client:
    ok, api, web = probe(client)
    print(f"Baseline: api={api} web={web} -> {'HEALTHY' if ok else 'NOT HEALTHY'}")
    if not ok:
        sys.exit("Service is not healthy before the drill - wait and try again.")
    input("Click Restart on the Dev App Service in the Azure portal, confirm, then press Enter here... ")
    t0 = time.time()
    rows, first_down, streak, recovered = [], None, 0, None
    while time.time() - t0 < GIVE_UP:
        t = time.time()
        ok, api, web = probe(client)
        rows.append([stamp(t), round(t - t0, 1), api, web, "UP" if ok else "DOWN"])
        print(f"{stamp(t)}  +{t - t0:6.1f}s  api={api} web={web}  {'UP' if ok else 'DOWN'}", flush=True)
        if not ok and first_down is None:
            first_down = t
        streak = streak + 1 if ok and first_down else 0
        if streak == NEEDED_OK:
            recovered = rows[-NEEDED_OK][1]  # seconds from the restart to the first probe of the healthy streak
            break
        if first_down is None and t - t0 > TARGET:
            break  # no downtime seen at all within 5 minutes
        time.sleep(max(0, INTERVAL - (time.time() - t)))

with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([["time", "seconds_since_restart", "api_status", "web_status", "state"], *rows])

print(f"\nRestart clicked    : {stamp(t0)}")
if first_down is None:
    print("No downtime observed at 5 s resolution - the restart may not have happened; repeat the drill.")
    sys.exit(1)
print(f"First failed probe : +{first_down - t0:.0f} s")
if recovered is None:
    print(f"QR-06 drill {DRILL}: not healthy after {GIVE_UP} s -> FAIL")
    sys.exit(1)
print(f"Healthy again      : +{recovered:.0f} s")
print(f"QR-06 drill {DRILL}: recovered in {recovered:.0f} s (target <= {TARGET} s) -> {'PASS' if recovered <= TARGET else 'FAIL'}")
sys.exit(0 if recovered <= TARGET else 1)
