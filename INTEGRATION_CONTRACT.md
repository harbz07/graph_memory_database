# soulOS Integration Contract

`graph_memory_database` is intended to run as an external memory dependency for `soul-os`.

## Service Role

- Expose shared + scoped memory APIs over HTTP.
- Serve as a memory backend for Workers and external clients.
- Keep memory model and agent wiring versioned independently from `soul-os` runtime code.

## Environment Contract (Consumer Side)

Expected in `soul-os` runtime:

- `CONSTELLATION_API_URL`
- `CONSTELLATION_API_KEY`

Request headers:

- `Authorization: Bearer <CONSTELLATION_API_KEY>`
- `Content-Type: application/json`

## Endpoint Contract

The following endpoints are expected for integration:

- `GET /config`
- `GET /entities`
- `POST /memory/search`
- `POST /memory/shared`
- `POST /memory/member`
- `POST /memory/batch`
- `GET /memory/all`

## Degradation Expectations

- Clients should tolerate temporary unavailability and degrade gracefully.
- Memory retrieval failures must not crash agent orchestration pipelines.
