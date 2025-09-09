from __future__ import annotations
from pathlib import Path
from typing import Tuple, List, Dict, Any
import yaml
import csv
from .models import GameState, GameConfig, Card, PlayerState, Slot
from .config import get_csv_columns, get_path


def load_yaml_config(path: str | Path) -> dict:
    """Load only game configuration from YAML, excluding cards."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Remove cards from config as they'll be loaded from CSV
    if 'cards' in cfg:
        del cfg['cards']
    return cfg


def load_cards_from_csv(csv_path: str | Path, include_all: bool = False) -> List[Card]:
    """Load card data exclusively from CSV file (English-only schema).

    Args:
        csv_path: Path to CSV file
        include_all: If True, include all cards regardless of InDeck status
    """
    cards = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Helper: robust int parsing (accept floats like '0.25' and tokens like 'n/a')
            def _to_int(v, default=0):
                try:
                    s = str(v).strip()
                    if not s or s.lower() in {"n/a", "na"}:
                        return default
                    return int(float(s))
                except Exception:
                    return default

            # Helper function to get first available column value
            def _get_column_value(field: str, default: Any = None) -> Any:
                for col in get_csv_columns(field):
                    if col in row and row[col]:
                        return row[col]
                return default
            
            # Determine if the card should be in the deck (English markers only)
            # Support multiple column names and ✓/✗ markers
            indeck_raw = (_get_column_value('in_deck') or '').strip()
            indeck_l = indeck_raw.lower()
            if indeck_raw in {'✓', '✔', '+'} or indeck_l in {'yes', 'true', '1', 'y'}:
                in_deck = True
            elif indeck_raw in {'✗', 'x', '-'} or indeck_l in {'no', 'false', '0', 'n'}:
                in_deck = False
            else:
                # Default to including the card if unclear
                in_deck = True
            if not in_deck and not include_all:
                continue
            
            # Map CSV columns to card attributes using unified column mappings
            card_data = {
                'id': _get_column_value('id') or f"card_{len(cards)}",
                'name': _get_column_value('name') or f"Card {len(cards)}",
                'type': (_get_column_value('type') or 'common').lower(),
                'faction': (_get_column_value('faction') or 'neutral').lower(),
                # Terminology: primary 'clan' only
                'clan': (_get_column_value('clan') or '').strip() or None,
                'hp': _to_int(_get_column_value('hp', 1), 1),
                'atk': _to_int(_get_column_value('atk', 0), 0),
                'd': _to_int(_get_column_value('defend', 0), 0),
                'price': _to_int(_get_column_value('price', 0), 0),
                'corruption': _to_int(_get_column_value('corruption', 0), 0),
                'rage': _to_int(_get_column_value('rage', 0), 0),
                'notes': (_get_column_value('notes') or '').strip(),
                # Optional pair-based synergy bonuses per card (default 0)
                'pair_hp': _to_int(_get_column_value('pair_hp', 0), 0),
                'pair_d': _to_int(_get_column_value('pair_d', 0), 0),
                'pair_r': _to_int(_get_column_value('pair_r', 0), 0),
            }
            # No legacy mirroring; 'caste' removed
            
            # Parse ABL if present
            abl_text = (_get_column_value('abl') or '').strip()
            if abl_text:
                card_data['abl'] = _parse_abl_text(abl_text)
                
            cards.append(Card(**card_data))
    return cards


def _parse_abl_text(abl_text: str) -> dict | int:
    """Parse ABL text into structured format."""
    text = (abl_text or "").strip()
    if not text:
        return 0
        
    parts = [p.strip() for p in text.replace(',', ';').split(';') if p.strip()]
    kv = {}
    on_enter = {}
    
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


def build_state_from_config(cfg: dict, cards: List[Card]) -> GameState:
    """Build game state from config and pre-loaded cards."""
    gcfg = GameConfig(**cfg.get("rules", {}))
    
    # Create players with hand limits from config
    hand_limit = cfg.get("hand_limit", 0)
    p1 = PlayerState(id="P1", hand_limit=hand_limit)
    p2 = PlayerState(id="P2", hand_limit=hand_limit)
    
    # Create game state with empty deck (cards will be added by server)
    st = GameState(config=gcfg, players={"P1": p1, "P2": p2})
    return st


def load_game(path: str | Path, csv_path: str | Path = None) -> Tuple[GameState, dict]:
    """Load game configuration and cards.
    
    Args:
        path: Path to YAML config file (for game rules, not cards)
        csv_path: Path to CSV file containing card data
    """
    # Load game config from YAML (without cards)
    cfg = load_yaml_config(path)
    
    # Default CSV path if not provided
    if csv_path is None:
        # Expect cards.csv to live alongside the YAML config in config/
        csv_path = Path(path).parent / 'cards.csv'
    
    # Load cards from CSV
    cards = []
    if csv_path.exists():
        cards = load_cards_from_csv(csv_path)
    
    # Build game state with config and cards
    st = build_state_from_config(cfg, cards)
    
    # Split cards: some in deck, some on shelf for selection
    # According to rules: shelf is open selection area
    if cards:
        # Put first 10 cards on shelf for selection, rest in deck
        shelf_size = min(10, len(cards))
        st.shelf = cards[:shelf_size]
        st.deck = cards[shelf_size:]
    else:
        st.deck = cards
    
    return st, cfg
