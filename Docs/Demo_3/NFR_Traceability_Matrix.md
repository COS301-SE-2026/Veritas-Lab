## 3.3.1 Quality Requirement Mapping

| Quality Requirement | Architectural Decision |
|---|---|
| QR-01: p95 latency <400ms at 300 concurrent users | Async FastAPI + asyncpg connection pool |
| QR-02: Availability >=99.5% over 30 days | Scheduled health checks (`availability.yml`, GitHub Actions) |
| QR-03: Average accessibility score >=90 across primary pages | Semantic markup / component structure in the Next.js frontend |
| QR-04: Average performance score >=90 across primary pages | Next.js static/SSR rendering, code splitting |
| QR-05: Maintainability -- >=80% automated test coverage | White-box unit testing (pytest, backend; Jest, frontend); object storage decoupled via boto3's S3-compatible interface (local MinIO, swappable for any S3-compatible provider) |
| QR-06: Reliability - 99.9% uptime, recovery within 5 minutes | Azure App Service Health Check (rollback); same GitHub Actions monitor as QR-02 |
| QR-07: Security - user passwords never stored in plaintext or reversibly | bcrypt one-way password hashing |

## 3.3.2 NFR Traceability Matrix


| ID | Quantified requirement | Tactic in SAS | Test / tool | Target / actual |
|----|-------------------------|----------------|--------------|------------------|
| QR-01 | p95 latency for `POST /api/getCases` at 300 concurrent users | Async FastAPI + asyncpg connection pool | Locust | <400ms / **330ms** |
| QR-02 | Availability over the 30 days before Demo 3 | Scheduled health checks (`.github/workflows/availability.yml`, GitHub Actions) | GitHub Actions run history for `availability.yml` | >=99.5% / **97.261%** |
| QR-03 | Average accessibility score across primary pages, Dev environment | Semantic markup / component structure in the Next.js frontend | Google Lighthouse, run against `https://veritas-lab-dev.azurewebsites.net` (5 pages) | >=90 / **88.8** |
| QR-04 | Average performance score across primary pages, Dev environment | Next.js static/SSR rendering, code splitting | Google Lighthouse, run against `https://veritas-lab-dev.azurewebsites.net` (5 pages) | >=90 / **96.6** |
| QR-05 | Maintainability: codebase maintains >=80% automated test coverage | White-box unit testing (pytest, backend; Jest, frontend); object storage decoupled via boto3's S3-compatible interface (local MinIO, swappable for any S3-compatible provider) | `pytest app/tests/unit --cov=app` (backend); `npm test -- --coverage` (frontend) | >=80% / **98% backend, 88.92% frontend** |
| QR-06 | Reliability: 99.9% uptime, recovery from critical failure within 5 minutes | Azure App Service Health Check (rollback); same GitHub Actions monitor as QR-02 | uptime half, same run history as QR-02; Azure Portal confirmation (recovery half) | Uptime >=99.9% / **98.390%**; Recovery ≤5min / **tactic enabled in Azure Portal** |
| QR-07 | Security: user passwords never stored in plaintext or reversibly | bcrypt one-way password hashing | `Backend/app/tests/unit/test_bcrypt_helpers.py` (pytest) | 0 plaintext-recoverable passwords / **verified: hash never equals plaintext, round-trip `checkpw` succeeds, 100% test coverage** |


**Note on QR-02 and QR-06:** our availability (97%) and uptime (98%) are below target because of two incidents in the last 30 days: a GitHub Actions outage on 6 August, and a domain migration around 14-20 August that caused a real outage and a gap in our monitoring. The team manually used the system during that window and can confirm it was reachable.

### QR-02 detail: Availability

**Method:** MTTF/MTTR-based availability, per the formula from L29 (Software Quality Assurance):

```
Availability = MTTF / (MTTF + MTTR) x 100%
```

where MTTF is the mean time between failures and MTTR is the mean time to recovery, both measured from the timestamped run history of the `availability.yml` scheduled health check (checks fire roughly every 47 minutes).

**Result (30-day window, 2026-08-04 to 2026-09-03):**

| Metric | Value |
|---|---|
| MTTF | 293.94 hours |
| MTTR | 8.28 hours |
| MTBF | 302.21 hours |
| **Availability** | **97.261%** |
| Corroborating simple uptime ratio (successful/total checks) | 98.394% (490/498) |
| Failure episodes counted | 1 |

**Target:** >=99.5% (not yet met -- see "What this means" below).

**Evidence and exclusions applied**, both required to get from the raw run history to the number above:

1. **Excluded (external cause, not our fault):** 3 checks on 2026-08-06 between 16:00-19:00 UTC, caused by a publicly reported GitHub Actions degradation that day. Removed from both the numerator and denominator entirely, same treatment as if the check had never run.
2. **Blackout (monitoring itself paused, no data either way):** 2026-08-15 05:52 UTC to 2026-08-20 08:29 UTC. `availability.yml` was intentionally disabled while investigating a real issue, per commits `5fc577c` ("Changes to the availability check while we investigate") and `dff3ffc` ("Updating/repairing the availability check"). This period is excluded from the MTTF/MTTR interval math (clipped out, not counted as uptime or downtime) since there is no data for it -- but it is NOT removed from the underlying incident: the genuine failure streak observed just before the pause (2026-08-14 23:59 to 2026-08-15 05:52, ~5.9 hours) is kept and counted as real downtime, since it reflects an actual detected problem rather than an excuse.

**What this means:** 97.261% is below the >=99.5% target. The follow-up action is to identify what caused the 2026-08-14 failure streak (suspected link to a domain migration around that date) and fix the underlying cause.
