# Docker — Reference (NOT tested end-to-end)

These Docker files are provided **as a reference artifact**. They
document how the FastAPI + CrewAI microservice could be containerized,
but they have **not been run end-to-end** during the project's
development timeline. Treat them as a starting point, not as a
ready-to-run deployment.

## Files

| File | Purpose |
|------|---------|
| `Dockerfile.agents` | Build the FastAPI + CrewAI microservice image |
| `docker-compose.yml` | Compose stack for the agents service |

## Scope — what is and is not covered

**Covered:**
- The FastAPI microservice (`agents_api.main:app`) with its 17 tools,
  orchestrator, router, 4 CrewAI agents, and mermaid tools.
- Health check hitting `/health`.
- Port binding to `127.0.0.1:8001` on the host.

**NOT covered:**
- **Odoo 19**: assumed to run on the host (see below).
- **PostgreSQL 18**: managed by the host Odoo install.
- **The Odoo module `meu_assistente_ia`**: it lives inside Odoo's
  addons path, not in this container.
- **Filestore / attachments**: out of scope for the agents service.

## Assumptions

1. **Odoo runs on the host** (Windows or WSL) at `http://localhost:8069`.
2. The container reaches it via `host.docker.internal:8069`.
   - Docker Desktop for Windows: works out of the box.
   - Docker on Linux/WSL: needs `extra_hosts: host.docker.internal:host-gateway`
     (already set in `docker-compose.yml`).
3. The `.env` file exists at the **repo root** (`../.env` relative to
   this `docker/` folder) and contains at least:
   - `GROQ_API_KEY` (required for LLM calls)
   - `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
4. **`main.py` and `odoo_tools.py` hardcode** `/home/denispy/project-agent-system`
   in `sys.path.append()` and `load_dotenv()`. If you build the image
   from a different context, patch those two lines or mount the .env
   at that path. This is acknowledged in `docs/LIMITATIONS.md` (L7).

## How to run (once Docker is installed)

```bash
# From the repo root
docker compose -f docker/docker-compose.yml up --build

# Verify
curl -s http://127.0.0.1:8001/health | python3 -m json.tool

# Stop
docker compose -f docker/docker-compose.yml down
```

## Why this is not the default deployment

The project's primary deployment target is **direct execution inside
WSL2 Ubuntu 26.04** (see `start_all.sh`). Reasons:

1. Odoo 19's developer workflow assumes a native install for module
   hot-reload and filestore access; containerizing it adds complexity
   without clear benefit for a single-developer thesis prototype.
2. Groq free tier is the primary LLM backend; running the agents
   service as a small container does not change the rate-limit profile.
3. Time-boxed delivery: priority was on functional completeness and
   documented limitations, not on infrastructure.

## Future work

- Containerize Odoo 19 + PostgreSQL 18 in the same compose stack
  (refer to the official `odoo:19` image and a `postgres:18` service).
  - Mount the `meu_assistente_ia` module into `/mnt/extra-addons`.
  - Persist `/var/lib/postgresql/data` and the Odoo filestore as volumes.
  - Seed the database from `odoo_db_*.sql` backups.
- Add a `pytest` service that runs `tests/smoke_test.py` against the
  compose stack.
- Wire the same workflow into GitHub Actions (currently only the lint
  workflow runs in CI).
