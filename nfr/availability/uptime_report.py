"""
QR-02 Availability and QR-06 Recovery: UptimeRobot report for https://veritaslab.app.

Reads the monitor and its up/down log from the UptimeRobot API using the read-only monitor key
that is already public in the README badge, then computes over the monitored window
(the last 30 days, or since the monitor was created if that is later):
  uptime %      = (monitored time - downtime) / monitored time
  MTTR          = mean duration of the down incidents
  MTTF          = time up / number of incidents
  availability  = MTTF / (MTTF + MTTR)          (L29 formula, as used in Demo 3)

Targets:
  QR-02  uptime >= 99.9 % over the window
  QR-06  outages detected within 5 min (check interval) and every incident recovered within 5 min

Run from the repo root:
  Backend/venv/Scripts/python.exe nfr/availability/uptime_report.py
"""
import csv
import os
import time
from datetime import datetime, timezone

import httpx

KEY = os.environ.get("UPTIMEROBOT_KEY", "m803931074-e5ec07b7d06780aa83293f0b")  # read-only, public in README badge
CSV_PATH = "Docs/Demo_4/evidence/QR-02-06-incidents.csv"
WINDOW = 30 * 24 * 3600
DOWN, PAUSED = 1, 99


def utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def hms(seconds):
    return f"{int(seconds // 3600)}h {int(seconds % 3600 // 60)}m {int(seconds % 60)}s"


resp = httpx.post("https://api.uptimerobot.com/v2/getMonitors", timeout=30, data={
    "api_key": KEY, "format": "json", "logs": 1, "logs_limit": 100, "custom_uptime_ratios": "7-30"})
monitor = resp.json()["monitors"][0]

now = int(time.time())
start = max(monitor["create_datetime"], now - WINDOW)  # the monitor may be younger than 30 days
incidents, paused = [], 0
for log in monitor["logs"]:
    begin, end = log["datetime"], log["datetime"] + log["duration"]
    in_window = max(0, min(end, now) - max(begin, start))
    if log["type"] == DOWN and in_window:
        incidents.append({"start": utc(begin), "duration_s": log["duration"], "in_window_s": in_window,
                          "reason": f"{log['reason']['code']} {log['reason']['detail']}",
                          "recovered_within_5_min": "PASS" if log["duration"] <= 300 else "MISS"})
    elif log["type"] == PAUSED:
        paused += in_window

monitored = now - start - paused
downtime = sum(i["in_window_s"] for i in incidents)
uptime = 100 * (monitored - downtime) / monitored
n = len(incidents)
mttr = sum(i["duration_s"] for i in incidents) / n if n else 0
mttf = (monitored - downtime) / n if n else monitored
availability = 100 * mttf / (mttf + mttr)
ratio_7, ratio_30 = monitor["custom_uptime_ratio"].split("-")

qr02 = uptime >= 99.9
detect = monitor["interval"] <= 300
recover = all(i["recovered_within_5_min"] == "PASS" for i in incidents)

print(f"Monitor        : {monitor['friendly_name']} ({monitor['url']}), HTTP(S) check every {monitor['interval']} s")
print(f"Window         : {utc(start)} -> {utc(now)}  ({monitored / 86400:.2f} days monitored)")
print(f"UptimeRobot    : 7-day {ratio_7} %, 30-day {ratio_30} % (UptimeRobot counts the full 30 days)")
print(f"Downtime       : {hms(downtime)} in {n} incident(s)")
print(f"Uptime         : {uptime:.3f} % over the monitored window   -> QR-02 (>= 99.9 %): {'PASS' if qr02 else 'FAIL'}")
print(f"MTTR / MTTF    : {hms(mttr)} / {mttf / 3600:.2f} h   (MTBF {(mttf + mttr) / 3600:.2f} h)")
print(f"Availability   : MTTF / (MTTF + MTTR) = {availability:.3f} %")
print(f"Budget left    : {hms(max(0, monitored * 0.001 - downtime))} more downtime before uptime drops below 99.9 %")
print("Incidents      :")
for i in incidents:
    print(f"  {i['start']}  down {hms(i['duration_s'])}  {i['reason']}  -> recovered within 5 min: {i['recovered_within_5_min']}")
print(f"QR-06 detection within 5 min (check interval {monitor['interval']} s): {'PASS' if detect else 'FAIL'}")
print(f"QR-06 every real incident recovered within 5 min: {'PASS' if recover else 'MISS'}")

with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["start", "duration_s", "in_window_s", "reason", "recovered_within_5_min"])
    writer.writeheader()
    writer.writerows(incidents)
