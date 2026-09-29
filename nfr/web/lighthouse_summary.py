import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path("Docs/Demo_4/evidence/lighthouse")
CSV_PATH = Path("Docs/Demo_4/evidence/QR-03-04-lighthouse-summary.csv")
# Part of the final URL each page must end on; anything else means a redirect (e.g. to /login)
EXPECTED = {"landing": "/landing", "login": "/login", "register": "/register", "dashboard": "/dashboard",
            "help": "/help", "admin": "/admin", "audit-log": "/audit-log",
            "case-page": "/case-page/", "workbench": "/workbench/"}

runs = defaultdict(list)
for report in sorted(OUT.glob("*.report.json")):
    lhr = json.loads(report.read_text(encoding="utf-8"))
    if lhr["configSettings"].get("extraHeaders"):  # never commit the session cookie
        lhr["configSettings"]["extraHeaders"] = None
        report.write_text(json.dumps(lhr), encoding="utf-8")
    cats = lhr["categories"]
    runs[report.name.split("-run")[0]].append({
        "file": report.name,
        "url": lhr.get("finalDisplayedUrl") or lhr.get("finalUrl", ""),
        "a11y": round((cats["accessibility"]["score"] or 0) * 100),
        "perf": round((cats["performance"]["score"] or 0) * 100),
        "lcp": lhr["audits"]["largest-contentful-paint"].get("numericValue", float("inf")) / 1000,
    })

rows, all_pass = [], True
for page, page_runs in runs.items():
    median_run = sorted(page_runs, key=lambda r: r["perf"])[len(page_runs) // 2]
    a11y = statistics.median(r["a11y"] for r in page_runs)
    perf = statistics.median(r["perf"] for r in page_runs)
    lcp = statistics.median(r["lcp"] for r in page_runs)
    redirected = any(EXPECTED.get(page, "") not in r["url"] for r in page_runs)
    qr03 = "PASS" if a11y >= 90 and not redirected else "FAIL"
    qr04 = "PASS" if perf >= 90 and lcp <= 2.5 and not redirected else "FAIL"
    all_pass &= qr03 == qr04 == "PASS"
    rows.append([page, len(page_runs), a11y, perf, f"{lcp:.2f}", qr03, qr04,
                 "REDIRECTED" if redirected else "ok", median_run["file"]])

header = ["page", "runs", "accessibility", "performance", "lcp_s", "QR-03", "QR-04", "final_url", "median_run"]
print(" | ".join(header))
for row in rows:
    print(" | ".join(str(c) for c in row))
with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([header, *rows])
print(f"\nLowest accessibility: {min(r[2] for r in rows)}  |  lowest performance: {min(r[3] for r in rows)}  |  "
      f"slowest LCP: {max(float(r[4]) for r in rows):.2f} s")
print("ALL PAGES PASS" if all_pass else "AT LEAST ONE PAGE MISSES A TARGET")
sys.exit(0 if all_pass else 1)