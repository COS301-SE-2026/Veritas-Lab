## NFR Traceability Matrix


| ID | Quantified requirement | Tactic in SAS | Test / tool | Target / actual |
|----|-------------------------|----------------|--------------|------------------|
| QR-01 | p95 latency for `POST /api/getCases` at 300 concurrent users | Async FastAPI + asyncpg connection pool | Locust | <400ms / **330ms** |
| QR-02 | Availability over the 30 days before Demo 3 | Scheduled health checks (`.github/workflows/availability.yml`, GitHub Actions) | GitHub Actions run history for `availability.yml` | ≥99.5% / **97.261%** |
| QR-03 | Average accessibility score across primary pages, Dev environment | Semantic markup / component structure in the Next.js frontend | Google Lighthouse, run against `https://veritas-lab-dev.azurewebsites.net` (5 pages) | ≥90 / **88.8** |
| QR-04 | Average performance score across primary pages, Dev environment | Next.js static/SSR rendering, code splitting | Google Lighthouse, run against `https://veritas-lab-dev.azurewebsites.net` (5 pages) | ≥90 / **96.6** |
| QR-05 | Maintainability: codebase maintains >=80% automated test coverage | White-box unit testing (pytest, backend; Jest, frontend); object storage decoupled via boto3's S3-compatible interface (local MinIO, swappable for any S3-compatible provider) | `pytest app/tests/unit --cov=app` (backend); `npm test -- --coverage` (frontend) | ≥80% / **98% backend, 88.92% frontend** |
| QR-06 | Reliability: 99.9% uptime, recovery from critical failure within 5 minutes | Azure App Service Health Check (rollback); same GitHub Actions monitor as QR-02 | uptime half, same run history as QR-02; Azure Portal confirmation (recovery half) | Uptime ≥99.9% / **98.390%**; Recovery ≤5min / **tactic enabled in Azure Portal** |
| QR-07 | Security: user passwords never stored in plaintext or reversibly | bcrypt one-way password hashing | `Backend/app/tests/unit/test_bcrypt_helpers.py` (pytest) | 0 plaintext-recoverable passwords / **verified: hash never equals plaintext, round-trip `checkpw` succeeds, 100% test coverage** |


**Note on QR-02 and QR-06:** our availability (97%) and uptime (98%) are below target because of two incidents in the last 30 days: a GitHub Actions outage on 6 August, and a domain migration around 14-20 August that caused a real outage and a gap in our monitoring. The team manually used the system during that window and can confirm it was reachable.
