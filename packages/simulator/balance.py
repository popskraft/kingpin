from __future__ import annotations
import csv
import statistics as stats
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from packages.engine.loader import load_game
from packages.engine.engine import Ctx, apply_action, initialize_game
from packages.engine.actions import Attack, Defend
from packages.engine.models import Slot, Card
import random
import argparse


def _place_starters(state, cfg):
    starters = cfg.get("starters", {})
    for pid, cards in starters.items():
        for i, cdata in enumerate(cards):
            if i >= len(state.players[pid].slots):
                break
            state.players[pid].slots[i] = Slot(card=Card(**cdata), face_up=True, muscles=0)


def run_one(seed: int, turns: int, config: str) -> Dict:
    state, cfg = load_game(config)
    random.seed(seed)
    state.seed = seed
    _place_starters(state, cfg)
    # Randomize starting player per game to avoid systemic first-move bias
    try:
        state.active_player = random.choice([pid for pid in state.players.keys()])
    except Exception:
        state.active_player = "P1"
    initialize_game(state)

    ctx = Ctx(state=state, log=[])

    empty_turns = 0
    winner: Optional[str] = None
    start_player = state.active_player

    for t in range(turns):
        ap = state.active_player
        op = state.opponent_id()
        did_something = False

        # Collect available slots
        ap_slots = state.players[ap].slots
        op_slots = state.players[op].slots
        my_indices = [i for i, s in enumerate(ap_slots) if s.card is not None]
        op_indices = [i for i, s in enumerate(op_slots) if s.card is not None]

        # Choose attacker: prefer highest ATK among own slots, else random
        attacker_slot = None
        if my_indices:
            attacker_slot = max(my_indices, key=lambda i: (ap_slots[i].card.atk if ap_slots[i].card else -1, random.random()))
        # Choose target: prefer weakest defended (fewest muscles; tie-breaker lowest HP), else random
        target_slot = None
        if op_indices:
            def target_key(i: int):
                s = op_slots[i]
                hp = s.card.hp if s.card else 0
                return (s.muscles, hp, random.random())
            target_slot = min(op_indices, key=target_key)

        # Decide action order randomly: 60% defend then attack, 40% attack then defend
        # Aggression: starting player in first 3 turns prefers attack first
        if ap == start_player and t < 3:
            do_defend_first = random.random() < 0.4
        else:
            do_defend_first = random.random() < 0.6

        def try_defend():
            nonlocal did_something
            if attacker_slot is not None:
                # Simple defend heuristic: if under-defended, increase chance to hire
                s = ap_slots[attacker_slot]
                goal = max(1, min(2, (s.card.d if s.card else 1) + 1))
                need = s.muscles < goal or (s.card and s.card.hp <= 2)
                prob = 0.85 if need else 0.4
                if random.random() < prob:
                    apply_action(ctx, Defend(target_slot=attacker_slot, hire_count=1))
                    did_something = True

        def try_attack():
            nonlocal did_something, winner
            if attacker_slot is not None and target_slot is not None:
                # Starting player early turns is more likely to spend 1 ammo
                base_prob_ammo = 0.25
                if ap == start_player and t < 3:
                    base_prob_ammo = 0.5
                ammo = 1 if random.random() < base_prob_ammo else 0
                res2 = apply_action(ctx, Attack(target_player=op, target_slot=target_slot, attacker_slot=attacker_slot, ammo_spend=ammo))
                did_something = True
                if isinstance(res2, dict) and "winner" in res2:
                    winner = res2.get("winner")
                    return True
            return False

        if do_defend_first:
            try_defend()
            if try_attack():
                break
        else:
            if try_attack():
                break
            try_defend()

        if not did_something:
            empty_turns += 1

        # If engine exposes end-of-turn switch implicitly inside actions, continue loop
        # Otherwise, rely on engine to advance turns via apply_action side-effects
        # If no progress is possible, we still cap by `turns`

    return {
        "seed": seed,
        "winner": winner,
        "turns_played": t + 1,  # 1-indexed count of turns run
        "empty_turns": empty_turns,
    }


def aggregate(results: List[Dict]) -> Dict:
    total = len(results)
    p1_wins = sum(1 for r in results if r.get("winner") == "P1")
    p2_wins = sum(1 for r in results if r.get("winner") == "P2")
    draws = total - p1_wins - p2_wins

    lengths = [r["turns_played"] for r in results]
    empty = [r["empty_turns"] for r in results]

    def pct(x: int) -> float:
        return 100.0 * x / total if total else 0.0

    summary = {
        "games": total,
        "p1_winrate": (p1_wins / total) if total else 0.0,
        "p1_wins": p1_wins,
        "p2_wins": p2_wins,
        "draws": draws,
        "mean_turns": stats.mean(lengths) if lengths else 0.0,
        "median_turns": stats.median(lengths) if lengths else 0.0,
        "p25_turns": stats.quantiles(lengths, n=4)[0] if len(lengths) >= 4 else 0.0,
        "p75_turns": stats.quantiles(lengths, n=4)[2] if len(lengths) >= 4 else 0.0,
        "mean_empty_turns": stats.mean(empty) if empty else 0.0,
        "empty_turn_rate": (sum(empty) / sum(lengths)) if lengths and sum(lengths) else 0.0,
    }
    return summary


def print_summary(summary: Dict):
    print("Balance summary")
    print(f"Games: {summary['games']}")
    print(f"P1 winrate: {summary['p1_winrate']*100:.1f}% (P1={summary['p1_wins']}, P2={summary['p2_wins']}, draws={summary['draws']})")
    print(
        "Turns: mean={:.2f}, median={}, IQR=[{}, {}]".format(
            summary["mean_turns"], summary["median_turns"], summary["p25_turns"], summary["p75_turns"]
        )
    )
    print(
        "Empty turns: mean={:.2f} per game, rate={:.1f}%".format(
            summary["mean_empty_turns"], summary["empty_turn_rate"] * 100
        )
    )


def write_csv(results: List[Dict], path: str):
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)


def main():
    parser = argparse.ArgumentParser(description="Run many simulated games to collect balance metrics")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--turns", type=int, default=15)
    parser.add_argument("--csv", default="")
    args = parser.parse_args()

    results: List[Dict] = []
    for seed in range(1, args.seeds + 1):
        r = run_one(seed=seed, turns=args.turns, config=args.config)
        results.append(r)

    summary = aggregate(results)
    print_summary(summary)

    if args.csv:
        write_csv(results, args.csv)
        print(f"Saved per-game metrics to {args.csv}")


if __name__ == "__main__":
    main()
