from __future__ import annotations
from pathlib import Path
from typing import Tuple
import yaml
from .models import GameState, GameConfig, Card, PlayerState


def load_yaml_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_state_from_config(cfg: dict) -> GameState:
    gcfg = GameConfig(**cfg.get("rules", {}))
    cards_data = cfg.get("cards", [])
    deck = [Card(**c) for c in cards_data if c.get("in_deck", True)]

    p1 = PlayerState(id="P1", hand_limit=cfg.get("hand_limit", 0))
    p2 = PlayerState(id="P2", hand_limit=cfg.get("hand_limit", 0))

    st = GameState(config=gcfg, deck=deck, players={"P1": p1, "P2": p2})
    return st


def load_game(path: str | Path) -> Tuple[GameState, dict]:
    cfg = load_yaml_config(path)
    st = build_state_from_config(cfg)
    return st, cfg
