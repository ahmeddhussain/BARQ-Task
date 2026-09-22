
# Evidence and submission index

- **Repository URL:** https://github.com/ahmeddhussain/BARQ-Task.git
- **Final commit:** 
- **Matching CI run:** [(Link to final green GitHub Actions run)](https://github.com/ahmeddhussain/BARQ-Task/actions/runs/35610149188)
- **Continuous 12-18 minute video URL:** (Link to YouTube/Drive)
- **Challenge receipt ID:** (Paste the ID from `.assessment/challenge.json` after running the challenge)
- **Starting video commit:** (The commit hash before you start recording)
- **Later documentation-only commits:** (List any commits made after the video just to update this file)

## Requirement Mapping

| Requirement | File / Output | Commit Hash | Video Timestamp |
| :--- | :--- | :--- | :--- |
| Baseline commit before changes | Initial Git Commit | [Commit Hash] | N/A |
| Progressive Git history | `git log` | [Commit Hash] | `00:00` |
| Block direct NGINX access to DBs | `docker-compose.yml` (networks) | [Commit Hash] | N/A |
| Use named PostgreSQL volume | `docker-compose.yml` (volumes) | [Commit Hash] | N/A |
| Avoid root user | `Dockerfile` | [Commit Hash] | N/A |
| Ignore secret files | `.gitignore`, `.dockerignore` | [Commit Hash] | N/A |
| Green CI Run | `.github/workflows/ci.yml` | [Commit Hash] | N/A |
| Service Health (Pre-flight) | `docker compose ps` | [Commit Hash] | `01:45` |
| Endpoints test & Load Balancing | `curl` commands | [Commit Hash] | `03:30` |
| Failure recovery (Stop backend) | `docker compose stop app-01` | [Commit Hash] | `06:00` |
| Record survives recreation | POST, Restart DB, GET | [Commit Hash] | `07:30` |
| Validation & Failure Scripts | `./validate.py`, `./failure_test.py` | [Commit Hash] | `08:45` |
| Historical log finding | `grep ', ' logs/access.log` | [Commit Hash] | `09:30` |
| Runtime Challenge Fix | `./video_challenge.sh` | [Commit Hash] | `11:00` |
| Live Port Change (8080 to 8090) | `.env`, `docker compose up -d nginx` | [Commit Hash] | `13:30` |
| Live Scale to 3 Instances | `docker-compose.yml`, `nginx.conf` | [Commit Hash] | `15:30` |