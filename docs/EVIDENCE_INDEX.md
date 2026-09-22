
# Evidence and submission index

- **Repository URL:**  https://github.com/ahmeddhussain/BARQ-Task.git
- **Final commit:**  "4cf798981763840121d7dfc3581dd3bf3708f313"
- **Matching CI run:**  https://github.com/ahmeddhussain/BARQ-Task/actions/runs/35610149188
- **Continuous 12-18 minute video URL:**  https://drive.google.com/file/d/18nhAd_d_LIfFLllMIVsxtr8K_7JCEsb4/view?usp=sharing
- **Challenge receipt ID:**  "f6ba7867c2374a8ab5caf709038594ca"
- **Starting video commit:**  "434e2cd0669c9f15156e48ee5cc1e09e0f034350"
- **Later documentation-only commits:**  commit `final doc edits`

## Requirement Mapping

| Requirement | File / Output / Command | Video Timestamp |
| :--- | :--- | :--- |
| **Clean starting state** | `git status` (shows clean working tree) | [00:10] |
| **Starting commit verification** | `git log -1 --oneline` | [00:15] |
| **Build/start stopped environment** | `docker compose up -d` | [00:30] |
| **Service health verification** | `docker compose ps` (all services healthy) | [00:40] |
| **Process liveness probe** | `curl -i http://localhost:8080/health` | [01:00] |
| **PostgreSQL & Redis readiness** | `curl -i http://localhost:8080/ready` | [01:20] |
| **Create PostgreSQL record** | `curl -X POST -H 'Content-Type: application/json' ... /records` | [01:30] |
| **List PostgreSQL records** | `curl http://localhost:8080/records` | [01:40] |
| **Redis-backed shared counter** | `curl http://localhost:8080/counter` | [01:50] |
| **Load-balanced backend identity** | `for i in {1..6}; do curl ... /instance; done` (proves app-01 & app-02) | [02:00] |
| **Failure demonstration (Stop backend)** | `docker compose stop app-01` | [03:00] |
| **Measure traffic & errors during failure** | `for i in {1..6}; do curl ... /instance; done` (proves 200 continued traffic & 504 errors) | [03:10] |
| **Backend recovery verification** | `docker compose start app-01` | [04:15] |
| **Volume persistence proof (Postgres)** | `docker compose restart postgres` & check `/records` | [04:30] |
| **Volume persistence proof (Redis)** | `docker compose restart redis` & check `/counter` | [05:00] |
| **Automated environment validation** | `./validate.py` (all endpoints, isolation, loadbalancing) | [05:30] |
| **Automated failure test** | `./failure_test.py` (chaos engineering failover) | [06:00] |
| **Historical log finding (Retries)** | `grep ', ' logs/access.log \| head -n 3` | [07:00] |
| **Historical log finding (Errors)** | `grep 'Connection refused' logs/error.log \| head -n 3` | [07:45] |
| **First-run challenge execution** | `./video_challenge.sh` | [08:40] |
| **Live challenge diagnosis & fix** | Diagnosed fault and fixed without `docker compose down` | [09:00] |
| **Post-challenge health verification** | `curl http://localhost:8080` and instance loop | [09:35] |
| **Live public port migration (8080 ➔ 8090)** | Updated `docker compose` & `docker compose up -d nginx` | [10:15] |
| **Verify NGINX works on port 8090** | `curl http://localhost:8090/` (8080 fails, 8090 returns 200) | [10:30] |
| **Live scale: Add third instance (app-03)** | Added `app-03` to compose & `nginx.conf`, rebuilt/started | [11:00] |
| **Prove all 3 instances respond** | `for i in {1..9}; do curl ... /instance; done` (shows app-01, 02, 03) | [12:00] |
| **Rerun validation on port 8090** | `./validate.py 8090` | [12:45] |
| **Inspect Git status and diff on screen** | `git status` and `git diff` | [13:20] |
| **Commit on screen & display hash** | `git commit -m "..."` and `git log -1` | [13:30] |
| **Push live commits to GitHub** | `git push` | [14:00] |