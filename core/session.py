#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GameSession — единый оркестратор игровой сессии.

UI-слой обращается к сессии, а не к разрозненным системам напрямую.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from core.combat.battle_service import BattleService
from core.combat.battlefield import Battlefield
from core.combat.loot import BattleResult
from core.creatures import Player, TestPlayer
from data.enemies import EnemyDatabase
from data.items import ItemDatabase
from data.locations import LocationManager
from systems.npcs import GeneratedQuest, NPCManager
from systems.quests import Tavern
from systems.danger_manager import DangerManager
from systems.save_system import load_session_into, save_session
from systems.shop_casino import Shop


@dataclass
class DeathPenaltyResult:
    """Результат поражения игрока для отображения в UI."""

    gold_lost: int = 0
    items_lost: List[str] = field(default_factory=list)
    health_restored: int = 0
    message: str = ""


class GameSession:
    """
    Игровая сессия: игрок, мир, экономика, квесты и боевые операции.

    Kivy-экраны получают ссылку на сессию через ``app.game`` / ``app.session``.
    """

    DEFAULT_SHOP_STOCK = {
        "w_iron_sword": 5,
        "w_steel_sword": 2,
        "a_leather_armor": 5,
        "a_iron_plate": 2,
        "a_steel_plate": 1,
        "p_small": 15,
        "p_med": 8,
        "p_large": 3,
    }

    def __init__(self):
        """Инициализировать пустую сессию с базовыми подсистемами."""
        self.player: Optional[Player] = None
        self.tavern = Tavern()
        self.location_manager = LocationManager()
        self.npc_manager = NPCManager()

        ItemDatabase.initialize()
        EnemyDatabase.initialize()

        self.shop = Shop(self.DEFAULT_SHOP_STOCK.copy())
        self.danger_manager = DangerManager()
        self.day = 1
        self.history: List[str] = []
        self.wins_in_row = 0

        # ── Party system ──
        self.party_members: List[Player] = []
        # -1 = активен главный игрок (self.player)
        # 0, 1, 2... = активен party_members[index]
        self.active_party_member_index: int = -1
        # ID нанятых NPC-слотов в городе (чтобы не спавнить повторно)
        self.hired_npc_ids: set = set()

    @property
    def has_player(self) -> bool:
        """True, если в сессии есть активный игрок."""
        return self.player is not None

    @property
    def active_player(self) -> Optional[Player]:
        """Вернуть активного персонажа (главный или член отряда)."""
        if self.active_party_member_index >= 0 and self.active_party_member_index < len(self.party_members):
            return self.party_members[self.active_party_member_index]
        return self.player

    def switch_to_next_party_member(self) -> Optional[Player]:
        """Переключиться на следующего члена отряда или главного игрока.
        Возвращает нового активного персонажа или None."""
        total = len(self.party_members) + 1  # +1 за главного игрока
        if total <= 1:
            return self.player
        self.active_party_member_index = (self.active_party_member_index + 1) % total - 1
        # -1 -> 0 (главный -> первый член отряда), 0 -> -1 и т.д.
        if self.active_party_member_index < -1:
            self.active_party_member_index = -1
        if (self.active_party_member_index >= 0 and
                self.active_party_member_index >= len(self.party_members)):
            self.active_party_member_index = -1
        return self.active_player

    def switch_to_player(self, index: int = -1) -> Optional[Player]:
        """Переключиться на персонажа по индексу.
        -1 = главный игрок, 0+ = party_members[index]."""
        if index == -1:
            self.active_party_member_index = -1
            return self.player
        if 0 <= index < len(self.party_members):
            self.active_party_member_index = index
            return self.party_members[index]
        return self.active_player

    def start_new_game(self, name: str, background: str = "squire") -> Player:
        """
        Создать нового игрока и привязать к сессии.

        Args:
            name: имя персонажа.
            background: ключ фона (noble / squire / hunter).

        Returns:
            Созданный Player.
        """
        self.player = Player(name, background)
        self.day = 1
        self.history = []
        self.wins_in_row = 0
        self.danger_manager.reset()
        return self.player

    def start_test_game(self, name: str) -> Player:
        """Создать тестового игрока с усиленными характеристиками."""
        self.player = TestPlayer(name)
        self.day = 1
        self.history = []
        self.wins_in_row = 0
        self.danger_manager.reset()
        return self.player

    def load_from_file(self, filename: str) -> bool:
        """
        Загрузить сессию из файла сохранения.

        Returns:
            True при успешной загрузке.
        """
        return load_session_into(self, filename)

    def save_to_file(self, filename: str) -> bool:
        """
        Сохранить сессию в файл.

        Returns:
            True при успешном сохранении.
        """
        if not self.player:
            return False
        return save_session(self, filename)

    def autosave(self) -> bool:
        """Быстрое автосохранение в ``autosave``."""
        return self.save_to_file("autosave")

    def advance_day(self) -> None:
        """Перевести игровой день на следующий."""
        self.day += 1

    def register_battle_encounter(self) -> None:
        """Зафиксировать начало боя: день и счётчик боёв."""
        self.advance_day()
        if self.player:
            self.player.battles_fought += 1

    def create_battle(
        self,
        enemies: List,
        register_encounter: bool = True,
    ) -> Tuple[Battlefield, BattleService]:
        """
        Создать бой с врагами.

        Args:
            enemies: список Creature.
            register_encounter: учитывать день/статистику боя.

        Returns:
            (Battlefield, BattleService).
        """
        if not self.player:
            raise RuntimeError("Нельзя начать бой без игрока.")
        if register_encounter:
            self.register_battle_encounter()
        battlefield = Battlefield(self.player, enemies)
        return battlefield, BattleService(battlefield)

    def refresh_shop(self) -> None:
        """Обновить ассортимент магазина по разблокированным локациям."""
        self.shop.refresh(self.location_manager)

    def mark_boss_defeated(self, boss_id: int) -> None:
        """Отметить босса как поверженного и проверить разблокировки."""
        if self.player:
            self.player.defeated_bosses.add(boss_id)
        self.location_manager.mark_boss_defeated(boss_id)

    def check_location_unlocks(self) -> List[str]:
        """
        Проверить новые локации после победы.

        Returns:
            ID разблокированных локаций.
        """
        return self.location_manager.check_and_unlock_locations()

    def add_history(self, message: str) -> None:
        """Добавить запись в журнал сессии."""
        self.history.append(message)

    def apply_death_penalty(self) -> DeathPenaltyResult:
        """
        Применить штрафы за поражение (золото, предметы, частичное HP).

        Returns:
            Структура с деталями для UI.
        """
        if not self.player:
            return DeathPenaltyResult(message="Нет активного игрока.")

        player = self.player
        gold_lost = player.coins // 10
        if gold_lost > 0:
            player.spend_coins(gold_lost)

        items_lost: List[str] = []
        non_quest_items = [
            (item, qty)
            for item, qty in player.inventory.list_items()
            if not item.is_quest_item()
        ]

        if non_quest_items:
            num_lost = random.randint(1, min(2, len(non_quest_items)))
            for _ in range(num_lost):
                if not non_quest_items:
                    break
                item, _qty = random.choice(non_quest_items)
                if player.inventory.remove(item.id, 1):
                    items_lost.append(item.name)
                    non_quest_items = [
                        entry
                        for entry in non_quest_items
                        if entry[0].id != item.id
                    ]

        restored_hp = max(1, int(player.max_health * 0.3))
        player.health = restored_hp

        message = (
            "Вас оглушили и оставили без сознания.\n"
            "Вы очнулись, потеряв часть добычи...\n\n"
            f"Потеряно: {gold_lost} золота.\n"
        )
        if items_lost:
            message += "\n".join(
                f"Потерян предмет: {name}" for name in items_lost
            )
            message += "\n"
        message += "\n[Сердце] Вы восстановили часть здоровья."

        return DeathPenaltyResult(
            gold_lost=gold_lost,
            items_lost=items_lost,
            health_restored=restored_hp,
            message=message,
        )

    def restore_npc_state(self, npc_data: dict) -> None:
        """Восстановить состояние NPC из сохранения."""
        if not npc_data:
            return
        for npc_id, state in npc_data.items():
            npc = self.npc_manager.get_npc(npc_id)
            if not npc:
                continue
            npc.completed_quests_count = state.get(
                "completed_quests_count",
                npc.completed_quests_count,
            )
            quest_data = state.get("current_quest")
            if quest_data:
                npc.current_quest = GeneratedQuest.from_dict(quest_data)
            else:
                npc.current_quest = None

    def complete_quest_and_reduce_danger(
        self, quest_id: str
    ) -> str:
        """Сдать квест и снизить глобальную опасность.

        Args:
            quest_id: ID завершённого квеста.

        Returns:
            Сообщение о снижении опасности.
        """
        reduction = self.danger_manager.on_quest_completed()
        if reduction > 0:
            return (
                f"Опасность снижена на {reduction:.0f}% "
                f"(теперь {self.danger_manager.danger_level:.0f}%)"
            )
        return "Опасность уже на минимуме."

    def to_save_dict(self) -> dict:
        """Сериализовать сессию для сохранения."""
        return {
            "version": "2.0",
            "day": self.day,
            "history": self.history,
            "wins_in_row": self.wins_in_row,
            "player": (
                self.player.to_dict() if self.player else None
            ),
            "party_members": [pm.to_dict() for pm in self.party_members],
            "active_party_member_index": self.active_party_member_index,
            "npcs": self.npc_manager.to_dict(),
            "danger": self.danger_manager.to_dict(),
        }


# Обратная совместимость: старый код импортирует Game
Game = GameSession
