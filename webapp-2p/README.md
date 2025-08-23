# KINGPIN 2-Player Web App

A Vite + React + TypeScript client for the KINGPIN 2-player manual table. Connects to the FastAPI + Socket.IO backend.

## Features

- 2 boards (you/opponent), 6–9 visible slots per side
- Hand zone with drag-and-drop to board
- Move card: hand → slot, slot ↔ slot, slot → hand, to discard
- Flip card on your board by double-click
- Add/remove shield tokens on slots, add/remove reserve money
- Draw, shuffle, and per-player visible slot count
- Real-time filtered state: your hand visible only to you

## Requirements

- Node 18+
- Python 3.10+

## Config (optional)

Create `.env` in this folder to override defaults:

```
VITE_SERVER_URL=http://localhost:8000
VITE_ROOM=demo
```

See `.env.example` for defaults.

## Install & Run

Backend (from repo root):

```
pip install -r requirements.txt
uvicorn packages.server.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (from `webapp-2p/`):

```
npm install
npm run dev
```

Open http://localhost:5173 in two browser tabs to simulate two players. Each tab will auto-join the same room and receive a seat (P1/P2).

## Notes

- Room fills at 2 seats; a 3rd tab will be rejected.
- Change visible slots with the slider (6–9). Changes apply per-player.
- Discard accepts drops from your hand or your slots.
- Use YAML or CSV data source (UI toggle in footer, affects only on first join for a room).
