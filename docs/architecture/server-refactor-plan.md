# Architecture — Server Refactor Plan (packages/server)

Goal: reduce `main.py` size and improve testability by separating concerns without changing behavior.

## Target layout

- `packages/server/main.py` — app bootstrap (FastAPI, Socket.IO wiring)
- `packages/server/api/routes.py` — REST routes (`/`, `/health`)
- `packages/server/socket/handlers.py` — Socket.IO event handlers (connect/join/attack/etc.)
- `packages/server/services/state.py` — state build/filter/serialize helpers
- `packages/server/services/cards_index.py` — cards index and caching

## Steps

1) Extract pure helpers first (no I/O):
   - `_serialize_slot_for_view`, `_filtered_view` → `services/state.py`
   - `_load_caste_map`, `_load_cards_index` → `services/cards_index.py`
2) Move FastAPI routes to `api/routes.py` and import `router` in `main.py`.
3) Move Socket.IO handlers to `socket/handlers.py` and register in `main.py`.
4) Keep function names and signatures; update imports only. Add unit tests for new modules.

Constraints: zero behavior change, green existing tests.
