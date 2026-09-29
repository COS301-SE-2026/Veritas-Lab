## QR-07 – Password protection

| | |
|---|---|
| **Requirement** | 100% of stored user passwords are bcrypt hashes with cost factor ≥ 12 (never plaintext); 0 API responses or URLs expose a password, hash or token; the `JWT_token` cookie is always `HttpOnly` and `Secure`. |
| **Demo 3 target** | "Passwords never stored in plaintext or reversibly", verified by one unit test (`test_bcrypt_helpers.py`). |
| **Why this is stricter** | Checks **every** user row in the real database and the cost factor, plus every auth response, every URL parameter in the API and the cookie flags, locally **and** on production. |
| **Tactic (SAS)** | bcrypt one-way hashing (Blowfish-based, per-password salt, cost 12) in `Backend/app/auth/auth.py` (`hash_password`, `verify_password`); JWT carried only in an HttpOnly + Secure cookie, never in a URL. |
| **Tools** | (1) Existing pytest suite, which also runs in CI on every PR: `unit/test_bcrypt_helpers.py`, `unit/test_login.py`, register/login/change_password tests in `integration/test_int_auth.py`. (2) System-level test `nfr/security/test_qr07_passwords.py` (pytest + httpx + asyncpg). (3) Browser DevTools on production. |
| **Environment** | Local `docker compose` stack, commit `72bd94f`, run 2026-09-28 23:22 (SAST); cookie flags confirmed on production `https://veritaslab.app`. |

**How to reproduce**
```bash
docker compose up -d backend
# (1) existing suite: DB_HOST/STORAGE_URL point the tests at the dockerised services from the host
cd Backend && DB_HOST=localhost STORAGE_URL=http://localhost:9000 venv/Scripts/python.exe -m pytest app/tests/unit/test_bcrypt_helpers.py app/tests/unit/test_login.py app/tests/integration/test_int_auth.py -k "bcrypt or login or register or change_password" --asyncio-mode=auto -v; cd ..
# (2) system-level checks (from the repo root)
Backend/venv/Scripts/python.exe -m pytest nfr/security/test_qr07_passwords.py -v -s -rA
# (3) stored hash prefixes (only the first 7 characters are shown)
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT username, userrole, left(userpassword, 7) AS hash_prefix, length(userpassword) AS hash_length FROM \"Users_DB\".\"Users\" ORDER BY username;"'
```
Note: `/refreshToken` only re-issues a cookie in the last 50% of a token's 30-minute lifetime, so test (2) signs a near-expiry token with the local `JWT_SECRET` to force a real refresh. The existing integration test `test_integration_refresh_token_near_expiry` uses the same approach.

**Results**

| Check | Target | Actual | Verdict |
|---|---|---|---|
| Existing auth test suite | all pass | 31 / 31 passed | PASS |
| (a) Stored passwords that are bcrypt, cost ≥ 12 | 100% | **4 / 4 (100%)**: ADMIN, INVESTIGATOR, USER and the test account, all `$2b$12$`, length 60 | PASS |
| (b) Responses exposing a password or hash (register, login, fetchUsers, refreshToken, changePassword) | 0 of 5 | **0 of 5** | PASS |
| (c) URL parameters carrying credentials | 0 | **0** across 31 routes (only `case_id`, `comment_id`, `media_id`, `user_id`) | PASS |
| (d) Cookie flags on register, login, refresh | HttpOnly + Secure on 3 / 3 | **3 / 3** (`HttpOnly; Secure; SameSite=none; Max-Age=1800`) | PASS |
| Production cookie (`veritaslab.app`) | HttpOnly + Secure | **HttpOnly true, Secure true**, SameSite None | PASS |

**Why 100% holds beyond the local accounts:** the code has exactly two ways to write `UserPassword`, and both store the output of `hash_password()`:
- `insert_user()` (`auth.py:357`), called by `/register` (`auth.py:672`) and by the seeding script (`Backend/init_db.py:15, 27, 37`);
- the `/changePassword` update (`auth.py:1462`).

The only other write is the SQL seed of the `SYSTEM_INIT` system account (see Findings).

**Evidence**

![QR-07 existing suite](imgs/QR-07-existing-suite.png)
![QR-07 system-level test](imgs/QR-07-pytest-pass.png)
![QR-07 stored hashes](imgs/QR-07-db-hashes.png)
![QR-07 production cookie flags](imgs/QR-07-prod-cookie.png)

Raw output: [`evidence/QR-07-existing-suite.txt`](evidence/QR-07-existing-suite.txt), [`evidence/QR-07-output.txt`](evidence/QR-07-output.txt), [`evidence/QR-07-junit.xml`](evidence/QR-07-junit.xml)

**Scope note:** email addresses and usernames are stored in plaintext because login looks users up by email; only passwords are hashed.
