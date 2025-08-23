from __future__ import annotations
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import time
import random
import csv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from engine.loader import load_game, load_yaml_config, build_state_from_config
from engine.models import GameState, PlayerState, Slot, Card
from engine.engine import initialize_game

# Socket.IO сервер (ASGI)
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app_fastapi = FastAPI()
app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app = socketio.ASGIApp(sio, other_asgi_app=app_fastapi)

ROOT = Path(__file__).resolve().parents[2]
MAX_SLOTS = 9
INIT_VISIBLE_SLOTS = 6

rooms: Dict[str, dict] = {}
sid_index: Dict[str, Dict[str, str]] = {}


def _new_slots(n: int) -> List[Slot]:
    return [Slot() for _ in range(n)]


def _place_starters(state: GameState, cfg: dict) -> None:
    starters = cfg.get("starters", {})
    # Боссы стартуют в руке, а не на столе
    # Разрешаем указывать стартеры как ID строкой или как словарь с id/оверрайдами
    cards_index = _load_cards_index()
    for pid, cards in starters.items():
        p = state.players[pid]
        for entry in cards:
            try:
                if isinstance(entry, str):
                    data = cards_index.get(entry)
                    if data:
                        p.hand.append(Card(**data))
                        continue
                elif isinstance(entry, dict):
                    cid = entry.get("id")
                    if cid and cid in cards_index:
                        base = dict(cards_index[cid])
                        base.update(entry)
                        p.hand.append(Card(**base))
                        continue
                    # Фоллбэк: использовать данные как есть
                    p.hand.append(Card(**entry))
                    continue
            except Exception:
                # В крайнем случае пропускаем некорректную запись
                pass


def _is_boss_card(c: Card) -> bool:
    name = (c.name or "").lower()
    ctype = (getattr(c, "type", "") or "").lower()
    notes = (getattr(c, "notes", "") or "").lower()
    text = f"{name} {ctype} {notes}"
    return ("boss" in text) or ("босс" in text)


def _guess_owner_from_text(text: str) -> Optional[str]:
    t = (text or "").lower()
    # Евристика по обозначению владельца: P1/П1, P2/П2
    if "p1" in t or "п1" in t:
        return "P1"
    if "p2" in t or "п2" in t:
        return "P2"
    return None


def _ensure_bosses_in_hands(st: GameState) -> None:
    """Перемещает босс-карты в руки соответствующих игроков при старте партии.
    Если в руках уже есть босс – ничего не делаем. Сначала ищем по владельцу,
    затем берём любой оставшийся босс, если владелец не указан в названии."""
    # Уже есть боссы в руках?
    have = {pid: any(_is_boss_card(c) for c in st.players[pid].hand) for pid in ("P1", "P2")}

    def take_from_deck(predicate) -> Optional[Card]:
        for i, c in enumerate(st.deck):
            if predicate(c):
                return st.deck.pop(i)
        return None

    # Сначала пытаемся взять по владельцу
    for pid in ("P1", "P2"):
        if have[pid]:
            continue
        owned = take_from_deck(lambda c: _is_boss_card(c) and _guess_owner_from_text((c.name or "") + " " + (getattr(c, "notes", "") or "")) == pid)
        if owned:
            st.players[pid].hand.append(owned)
            have[pid] = True

    # Затем берём любой оставшийся босс, если всё ещё нет
    for pid in ("P1", "P2"):
        if have[pid]:
            continue
        any_boss = take_from_deck(lambda c: _is_boss_card(c))
        if any_boss:
            st.players[pid].hand.append(any_boss)
            have[pid] = True


def _ensure_slots(state: GameState, count: int = MAX_SLOTS) -> None:
    for pid in ("P1", "P2"):
        p = state.players.get(pid) or PlayerState(id=pid, hand_limit=6)
        if len(p.slots) < count:
            p.slots.extend(_new_slots(count - len(p.slots)))
        state.players[pid] = p


def _build_state_from_csv() -> Tuple[GameState, dict]:
    """Load game state with cards from CSV file."""
    # Load game configuration from YAML (without cards)
    cfg = load_yaml_config(ROOT / "config" / "default.yaml")
    
    # Load cards from CSV
    csv_path = ROOT / "config" / "cards.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Card data file not found: {csv_path}")
    
    # Load game state with cards from CSV
    st, _ = load_game(
        str(ROOT / "config" / "default.yaml"),
        csv_path=csv_path
    )
    # Rules/UI: Reserve (Rejected) starts empty; entire deck goes to Draw pile.
    # Some loaders may prefill a visible shelf; merge it back into the deck for start state.
    if getattr(st, "shelf", None):
        if len(st.shelf) > 0:
            st.deck.extend(st.shelf)
            st.shelf.clear()
    
    # Initialize game state
    _ensure_slots(st, MAX_SLOTS)
    _place_starters(st, cfg)
    random.shuffle(st.deck)
    _ensure_bosses_in_hands(st)
    initialize_game(st)
    return st, cfg


def _parse_abl_text(abl_text: str) -> dict | int:
    text = (abl_text or "").strip()
    if not text:
        return 0
    parts = [p.strip() for p in text.replace(',', ';').split(';') if p.strip()]
    kv: dict = {}
    on_enter: dict = {}
    for p in parts:
        if ':' in p:
            k, v = p.split(':', 1)
            k = k.strip().lower()
            v = v.strip()
            try:
                num = int(float(v)) if v not in ("all", "n/a") else v
            except Exception:
                num = v
            if k in {"steal", "gain", "bribe"} and isinstance(num, int):
                on_enter[k] = num
            else:
                kv[k] = num
        else:
            kv[p] = 1
    if on_enter:
        kv["on_enter"] = on_enter
    return kv or 0


def _load_caste_map() -> Dict[str, str]:
    csv_path = ROOT / "config" / "cards.csv"
    result: Dict[str, str] = {}
    if not csv_path.exists():
        return result
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = (row.get("ID") or row.get("Id") or "").strip()
            if not cid:
                continue
            caste = (row.get("Каста") or row.get("Caste") or "").strip()
            if caste:
                result[cid] = caste
    return result


def _load_cards_index() -> Dict[str, dict]:
    """Загрузить все карты из CSV в индекс по ID без фильтрации по InDeck/В_колоде.
    Возвращает dict[card_id] -> card_data (совместимую с engine.models.Card).
    """
    csv_path = ROOT / "config" / "cards.csv"
    index: Dict[str, dict] = {}
    if not csv_path.exists():
        return index
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            cid = (row.get("ID") or row.get("Id") or f"card_{i}").strip()
            if not cid:
                continue
            name = (row.get("Name") or row.get("Название") or f"Card {i}").strip()
            ctype = (row.get("Type") or row.get("Тип") or "common").strip().lower()
            faction = (row.get("Faction") or row.get("Фракция") or "neutral").strip().lower()
            caste = (row.get("Caste") or row.get("Каста") or "").strip() or None
            def _to_int(v, default=0):
                try:
                    return int(float(v))
                except Exception:
                    return default
            hp = _to_int(row.get("HP", 1), 1) if row.get("HP") else 1
            atk = _to_int(row.get("ATK", 0), 0) if row.get("ATK") else 0
            defend = _to_int(row.get("Defend", 0), 0) if row.get("Defend") else 0
            notes = (row.get("Description") or row.get("Описание") or "").strip()
            abl_text = (row.get("ABL") or "").strip()
            data = {
                "id": cid,
                "name": name,
                "type": ctype,
                "faction": faction,
                "caste": caste,
                "hp": hp,
                "atk": atk,
                "d": defend,
                "notes": notes,
            }
            if abl_text:
                data["abl"] = _parse_abl_text(abl_text)
            index[cid] = data
    return index


def _serialize_slot_for_view(s: Slot, for_owner: bool) -> dict:
    if for_owner:
        return s.model_dump()
    # Для оппонента показываем только открытые карты; закрытые считаем пустыми
    if s.face_up and s.card is not None:
        return s.model_dump()
    return {"card": None, "face_up": False, "muscles": 0}


def _filtered_view(state: GameState, viewer_pid: str, visible_you: int, visible_op: int) -> dict:
    you = state.players[viewer_pid]
    op_pid = "P2" if viewer_pid == "P1" else "P1"
    op = state.players[op_pid]
    you_board = [_serialize_slot_for_view(s, True) for s in you.slots[:visible_you]]
    op_board = [_serialize_slot_for_view(s, False) for s in op.slots[:visible_op]]
    return {
        "you": {
            "id": viewer_pid,
            "hand": [c.model_dump() for c in you.hand],
            "board": you_board,
            "tokens": you.tokens.model_dump(),
        },
        "opponent": {
            "id": op_pid,
            # Кол-во карт в руке оппонента скрываем; отдаём только открытые карты стола
            "board": op_board,
            # Отдаём только количество карт в руке оппонента, без идентификаторов
            "handCount": len(op.hand),
            "tokens": op.tokens.model_dump(),
        },
        "shared": {
            "deckCount": len(state.deck),
            "shelfCount": len(state.shelf),
            # Список карт на полке (открытая информация): полные данные для отображения
            "shelf": [c.model_dump() for c in state.shelf],
            "discardCount": len(state.discard_out_of_game),
        },
        "meta": {
            "visible_slots": {"you": visible_you, "opponent": visible_op},
            "turn": {
                "active": state.active_player,
                "number": state.turn_number,
                "phase": state.phase.value if hasattr(state.phase, "value") else str(state.phase),
            },
        },
    }


def _log(room_id: str, kind: str, msg: str, actor: Optional[str] = None) -> None:
    r = rooms.get(room_id)
    if not r:
        return
    st: GameState = r.get("state")
    entry = {
        "id": len(r.setdefault("log", [])) + 1,
        "t": time.time(),
        "kind": kind,
        "msg": msg,
        "actor": actor,
        "turn": getattr(st, "turn_number", 0),
        "active": getattr(st, "active_player", None),
    }
    r["log"].append(entry)


async def _emit_views(room_id: str) -> None:
    r = rooms.get(room_id)
    if not r:
        return
    st: GameState = r["state"]
    vs = r.get("visible_slots", {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS})
    for pid, sid in r.get("seats", {}).items():
        if not sid:
            continue
        view = _filtered_view(st, pid, visible_you=vs.get(pid, INIT_VISIBLE_SLOTS), visible_op=vs.get("P2" if pid == "P1" else "P1", INIT_VISIBLE_SLOTS))
        # append last N log entries
        view.setdefault("meta", {})["log"] = (r.get("log") or [])[-50:]
        await sio.emit("state", view, to=sid)


@app_fastapi.get("/")
async def root():
    return {
        "ok": True,
        "service": "KINGPIN 2P Server",
        "health": "/health",
        "socket_io": "/socket.io/",
    }


@app_fastapi.get("/health")
async def health():
    return {"ok": True}


@sio.event
async def connect(sid, environ):
    await sio.emit("connected", {"sid": sid}, to=sid)


@sio.event
async def join_room(sid, data):
    room = data.get("room", "demo")
    # Always use CSV as the single source of truth for card data
    # Подключаемся к комнате
    await sio.enter_room(sid, room)

    if room not in rooms:
        # Инициализация комнаты
        state, cfg = _build_state_from_csv()
        rooms[room] = {
            "state": state,
            "cfg": cfg,
            "seats": {"P1": None, "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": [],
        }
        # Debug: log and print deck/shelf sizes after CSV load
        try:
            print(f"[ROOM {room}] CSV loaded: shelf={len(state.shelf)}, deck={len(state.deck)}")
        except Exception:
            pass
        _log(room, "load", f"CSV loaded: shelf={len(state.shelf)}, deck={len(state.deck)}")
        _log(room, "room", f"Room created (source=CSV)")
        _log(room, "turn_start", f"Game started. Active: {state.active_player} · Turn {state.turn_number}")

    r = rooms[room]
    # Назначение места
    seat: Optional[str] = None
    if r["seats"].get("P1") is None:
        seat = "P1"
    elif r["seats"].get("P2") is None:
        seat = "P2"
    else:
        await sio.emit("room_full", {"room": room}, to=sid)
        return

    r["seats"][seat] = sid
    sid_index[sid] = {"room": room, "pid": seat}
    _log(room, "join", f"{seat} joined", actor=seat)
    await sio.emit("joined", {"room": room, "seat": seat, "source": r.get("source", "yaml"), "visibleSlots": r["visible_slots"][seat]}, to=sid)
    await _emit_views(room)


@sio.event
async def remove_op_shield(sid, data):
    """Remove a shield from the opponent's slot without refunding money to them.
    Used to simulate the opponent destroying a defender token.
    Client sends: { slotIndex }
    """
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    op_pid = "P2" if pid == "P1" else "P1"
    try:
        si = int(data.get("slotIndex", -1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[op_pid].slots):
        return
    slot = st.players[op_pid].slots[si]
    if slot.muscles > 0:
        slot.muscles -= 1
        _log(room, "token", f"{pid} destroyed 1 shield on {op_pid}'s slot {si+1}", actor=pid)
        await _emit_views(room)


@sio.event
async def add_shield_only(sid, data):
    """Add shield to slot without changing reserve money.
    Used for internal shield distribution.
    Client sends: { slotIndex, count }
    """
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    st.players[pid].slots[si].muscles += max(0, count)
    _log(room, "token", f"{pid} +{max(0, count)} shield on slot {si+1} (internal)", actor=pid)
    await _emit_views(room)


@sio.event
async def remove_shield_only(sid, data):
    """Remove shield from slot without changing reserve money.
    Used for internal shield distribution.
    Client sends: { slotIndex, count }
    """
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    st.players[pid].slots[si].muscles = max(0, st.players[pid].slots[si].muscles - max(0, count))
    _log(room, "token", f"{pid} -{max(0, count)} shield on slot {si+1} (internal)", actor=pid)
    await _emit_views(room)


@sio.event
async def add_shield_from_reserve(sid, data):
    """Atomically move money from player's reserve to a shield on a slot.
    This represents spending reserve money to place shields. Does not affect bank directly.
    Client sends: { slotIndex, count }
    """
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    n = max(0, count)
    if n <= 0:
        return
    p = st.players[pid]
    take = min(n, max(0, p.tokens.reserve_money))
    if take <= 0:
        return
    p.tokens.reserve_money -= take
    p.slots[si].muscles += take
    _log(room, "token", f"{pid} spent {take} money → +{take} shield on slot {si+1}", actor=pid)
    await _emit_views(room)


@sio.event
async def remove_shield_to_reserve(sid, data):
    """Atomically move shield(s) from a slot back to player's reserve.
    Internal redistribution: does not affect bank directly.
    Client sends: { slotIndex, count }
    """
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    n = max(0, count)
    if n <= 0:
        return
    p = st.players[pid]
    give = min(n, max(0, p.slots[si].muscles))
    if give <= 0:
        return
    p.slots[si].muscles -= give
    p.tokens.reserve_money += give
    _log(room, "token", f"{pid} returned {give} shield → +{give} money to reserve from slot {si+1}", actor=pid)
    await _emit_views(room)


@sio.event
async def cursor(sid, data):
    """Relay normalized cursor coordinates within the board to the other player in the same room.
    Client sends: { room, x, y, visible }
    x,y are expected in [0,1]. visible toggles rendering on receiver side.
    """
    info = sid_index.get(sid)
    if not info:
        return
    room = info.get("room")
    pid = info.get("pid")
    if not room:
        return
    try:
        x = float(data.get("x", 0))
        y = float(data.get("y", 0))
        visible = bool(data.get("visible", True))
    except Exception:
        x, y, visible = 0.0, 0.0, False
    payload = {"pid": pid, "x": max(0.0, min(1.0, x)), "y": max(0.0, min(1.0, y)), "visible": visible}
    # Broadcast to the room except the sender
    await sio.emit("cursor", payload, room=room, skip_sid=sid)


@sio.event
async def disconnect(sid):
    info = sid_index.pop(sid, None)
    if not info:
        return
    room = info.get("room")
    pid = info.get("pid")
    r = rooms.get(room)
    if not r:
        return
    if r["seats"].get(pid) == sid:
        r["seats"][pid] = None


@sio.event
async def draw(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    if not st.deck:
        # Перетасовать полку в колоду, если есть
        if st.shelf:
            random.shuffle(st.shelf)
            st.deck.extend(st.shelf)
            st.shelf.clear()
    if not st.deck:
        await sio.emit("error", {"msg": "deck_empty"}, to=sid)
        return
    card = st.deck.pop(0)
    st.players[pid].hand.append(card)
    _log(room, "draw", f"{pid} drew a card", actor=pid)
    await _emit_views(room)


@sio.event
async def move_card(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    from_zone = data.get("from")
    to_zone = data.get("to")
    from_index = data.get("fromIndex")
    to_index = data.get("toIndex")

    p = st.players[pid]
    if from_zone == "hand" and to_zone == "slot":
        try:
            card = p.hand.pop(int(from_index))
        except Exception:
            return
        si = int(to_index)
        if si < 0 or si >= len(p.slots):
            p.hand.append(card)
            return
        slot = p.slots[si]
        if slot.card is None:
            slot.card = card
            slot.face_up = True
            _log(room, "play", f"{pid} played {card.name} to slot {si+1}", actor=pid)
        else:
            # обмен
            p.hand.append(slot.card)
            slot.card = card
            slot.face_up = True
            _log(room, "swap", f"{pid} swapped card into slot {si+1}", actor=pid)
    elif from_zone == "slot" and to_zone == "hand":
        si = int(from_index)
        if si < 0 or si >= len(p.slots):
            return
        slot = p.slots[si]
        if slot.card is None:
            return
        card = slot.card
        p.hand.append(card)
        slot.card = None
        slot.muscles = 0
        _log(room, "pickup", f"{pid} picked up {card.name} from slot {si+1}", actor=pid)
    elif from_zone == "slot" and to_zone == "slot":
        si = int(from_index)
        di = int(to_index)
        if si < 0 or si >= len(p.slots) or di < 0 or di >= len(p.slots):
            return
        s_from = p.slots[si]
        s_to = p.slots[di]
        s_from.card, s_to.card = s_to.card, s_from.card
        s_from.face_up = True if s_from.card else s_from.face_up
        s_to.face_up = True if s_to.card else s_to.face_up
        _log(room, "rearrange", f"{pid} rearranged slots {si+1} ⇄ {di+1}", actor=pid)
    elif to_zone == "discard":
        # Перенос в общий отбой (вне игры)
        if from_zone == "hand":
            try:
                card = p.hand.pop(int(from_index))
            except Exception:
                return
            st.discard_out_of_game.append(card)
            _log(room, "discard", f"{pid} discarded {card.name}", actor=pid)
        elif from_zone == "slot":
            si = int(from_index)
            if si < 0 or si >= len(p.slots):
                return
            slot = p.slots[si]
            if slot.card is None:
                return
            card = slot.card
            st.discard_out_of_game.append(card)
            slot.card = None
            slot.muscles = 0
            _log(room, "discard", f"{pid} discarded {card.name} from slot {si+1}", actor=pid)
    elif to_zone == "shelf":
        # Полка (временное откладывание карт, могут вернуться в игру)
        if from_zone == "hand":
            try:
                card = p.hand.pop(int(from_index))
            except Exception:
                return
            st.shelf.append(card)
            _log(room, "shelve", f"{pid} placed {card.name} on shelf", actor=pid)
        elif from_zone == "slot":
            si = int(from_index)
            if si < 0 or si >= len(p.slots):
                return
            slot = p.slots[si]
            if slot.card is None:
                return
            card = slot.card
            st.shelf.append(card)
            slot.card = None
            slot.muscles = 0
            _log(room, "shelve", f"{pid} moved {card.name} from slot {si+1} to shelf", actor=pid)
    elif from_zone == "shelf" and to_zone == "hand":
        # Взять карту с полки в руку
        if pid != st.active_player:
            await sio.emit("error", {"msg": "not_your_turn"}, to=sid)
            return
        try:
            idx = int(from_index)
            if idx < 0 or idx >= len(st.shelf):
                return
        except Exception:
            return
        card = st.shelf.pop(idx)
        p.hand.append(card)
        _log(room, "unshelve", f"{pid} took {card.name} from shelf to hand", actor=pid)
    elif from_zone == "shelf" and to_zone == "slot":
        # Положить карту с полки на пустой слот
        if pid != st.active_player:
            await sio.emit("error", {"msg": "not_your_turn"}, to=sid)
            return
        try:
            idx = int(from_index)
            si = int(to_index)
        except Exception:
            return
        if idx < 0 or idx >= len(st.shelf) or si < 0 or si >= len(p.slots):
            return
        slot = p.slots[si]
        if slot.card is not None:
            # Не кладём поверх занятых слотов
            return
        card = st.shelf.pop(idx)
        slot.card = card
        slot.face_up = True
        _log(room, "unshelve", f"{pid} played {card.name} from shelf to slot {si+1}", actor=pid)
    else:
        # Неподдерживаемая комбинация
        return
    await _emit_views(room)


@sio.event
async def end_turn(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    if pid != st.active_player:
        await sio.emit("error", {"msg": "not_your_turn"}, to=sid)
        return
    prev = st.active_player
    st.active_player = "P2" if st.active_player == "P1" else "P1"
    st.turn_number += 1
    # Сброс фазы к началу хода
    try:
        from packages.engine.models import TurnPhase
        st.phase = TurnPhase.upkeep
    except Exception:
        pass
    _log(room, "end_turn", f"{prev} ended turn. Now {st.active_player}'s turn · Turn {st.turn_number}")
    await _emit_views(room)


@sio.event
async def flip_card(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    si = int(data.get("slotIndex", -1))
    if si < 0 or si >= len(st.players[pid].slots):
        return
    slot = st.players[pid].slots[si]
    if slot.card is None:
        return
    slot.face_up = not slot.face_up
    name = slot.card.name if slot.card else "Card"
    _log(room, "flip", f"{pid} flipped {name} {'up' if slot.face_up else 'down'}", actor=pid)
    await _emit_views(room)


@sio.event
async def add_token(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    kind = (data.get("kind") or "shield").lower()
    count = int(data.get("count", 1))
    if kind == "shield":
        si = int(data.get("slotIndex", -1))
        if 0 <= si < len(st.players[pid].slots):
            st.players[pid].slots[si].muscles += max(0, count)
            _log(room, "token", f"{pid} +{max(0, count)} shield on slot {si+1}", actor=pid)
    elif kind == "money":
        st.players[pid].tokens.reserve_money += max(0, count)
        _log(room, "token", f"{pid} +{max(0, count)} money", actor=pid)
    await _emit_views(room)


@sio.event
async def remove_token(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    kind = (data.get("kind") or "shield").lower()
    count = int(data.get("count", 1))
    if kind == "shield":
        si = int(data.get("slotIndex", -1))
        if 0 <= si < len(st.players[pid].slots):
            st.players[pid].slots[si].muscles = max(0, st.players[pid].slots[si].muscles - max(0, count))
            _log(room, "token", f"{pid} -{max(0, count)} shield on slot {si+1}", actor=pid)
    elif kind == "money":
        st.players[pid].tokens.reserve_money = max(0, st.players[pid].tokens.reserve_money - max(0, count))
        _log(room, "token", f"{pid} -{max(0, count)} money", actor=pid)
    await _emit_views(room)


@sio.event
async def shuffle_deck(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    random.shuffle(st.deck)
    _log(room, "shuffle", "Deck shuffled")
    await _emit_views(room)


@sio.event
async def set_visible_slots(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    n = int(data.get("count", INIT_VISIBLE_SLOTS))
    n = max(6, min(MAX_SLOTS, n))
    r.setdefault("visible_slots", {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS})
    r["visible_slots"][pid] = n
    _log(room, "ui", f"{pid} set visible slots to {n}", actor=pid)
    await _emit_views(room)


@sio.event
async def reset_room(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    r = rooms.get(room)
    if not r:
        return
    # Optionally override room source if provided by requester
    try:
        req_source = (data.get("source") or "").lower()
    except Exception:
        req_source = ""
    if req_source in {"yaml", "csv"}:
        r["source"] = req_source
    # Rebuild state based on the (possibly updated) room's source
    # Always use CSV as the single source of truth for card data
    state, cfg = _build_state_from_csv()
    # Preserve seats but reset state and visibility
    r["state"] = state
    r["cfg"] = cfg
    r["visible_slots"] = {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS}
    r.setdefault("log", []).clear()
    # Debug: log and print deck/shelf sizes after reset
    try:
        print(f"[ROOM {room}] After reset: shelf={len(state.shelf)}, deck={len(state.deck)}")
    except Exception:
        pass
    _log(room, "load", f"After reset: shelf={len(state.shelf)}, deck={len(state.deck)}")
    _log(room, "reset", f"Room reset (source={r.get('source', 'csv').upper()})")
    _log(room, "turn_start", f"Game started. Active: {state.active_player} · Turn {state.turn_number}")
    # Re-emit 'joined' meta so clients refresh any cached UI derived from it
    seats = r.get("seats", {})
    for pid, psid in seats.items():
        if psid:
            await sio.emit("joined", {"room": room, "seat": pid, "source": r.get("source", "yaml"), "visibleSlots": r["visible_slots"][pid]}, to=psid)
    await _emit_views(room)
