from __future__ import annotations
from pathlib import Path
from typing import Tuple, List, Dict, Any
import yaml
import csv
from .models import GameState, GameConfig, Card, PlayerState, Slot


def load_yaml_config(path: str | Path) -> dict:
    """Load only game configuration from YAML, excluding cards."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Remove cards from config as they'll be loaded from CSV
    if 'cards' in cfg:
        del cfg['cards']
    return cfg


def load_cards_from_csv(csv_path: str | Path) -> List[Card]:
    """Load card data exclusively from CSV file."""
    cards = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Determine if the card should be in the deck
            # Support both English 'InDeck' and Russian 'В_колоде' columns and ✓/✗ markers
            indeck_raw = (row.get('InDeck') or row.get('В_колоде') or row.get('In Deck') or '').strip()
            indeck_l = indeck_raw.lower()
            if indeck_raw in {'✓', '✔', '+'} or indeck_l in {'yes', 'true', '1', 'y', 'да'}:
                in_deck = True
            elif indeck_raw in {'✗', 'x', '-'} or indeck_l in {'no', 'false', '0', 'n', 'нет'}:
                in_deck = False
            else:
                # Default to including the card if unclear
                in_deck = True
            if not in_deck:
                continue
                
            # Map CSV columns to card attributes
            card_data = {
                'id': row.get('ID') or row.get('Id') or f"card_{len(cards)}",
                'name': row.get('Name') or row.get('Название') or f"Card {len(cards)}",
                'type': (row.get('Type') or row.get('Тип') or 'common').lower(),
                'faction': (row.get('Faction') or row.get('Фракция') or 'neutral').lower(),
                'caste': (row.get('Caste') or row.get('Каста') or '').strip() or None,
                'hp': int(row.get('HP', 1)) if row.get('HP') else 1,
                'atk': int(row.get('ATK', 0)) if row.get('ATK') else 0,
                'd': int(row.get('Defend', 0)) if row.get('Defend') else 0,
                'notes': (row.get('Description') or row.get('Описание') or '').strip()
            }
            
            # Parse ABL if present
            abl_text = (row.get('ABL') or '').strip()
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
