"""
Рефакторинг engine.py для улучшения тестируемости
Разбиваем крупные функции на более мелкие, тестируемые компоненты
"""

from __future__ import annotations
from typing import List, Dict
import random
from pydantic import BaseModel
from .models import GameState, PlayerState, Slot, TurnPhase
from .actions import Action, Attack, Defend, Influence, DiscardCard, Draw


class Ctx(BaseModel):
    state: GameState
    log: List[Dict] = []


class ActionResult(BaseModel):
    """Результат выполнения действия"""
    phase: str
    error: str = ""
    winner: str = ""
    win_reason: str = ""


class AttackHandler:
    """Обработчик атак - отдельный класс для лучшей тестируемости"""
    
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.state = ctx.state
        self.ap = self.state.get_player(self.state.active_player)
        self.op = self.state.get_player(self.state.opponent_id())
    
    def handle_attack(self, action: Attack) -> ActionResult:
        """Обработка атаки"""
        # 1. Рассчитать и потратить боеприпасы
        ammo = self._calculate_ammo(action.ammo_spend)
        self._spend_ammo(ammo)
        
        # 2. Рассчитать урон
        damage = self._calculate_damage(action, ammo)
        
        # 3. Применить атаку
        self._apply_attack(action, damage)
        
        self.state.phase = TurnPhase.resolution
        return ActionResult(phase=self.state.phase.value)
    
    def _calculate_ammo(self, requested_ammo: int) -> int:
        """Рассчитать количество боеприпасов для атаки"""
        max_ammo = min(self.state.config.ammo_max_bonus, requested_ammo)
        available_ammo = self.ap.tokens.reserve_money
        return max(0, min(max_ammo, available_ammo))
    
    def _spend_ammo(self, ammo: int) -> None:
        """Потратить боеприпасы"""
        self.ap.tokens.reserve_money -= ammo
        self.ap.tokens.otboy += ammo
    
    def _calculate_damage(self, action: Attack, ammo: int) -> int:
        """Рассчитать общий урон"""
        damage = action.base_damage if action.base_damage > 0 else 0
        
        # Добавить урон от атакующей карты
        if action.attacker_slot is not None:
            attacker_slot = self.ap.slots[action.attacker_slot]
            if attacker_slot.card:
                damage += attacker_slot.card.atk
        
        damage += ammo
        return damage
    
    def _apply_attack(self, action: Attack, damage: int) -> None:
        """Применить атаку к цели"""
        if action.target_slot is not None:
            target_slot = self.op.slots[action.target_slot]
            _apply_damage(target_slot, damage, self.ctx, owner_pid=self.op.id)
        else:
            self._handle_boardless_attack(damage)
    
    def _handle_boardless_attack(self, damage: int) -> None:
        """Обработка атаки когда у противника нет карт на поле"""
        opponent_has_board = any(s.card is not None for s in self.op.slots)
        
        if opponent_has_board:
            self.ctx.log.append({"type": "attack_skipped", "reason": "opponent_has_board"})
            return
        
        # Атака по руке если разрешено
        if self.state.config.hand_enabled and self.op.hand:
            self._attack_hand_card(damage)
        else:
            self.ctx.log.append({"type": "attack_skipped", "reason": "no_target"})
    
    def _attack_hand_card(self, damage: int) -> None:
        """Атака карты из руки"""
        hand_card = self.op.hand[0]
        
        # Попытка экстренного размещения
        free_slot_idx = self._find_free_slot()
        
        if free_slot_idx is not None:
            self._emergency_deploy_and_defend(hand_card, free_slot_idx, damage)
        else:
            self._direct_hand_damage(hand_card, damage)
    
    def _find_free_slot(self) -> int | None:
        """Найти свободный слот"""
        for i, slot in enumerate(self.op.slots):
            if slot.card is None:
                return i
        return None
    
    def _emergency_deploy_and_defend(self, hand_card, slot_idx: int, damage: int) -> None:
        """Экстренное размещение карты и защита"""
        target_slot = self.op.slots[slot_idx]
        target_slot.card = hand_card
        target_slot.face_up = True
        
        # Применить эффекты входа
        _on_enter_slot(self.ctx, self.op.id, slot_idx)
        
        # Удалить из руки
        self.op.hand.pop(0)
        
        # Экстренная защита
        quota = _defense_quota(self.ctx, self.op.id, target_slot)
        self._emergency_defense(target_slot, quota, damage)
        
        # Применить урон
        _apply_damage(target_slot, damage, self.ctx, owner_pid=self.op.id)
        self.ctx.log.append({"type": "attack_hand_deployed", "slot": slot_idx, "dmg": damage})
    
    def _emergency_defense(self, target_slot: Slot, quota: int, damage: int) -> None:
        """Экстренная защита при атаке по руке"""
        already_defended = target_slot.muscles
        remaining_quota = max(0, quota - already_defended)
        
        # Нанять защиту за деньги
        if remaining_quota > 0 and self.op.tokens.reserve_money > 0:
            can_hire = min(self.op.tokens.reserve_money, remaining_quota)
            if can_hire > 0:
                self.op.tokens.reserve_money -= can_hire
                target_slot.muscles += can_hire
                remaining_quota -= can_hire
        
        # Переназначить защиту с других слотов
        self._reassign_defense(target_slot, remaining_quota, damage)
    
    def _reassign_defense(self, target_slot: Slot, remaining_quota: int, damage: int) -> None:
        """Переназначить защиту с других слотов"""
        need_block = max(0, damage - target_slot.muscles)
        target_slot_idx = self.op.slots.index(target_slot)
        
        for i, slot in enumerate(self.op.slots):
            if i == target_slot_idx or slot.muscles <= 0:
                continue
            if need_block <= 0 or remaining_quota <= 0:
                break
                
            move = min(slot.muscles, need_block, remaining_quota)
            if move > 0:
                slot.muscles -= move
                target_slot.muscles += move
                need_block -= move
                remaining_quota -= move
                self.ctx.log.append({
                    "type": "reassign_muscles", 
                    "from": i, 
                    "to": target_slot_idx, 
                    "count": move
                })
    
    def _direct_hand_damage(self, hand_card, damage: int) -> None:
        """Прямой урон карте в руке"""
        hand_card.hp -= max(0, damage)
        
        if hand_card.hp <= 0:
            self.ctx.state.discard_out_of_game.append(hand_card)
            self.op.hand.pop(0)
            self.ctx.log.append({"type": "attack_hand", "dmg": damage, "killed": True})
        else:
            self.ctx.log.append({"type": "attack_hand", "dmg": damage, "killed": False})


class DefendHandler:
    """Обработчик защиты"""
    
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.state = ctx.state
        self.ap = self.state.get_player(self.state.active_player)
    
    def handle_defend(self, action: Defend) -> ActionResult:
        """Обработка защиты"""
        slot = self.ap.slots[action.target_slot]
        
        if not slot.card:
            return ActionResult(phase="", error="No card in slot")
        
        # Рассчитать квоту защиты
        quota = _defense_quota(self.ctx, self.ap.id, slot)
        already_defended = slot.muscles
        remaining_quota = max(0, quota - already_defended)
        
        # Нанять защитников
        hire_count = max(0, min(
            action.hire_count, 
            remaining_quota, 
            self.ap.tokens.reserve_money
        ))
        
        # Применить изменения
        self.ap.tokens.reserve_money -= hire_count
        slot.muscles += hire_count
        
        self.ctx.log.append({"type": "defend", "hired": hire_count})
        self.state.phase = TurnPhase.resolution
        
        return ActionResult(phase=self.state.phase.value)


class InfluenceHandler:
    """Обработчик влияния (микро-подкуп)"""
    
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.state = ctx.state
        self.ap = self.state.get_player(self.state.active_player)
    
    def handle_influence(self, action: Influence) -> ActionResult:
        """Обработка влияния"""
        if not self._can_micro_bribe(action):
            return ActionResult(phase="", error="micro_bribe_already_used")
        
        if self.ap.tokens.reserve_money >= 2:
            self._apply_micro_bribe(action)
        
        self.state.phase = TurnPhase.resolution
        return ActionResult(phase=self.state.phase.value)
    
    def _can_micro_bribe(self, action: Influence) -> bool:
        """Проверить можно ли использовать микро-подкуп"""
        if not (action.micro_bribe_target_player and action.micro_bribe_target_slot is not None):
            return True
        
        if self.state.config.micro_bribe_once_per_turn:
            return not self.state.flags.get("micro_bribe_used", False)
        
        return True
    
    def _apply_micro_bribe(self, action: Influence) -> None:
        """Применить микро-подкуп"""
        self.ap.tokens.reserve_money -= 2
        self.ap.tokens.otboy += 2
        
        target_player = self.state.get_player(action.micro_bribe_target_player)
        target_slot = target_player.slots[action.micro_bribe_target_slot]
        
        if target_slot.muscles > 0:
            target_slot.muscles -= 1
            target_player.tokens.otboy += 1
        
        self.state.flags["micro_bribe_used"] = True
        self.ctx.log.append({
            "type": "micro_bribe", 
            "slot": action.micro_bribe_target_slot
        })


# Импорт существующих функций (заглушки для демонстрации)
def _card_trait(card, key: str, default: int = 0) -> int:
    """Заглушка - используется существующая функция"""
    pass

def _maybe_trigger_cascade(ctx: Ctx, pid: str) -> None:
    """Заглушка - используется существующая функция"""
    pass

def _authority_bonus(p: PlayerState) -> int:
    """Заглушка - используется существующая функция"""
    pass

def _defense_quota(ctx: Ctx, pid: str, slot: Slot) -> int:
    """Заглушка - используется существующая функция"""
    pass

def _on_enter_slot(ctx: Ctx, owner_pid: str, slot_index: int) -> None:
    """Заглушка - используется существующая функция"""
    pass

def _apply_damage(slot: Slot, damage: int, ctx: Ctx, owner_pid: str):
    """Заглушка - используется существующая функция"""
    pass


# Рефакторинная версия apply_action
def apply_action_refactored(ctx: Ctx, action: Action) -> ActionResult:
    """
    Рефакторинная версия apply_action с улучшенной тестируемостью
    """
    # Фабрика обработчиков
    handlers = {
        Attack: AttackHandler,
        Defend: DefendHandler,
        Influence: InfluenceHandler,
        # DiscardCard и Draw можно также вынести в отдельные обработчики
    }
    
    handler_class = handlers.get(type(action))
    if handler_class:
        handler = handler_class(ctx)
        if isinstance(action, Attack):
            return handler.handle_attack(action)
        elif isinstance(action, Defend):
            return handler.handle_defend(action)
        elif isinstance(action, Influence):
            return handler.handle_influence(action)
    
    # Пока оставляем обработку других действий в исходном виде
    return ActionResult(phase="unknown")
