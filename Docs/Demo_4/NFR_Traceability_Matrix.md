# NFR Traceability Matrix

This matrix traces each quality requirement in the [Non-Functional Requirements](Non_Functional_Requirements.md) to:
1. the architectural tactic in the SAS that is meant to achieve it;
2. the executable test that measures it;
3. the measured result, with a link to the screenshots and raw output in [NFR Testing](NFR_Testing.md).

Every requirement has at least one test, and every tactic listed has a row.

Targets were fixed before the final runs and are stricter than in Demo 3: per-page instead of averaged, higher thresholds, honest denominators, and measured rather than claimed. A miss is reported as a miss.

## 3.3.2 NFR Traceability Matrix

| ID | Quantified requirement | Tactic in SAS | Test / tool | Target / actual |
|---|---|---|---|---|
| QR-01 | p95 latency for `GET /api/getCases` at 300 concurrent users | Async FastAPI + asyncpg connection pool | Locust ([`nfr/performance/locustfile.py`](../../nfr/performance/locustfile.py)) | <300ms / 500ms |
| QR-02 | Availability: uptime of `https://veritaslab.app` over the monitored window (last 30 days, or since monitoring began) | External ping/echo monitoring (UptimeRobot, 5-min multi-region checks, email alerts); Main CD automatic rollback on a failed deployment | UptimeRobot API, [`nfr/availability/uptime_report.py`](../../nfr/availability/uptime_report.py) | ≥ 99.9% / **99.918%** (22.42 days, 26 m 23 s down) |
| QR-03 | Accessibility: Lighthouse accessibility score of **every** primary page (9 pages including logged-in and admin), desktop, median of 3 runs | Semantic markup, labelled form components, design-token colour system | Lighthouse 12.8.2 CLI + [`nfr/web/lighthouse_auth.mjs`](../../nfr/web/lighthouse_auth.mjs) + [`nfr/web/lighthouse_summary.py`](../../nfr/web/lighthouse_summary.py) | ≥ 90 on every page / **6 of 9 pages; lowest 85** (dashboard 86, admin 86, case-page 85) |
| QR-04 | Performance: Lighthouse performance score and Largest Contentful Paint of **every** primary page (same 9 pages and runs) | Next.js server-side rendering, route-level code-splitting, lazy-loaded thumbnails | Same Lighthouse runs as QR-03 | ≥ 90 and LCP ≤ 2.5 s on every page / **7 of 9 pages; lowest 77, LCP 4.75 s** (case-page, workbench) |
| QR-05 | Maintainability: line coverage of the backend (production code, tests excluded) and the frontend (every source file), measured separately | White-box unit testing (pytest, Jest); regression suite required on every PR by the `dev` ruleset (5 checks); S3-compatible storage interface for testability | pytest-cov 7.1.0 `--cov-fail-under=85`; Jest 30 `--coverageThreshold` 85% | Overall **85%** / Overall **95%** |
| QR-06 | Reliability: time to detect an outage, and time to restore service (MTTR) in forced-restart drills and real incidents | Ping/echo detection and alerting (UptimeRobot); Azure App Service container restart; Main CD rollback / manual redeploy | [`nfr/availability/recovery_drill.py`](../../nfr/availability/recovery_drill.py) (3 drills on Dev); [`nfr/availability/uptime_report.py`](../../nfr/availability/uptime_report.py) (real incidents) | Detect ≤ 5 min / **5 min, PASS**; drills ≤ 5 min (3/3) / **⏳**; real incidents ≤ 5 min / **26 m 23 s** |
| QR-07 | Security: stored password format, credential exposure in responses and URLs, auth cookie flags | bcrypt one-way password hashing (cost 12); JWT only in an HttpOnly + Secure cookie | Existing pytest suite (31 tests, runs in CI) + [`nfr/security/test_qr07_passwords.py`](../../nfr/security/test_qr07_passwords.py) + DevTools on production | 100% bcrypt cost ≥ 12 / **4 of 4**; 0 leaking responses / **0 of 5**; 0 credential URL params / **0 of 31 routes**; HttpOnly + Secure / **3 of 3** |


Full evidence, reproduction commands and screenshots for every row: [NFR Testing](NFR_Testing.md).
