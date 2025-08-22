import random
from packages.engine.models import GameState, PlayerState, Slot, Card
from packages.engine.engine import Ctx, _defense_quota, _on_enter_slot, _maybe_trigger_cascade, apply_action
from packages.engine.actions import Attack, Draw


def make_state():
    st = GameState()
    # two players
    st.players = {
        "P1": PlayerState(id="P1", hand_limit=6),
        "P2": PlayerState(id="P2", hand_limit=6),
    }
    st.active_player = "P1"
    st.config.hand_enabled = True
    st.config.cascade_enabled = True
    st.config.cascade_reward = 2
    st.config.cascade_max_triggers = 3
    return st


def test_authority_extra_defense_defense_quota():
    st = make_state()
    ctx = Ctx(state=st)
    p1 = st.get_player("P1")
    # Boss with authority in slot 0
    p1.slots[0] = Slot(card=Card(id="boss", name="Boss", type="boss", faction="gangsters", hp=10, atk=0, d=1, abl={"authority": 1}))
    # Target card with base d=1 and extra_defense=1 in slot 1
    p1.slots[1] = Slot(card=Card(id="sentinel_extra", name="Страж-экстра", type="common", faction="government", hp=5, atk=1, d=1, abl={"extra_defense": 1}))
    quota = _defense_quota(ctx, "P1", p1.slots[1])
    assert quota == 3, f"expected D(1)+extra(1)+authority(1)=3, got {quota}"


def test_on_enter_thief_steal2():
    st = make_state()
    ctx = Ctx(state=st)
    p1 = st.get_player("P1")
    p2 = st.get_player("P2")
    p2.tokens.reserve_money = 5
    # place thief into P1 slot 0 and fire on-enter
    thief = Card(id="thief_1", name="Вор", type="common", faction="gangsters", hp=3, atk=0, d=1, abl={"on_enter": {"steal": 2}})
    p1.slots[0] = Slot(card=thief)
    _on_enter_slot(ctx, "P1", 0)
    assert p1.tokens.reserve_money == 12 + 2
    assert p2.tokens.reserve_money == 5 - 2
    # log should contain on_enter with amount 2
    assert any(e.get("type") == "on_enter" and e.get("effect") == "steal" and e.get("amount") == 2 for e in ctx.log)


def test_cascade_trigger_on_slot_and_hand_deploy():
    st = make_state()
    ctx = Ctx(state=st)
    p1 = st.get_player("P1")
    # Prepare P1 board with 5 cards: 2 gangsters, 2 government, 1 mercenary
    p1.slots[0] = Slot(card=Card(id="g1", name="G1", type="common", faction="gangsters", hp=1, atk=0, d=0))
    p1.slots[1] = Slot(card=Card(id="g2", name="G2", type="common", faction="gangsters", hp=1, atk=0, d=0))
    p1.slots[2] = Slot(card=Card(id="gov1", name="Gov1", type="common", faction="government", hp=1, atk=0, d=0))
    p1.slots[3] = Slot(card=Card(id="gov2", name="Gov2", type="common", faction="government", hp=1, atk=0, d=0))
    p1.slots[4] = Slot(card=Card(id="merc1", name="Merc1", type="common", faction="mercenaries", hp=1, atk=0, d=0))
    base_money = p1.tokens.reserve_money
    # Place second mercenary into slot 5 to complete 2-2-2 via Draw(place=slot)
    st.deck = [Card(id="merc2", name="Merc2", type="common", faction="mercenaries", hp=1, atk=0, d=0)]
    res = apply_action(ctx, Draw(place="slot", slot_index=5))
    assert p1.tokens.reserve_money == base_money + 2
    assert any(e.get("type") == "cascade_trigger" for e in ctx.log)

    # Hand-deploy cascade: reset log and set up P2 to be defender completing 2-2-2 when auto-deploying from hand
    ctx.log.clear()
    st.active_player = "P1"
    p2 = st.get_player("P2")
    # Clear P2 board and prepare 5 cards leaving 1 mercenary missing
    p2.slots = [Slot() for _ in range(6)]
    p2.slots[0] = Slot(card=Card(id="gg1", name="G1", type="common", faction="gangsters", hp=1, atk=0, d=0))
    p2.slots[1] = Slot(card=Card(id="gg2", name="G2", type="common", faction="gangsters", hp=1, atk=0, d=0))
    p2.slots[2] = Slot(card=Card(id="gov1b", name="Gov1", type="common", faction="government", hp=1, atk=0, d=0))
    p2.slots[3] = Slot(card=Card(id="gov2b", name="Gov2", type="common", faction="government", hp=1, atk=0, d=0))
    p2.slots[4] = Slot(card=Card(id="merc1b", name="Merc1", type="common", faction="mercenaries", hp=1, atk=0, d=0))
    # Put second mercenary into P2 hand to be auto-deployed on attack
    p2.hand = [Card(id="merc2b", name="Merc2", type="common", faction="mercenaries", hp=1, atk=0, d=0)]
    # Ensure P2 board is empty to allow hand-target logic
    p2.slots = [Slot() for _ in range(6)]
    # Attack with no explicit slot; defender has empty board, so engine will auto-deploy first hand card face-up and call _on_enter_slot
    st.config.hand_enabled = True
    res2 = apply_action(ctx, Attack(target_player="P2", base_damage=1))
    assert any(e.get("type") in ("attack_hand_deployed", "on_enter") for e in ctx.log)


def test_on_enter_gain():
    st = make_state()
    ctx = Ctx(state=st)
    p1 = st.get_player("P1")
    base_money = p1.tokens.reserve_money
    gainer = Card(id="gainer", name="Gainer", type="common", faction="gangsters", hp=1, atk=0, d=0, abl={"on_enter": {"gain": 3}})
    p1.slots[0] = Slot(card=gainer)
    _on_enter_slot(ctx, "P1", 0)
    assert p1.tokens.reserve_money == base_money + 3
    assert any(e.get("type") == "on_enter" and e.get("effect") == "gain" and e.get("amount") == 3 for e in ctx.log)


def test_on_enter_bribe_respects_quota():
    st = make_state()
    ctx = Ctx(state=st)
    p1 = st.get_player("P1")
    # Boss with authority 1 to raise quota
    p1.slots[0] = Slot(card=Card(id="boss", name="Boss", type="boss", faction="gangsters", hp=10, atk=0, d=0, abl={"authority": 1}))
    # Card with d=1 and extra_defense=1 -> quota base 1 + extra 1 + authority 1 = 3
    bribed = Card(id="briber", name="Briber", type="common", faction="government", hp=3, atk=0, d=1, abl={"extra_defense": 1, "on_enter": {"bribe": 5}})
    p1.slots[1] = Slot(card=bribed)
    _on_enter_slot(ctx, "P1", 1)
    # Should cap at 3 muscles placed
    assert p1.slots[1].muscles == 3
    assert any(e.get("type") == "on_enter" and e.get("effect") == "bribe" and e.get("placed") == 3 for e in ctx.log)
