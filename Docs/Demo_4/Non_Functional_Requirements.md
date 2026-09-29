# Non-Functional Requirements

Every quality requirement below is quantified: it has a measurable target, and a test that anyone can re-run. The tests, results and screenshots are in [NFR Testing](NFR_Testing.md), and the traceability to architectural tactics is in the [NFR Traceability Matrix](NFR_Traceability_Matrix.md).

## Quality requirements

### QR-01: Performance under load
Both parts are measured on the Dev Azure deployment, which runs in South Africa North with the same Docker images as production. The load is generated from South Africa, where the users are.

- **QR-01a (entry pages):** `GET /landing` and `GET /login`, the pages every visitor reaches first, must **each** answer with a **95th-percentile response time below 200 ms** and an **error rate below 1%**, while **300 concurrent visitors** use the site for **5 minutes**.
- **QR-01b (case API):** `GET /api/getCases`, the case list behind the dashboard, must answer with a **95th-percentile response time below 200 ms** and an **error rate below 1%**, while **300 concurrent logged-in users** use the system for **5 minutes**.

### QR-02: Availability
`https://veritaslab.app` must be up **at least 99.9%** of the monitored window. The window is the last 30 days, or the time since monitoring started if that is shorter. Availability is measured by UptimeRobot HTTP(S) checks **every 5 minutes** from several regions.

### QR-03: Accessibility
**Every** primary page must score **at least 90** on Google Lighthouse Accessibility (desktop preset, median of 3 runs). This covers **9 pages**, including the logged-in and admin-only pages: landing, login, register, dashboard, help, admin, audit log, case page and evidence workbench.

### QR-04: Performance (page load)
**Every** primary page must score **at least 90** on Google Lighthouse Performance, **and** have a Largest Contentful Paint of **2.5 s or less**. It uses the same 9 pages and the same runs as QR-03.

### QR-05: Maintainability
Automated test line coverage must be **at least 85% for the backend** and **at least 85% for the frontend**, measured separately.
- **Backend:** all production code under `Backend/app` (`api`, `auth`, `core`, `ai`, `training`), with test code excluded, measured by the unit test suite.
- **Frontend:** every source file under `frontend/src`, including files no test imports, except type declarations and the brand style-guide page. Measured by the full Jest suite.

### QR-06: Reliability (recoverability)
Outages must be **detected within 5 minutes**, and service must be **restored within 5 minutes** (MTTR ≤ 5 minutes). This must hold for **3 out of 3** forced-restart drills, **and** for every real incident in the monitoring window.

### QR-07: Security
**100%** of stored user passwords must be bcrypt one-way hashes with a **cost factor of at least 12**, never plaintext. **No** API response or URL may expose a password, password hash or session token, and the authentication cookie must always be **HttpOnly** and **Secure**.

