from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import random

from packages.engine.loader import load_game
from packages.engine.models import GameState, PlayerState, Slot, Card
from packages.engine.engine import initialize_game
from .cards_index import _load_cards_index


ROOT = Path(__file__).resolve().parents[3]


def _new_slots(n: int) -> List[Slot]:
    return [Slot() for _ in range(n)]


def _place_starters(state: GameState, cfg: dict) -> None:
    starters = cfg.get("starters", {})
    # Bosses start in hand; allow entries as ID string or dict with overrides
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
                    # Fallback: use as-is
                    p.hand.append(Card(**entry))
                    continue
            except Exception:
                # Ignore malformed entry
                pass


def _is_boss_card(c: Card) -> bool:
    name = (c.name or "").lower()
    ctype = (getattr(c, "type", "") or "").lower()
    notes = (getattr(c, "notes", "") or "").lower()
    text = f"{name} {ctype} {notes}"
    return ("boss" in text) or ("босс" in text)


def _guess_owner_from_text(text: str) -> Optional[str]:
    t = (text or "").lower()
    if "p1" in t or "п1" in t:
        return "P1"
    if "p2" in t or "п2" in t:
        return "P2"
    return None


def _ensure_bosses_in_hands(st: GameState) -> None:
    """Move boss cards into players' hands at game start.
    Prefer owner-indicated boss first, then any remaining boss."""
    have = {pid: any(_is_boss_card(c) for c in st.players[pid].hand) for pid in ("P1", "P2")}

    def take_from_deck(predicate) -> Optional[Card]:
        for i, c in enumerate(st.deck):
            if predicate(c):
                return st.deck.pop(i)
        return None

    for pid in ("P1", "P2"):
        if have[pid]:
            continue
        owned = take_from_deck(lambda c: _is_boss_card(c) and _guess_owner_from_text((c.name or "") + " " + (getattr(c, "notes", "") or "")) == pid)
        if owned:
            st.players[pid].hand.append(owned)
            have[pid] = True

    for pid in ("P1", "P2"):
        if have[pid]:
            continue
        any_boss = take_from_deck(lambda c: _is_boss_card(c))
        if any_boss:
            st.players[pid].hand.append(any_boss)
            have[pid] = True


def _ensure_slots(state: GameState, count: int) -> None:
    for pid in ("P1", "P2"):
        p = state.players.get(pid) or PlayerState(id=pid, hand_limit=6)
        if len(p.slots) < count:
            p.slots.extend(_new_slots(count - len(p.slots)))
        state.players[pid] = p


def _build_state_from_csv(MAX_SLOTS: int) -> Tuple[GameState, dict]:
    """Load game state with cards from CSV file using unified loader.
    Returns (state, config)."""
    csv_path = ROOT / "config" / "cards.csv"
    st, cfg = load_game(
        str(ROOT / "config" / "default.yaml"),
        csv_path=csv_path,
    )
    # Merge any shelf back to deck for a clean start
    if getattr(st, "shelf", None):
        if len(st.shelf) > 0:
            st.deck.extend(st.shelf)
            st.shelf.clear()
    _ensure_slots(st, MAX_SLOTS)
    _place_starters(st, cfg)
    random.shuffle(st.deck)
    _ensure_bosses_in_hands(st)
    initialize_game(st)
    return st, cfg

