# graph_memory_database

This workspace is organized around a shared-plus-scoped memory system for multiple assistants, exposed through a Python backend that can be called by a Cloudflare Worker and ingested through the `BigGulp` frontend.

## Architecture

- Shared memory lives in the cross-entity graph and is visible to all assistants.
- Scoped memory is isolated by assistant/member key using `agent_id`.
- The REST API in `backend/api_server.py` is the main HTTP surface for:
  - Cloudflare Workers
  - `BigGulp`
  - Gemini function calling
  - any other assistant that should read/write memories over HTTP
- The MCP server in `backend/mcp_server.py` exposes the same memory model to Claude-style MCP clients.

## Workspace Layout

```text
graph_memory_database/
  artifacts/
    memory/
      scoped/
  backend/
    api_server.py
    mcp_server.py
    memory_core.py
    entity_registry.py
    gemini_integration.py
    env_utils.py
    crewai/
  frontend/
    BigGulp/
  governance/
    agent_roster.yml
    agents/
  migrations/
    cortex_migration.py
    glitch_kernel_migration.py
    nova_kernel_migration.py
  scripts/
    export_memory_artifacts.py
    readme_seed.py
    preflight.cmd
  workshop/
    prototypes/
    research/
  data/
    mem0_memories.json
    chatgpt_kernel.txt
    cortex_resp.json
    .cortex_progress.json
  archive/
    constellation_graph_memory.py
    constellation_graph_init.py
    multi_ai_graph_memory.py
    unknown_draft.py
```

## Shared vs Scoped Memory

### Shared

Use shared memory for facts that should be traversable across assistants.

REST endpoint:

```text
POST /memory/shared
```

Example payload:

```json
{
  "content": "Claude: Harvey prefers synthesis over exhaustive recall.",
  "category": "system/technical"
}
```

### Scoped

Use scoped memory for assistant-private context.

REST endpoint:

```text
POST /memory/member
```

Example payload:

```json
{
  "content": "Harvey wants this preserved only for Gemini.",
  "member": "gemini",
  "category": "project_milestone",
  "use_graph": false
}
```

Valid primary members:

- `claude`
- `nova`
- `gemini`
- `mephistopheles`

Additional scoped satellites and governance agents are defined canonically in `backend/entity_registry.py`.

Governance-scoped stewards currently include:

- `linter_agent`
- `entity_registry_keeper`
- `migration_agent`
- `project_architect`
- `workflows_orchestrator`

Use `GET /entities` when a client needs the full memory-capable registry and capability map instead of only the member hierarchy.

## Cloudflare Worker Integration

Your Worker should call the backend REST API, not the archive scripts.

Recommended pattern:

- Read `CONSTELLATION_API_URL` from Worker env/secrets.
- Read `CONSTELLATION_API_KEY` from Worker secrets.
- Optionally read `GET /config` at startup or deploy time to discover auth and batch settings.
- Call:
  - `POST /memory/shared` for shared writes
  - `POST /memory/member` for scoped writes
  - `POST /memory/batch` for batched shared/scoped writes
  - `POST /memory/search` for retrieval
  - `GET /memory/all` for inspection
  - `GET /members` to discover valid member keys
  - `GET /entities` to discover the canonical registry and scope capabilities
  - `GET /config` to discover capabilities

Example request headers:

```text
Authorization: Bearer <CONSTELLATION_API_KEY>
Content-Type: application/json
```

Example Worker-friendly batch payload:

```json
{
  "items": [
    {
      "scope": "shared",
      "content": "Claude: Harvey wants shared architectural decisions preserved globally.",
      "category": "system/technical",
      "client_id": "shared-1"
    },
    {
      "scope": "member",
      "member": "gemini",
      "content": "Keep this only in Gemini's scoped memory.",
      "category": "project_milestone",
      "use_graph": false,
      "client_id": "gemini-1"
    }
  ],
  "stop_on_error": false
}
```

Batch responses return per-item success or failure so a Worker can retry only the failed writes.

CORS/auth notes:

- `Authorization: Bearer <CONSTELLATION_API_KEY>` is supported across the Worker-facing API.
- `OPTIONS` requests are allowed for browser-based callers.
- CORS origins are controlled by `CORS_ORIGINS`.
- Batch size is controlled by `CONSTELLATION_MAX_BATCH_SIZE` and exposed through `GET /config`.

## BigGulp

`frontend/BigGulp` is the ingestion UI.

It is intended to:

- submit shared memories
- submit scoped memories
- run redundancy checks before ingest
- point at the same REST API your Worker uses

Frontend env variables live in Cloudflare Pages or local frontend env files:

- `VITE_API_URL`
- `VITE_API_KEY`

See `frontend/BigGulp/.env.example`.

## Environment Setup

Copy `.env.example` to `.env.local` for local use and fill in your actual secrets.

Relevant variables:

- `MEM0_API_KEY`
- `PINECONE_API_KEY`
- `CONSTELLATION_API_KEY`
- `CONSTELLATION_API_URL`
- `GEMINI_API_KEY`
- `CORS_ORIGINS`
- `CONSTELLATION_MAX_BATCH_SIZE`

Tracked secret-bearing files were sanitized. Use `.env.local` or shell environment variables for real credentials.

## Canonical Artifact Export

The canonical memory export flow is:

```bash
python scripts/export_memory_artifacts.py
python build_graph.py
```

Generated outputs are written to `artifacts/memory/`:

- `manifest.json`
- `latest_shared.json`
- `latest_memories.json`
- `scoped/<member>.json`
- `memory_graph.html`

`build_graph.py` now prefers the consolidated artifact export and falls back to the legacy `data/mem0_memories.json` input only when the new export has not been generated yet.

## Running the Backend

### REST API

```bash
python backend/api_server.py
```

or

```bash
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

### MCP Server

```bash
python backend/mcp_server.py
```

### Gemini Integration

```bash
python backend/gemini_integration.py
```

## Seed / Migration Scripts

### Seed foundational memories

```bash
python scripts/readme_seed.py --dry-run
python scripts/readme_seed.py
```

### Migrations

```bash
python migrations/cortex_migration.py --dry-run
python migrations/glitch_kernel_migration.py --dry-run
python migrations/nova_kernel_migration.py --dry-run
```

## Governance and CI/CD

Governance ownership and coordination live in:

- `governance/agent_roster.yml`
- `governance/agents/*.agent.md`

Active GitHub workflows live in `.github/workflows/`:

- `ci-active-dev.yml` validates backend compilation and the BigGulp production build
- `deploy-frontend.yml` deploys `frontend/BigGulp` to Cloudflare Pages on pushes to `main`
- `export-memory-artifacts.yml` exports the canonical memory artifacts and uploads them as CI artifacts

The frontend deployment workflow expects these GitHub secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_PAGES_PROJECT_NAME`
- `VITE_API_URL`
- `VITE_API_KEY`

The artifact export workflow expects:

- `MEM0_API_KEY`

## Workshop Partition

`workshop/` is the phased surface for experimental or pre-promotion material. Runtime code, canonical exports, and deployable automation stay in the active root surface until a future promotion or relocation plan says otherwise.

## Notes

- `archive/` holds older prototypes and drafts that were removed from the active root.
- `data/` holds exports, source corpora, and migration artifacts.
- `artifacts/memory/` is the dedicated store for generated memory outputs and graph artifacts.
- `workshop/` is reserved for non-runtime experiments, drafts, and research.
- `.gitignore` now excludes local env files, caches, frontend build output, and local dependencies.
- `scripts/preflight.cmd` now runs the maintained seed script instead of embedding secrets.
