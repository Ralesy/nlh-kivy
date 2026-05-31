#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BattleService — фасад боевой логики для UI-слоя.

UI вызывает только методы сервиса и отображает результат.
"""

from typing import List, Optional, Tuple

from core.combat.battlefield import Battlefield
from core.combat.loot import BattleResult


class BattleService:
    """Инкапсуляция боевой логики для Kivy-экранов."""

    def __init__(self, battlefield: Battlefield):
        """Привязать сервис к активному боевому полю."""
        self.battlefield = battlefield

    def get_battle_status(self) -> dict:
        """
        Снимок состояния боя для отрисовки HUD.

        Returns:
            Словарь с HP, врагами, раундом и флагами окончания.
        """
        player = self.battlefield.player
        companions = []
        for companion in player.companions:
            if companion.is_alive:
                companions.append(
                    {
                        "name": companion.name,
                        "health": companion.health,
                        "max_health": companion.max_health,
                    }
                )

        enemies = []
        for enemy in self.battlefield.alive_enemies():
            enemies.append(
                {
                    "name": enemy.name,
                    "health": enemy.health,
                    "max_health": enemy.max_health,
                    "damage": enemy.damage,
                    "defense": enemy.defense,
                }
            )

        weapon = player.weapon
        ability = getattr(weapon, "ability", None) if weapon else None
        ability_available = (
            ability is not None
            and ability.ability_type == "active"
            and not self.battlefield.ability_used_this_battle
        )

        return {
            "round": self.battlefield.round,
            "player_health": player.health,
            "player_max_health": player.max_health,
            "player_damage": player.damage,
            "player_defense": player.defense,
            "companions": companions,
            "enemies": enemies,
            "is_over": self.battlefield.is_over(),
            "player_alive": player.is_alive,
            "ability_available": ability_available,
            "ability_name": ability.name if ability else "",
        }

    def player_attack_enemy(self, enemy_index: int) -> Tuple[str, bool]:
        """
        Атака игрока по врагу с заданным индексом.

        Args:
            enemy_index: индекс в alive_enemies().

        Returns:
            (лог, враг убит).
        """
        return self.battlefield.player_attack(enemy_index)

    def use_ability(self) -> Tuple[bool, List[str]]:
        """Активировать способность оружия."""
        return self.battlefield.use_weapon_ability()

    def run_enemy_phase(self) -> List[str]:
        """
        Полная фаза врагов: спутники, затем враги.

        Returns:
            Список сообщений для боевого лога.
        """
        logs: List[str] = []
        for msg in self.battlefield.companion_turn():
            logs.append(msg)
        for msg in self.battlefield.enemy_turn():
            logs.append(msg)
        return logs

    def attempt_escape(self) -> Tuple[bool, List[str]]:
        """Попытка побега из боя."""
        return self.battlefield.attempt_escape()

    def surrender(self) -> Tuple[str, bool]:
        """
        Сдаться врагам.

        Returns:
            (сообщение, игрок считается поверженным).
        """
        message = f"{self.battlefield.player.name} сдался врагам..."
        self.battlefield.player.health = 0
        return message, True

    def next_round(self) -> None:
        """Увеличить номер раунда."""
        self.battlefield.round += 1

    def is_battle_over(self) -> bool:
        """Проверить, завершён ли бой."""
        return self.battlefield.is_over()

    def get_winner(self) -> Optional[str]:
        """
        Определить победителя.

        Returns:
            'player', 'enemies' или None, если бой ещё идёт.
        """
        if not self.is_battle_over():
            return None
        if not self.battlefield.player.is_alive:
            return "enemies"
        if not self.battlefield.alive_enemies():
            return "player"
        return None

    def generate_loot(self) -> BattleResult:
        """Сформировать награду за победу."""
        return self.battlefield.generate_battle_loot()
