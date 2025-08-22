from __future__ import annotations
import random
from typing import Optional
import typer
from rich import print
from packages.engine.loader import load_game
from packages.engine.engine import Ctx, apply_action, initialize_game
from packages.engine.actions import Attack, Defend
from packages.engine.models import Slot, Card

app = typer.Typer(add_completion=False)


def _place_starters(state, cfg):
    starters = cfg.get("starters", {})
    for pid, cards in starters.items():
        for i, cdata in enumerate(cards):
            if i >= len(state.players[pid].slots):
                break
            state.players[pid].slots[i] = Slot(card=Card(**cdata), face_up=True, muscles=0)


@app.command()
def simulate(config: str = typer.Option("config/default.yaml", "--config", "-c"),
            seed: int = typer.Option(42, "--seed"),
            turns: int = typer.Option(4, "--turns")):
    state, cfg = load_game(config)
    random.seed(seed)
    state.seed = seed
    _place_starters(state, cfg)
    initialize_game(state)

    ctx = Ctx(state=state, log=[])

    print("[bold]Start[/bold]", state.model_dump())

    for t in range(turns):
        ap = state.active_player
        op = state.opponent_id()
        # Примитив: если есть карта на слоте 0 — укрепляем на 1
        if state.players[ap].slots[0].card is not None:
            act = Defend(target_slot=0, hire_count=1)
            res = apply_action(ctx, act)
            print(f"[cyan]{ap} DEFEND[/cyan] ->", res)
        # Затем атакуем слот 0 оппонента базовой атакой с нашего слота 0
        if state.players[ap].slots[0].card is not None and state.players[op].slots[0].card is not None:
            act2 = Attack(target_player=op, target_slot=0, attacker_slot=0, ammo_spend=0)
            res2 = apply_action(ctx, act2)
            print(f"[red]{ap} ATTACK[/red] ->", res2)
            if "winner" in res2:
                print("[green]WINNER:", res2["winner"], res2.get("win_reason"), "[/green]")
                break

    print("[bold]End[/bold]", state.model_dump())


if __name__ == "__main__":
    app()
