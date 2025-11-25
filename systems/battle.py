#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Battle system: боевая система, враги и события.
Полностью переработана для новой системы врагов и дропа.
"""

import random
from typing import List, Tuple, Optional
from core.creatures import Creature, Player
from core.utils import clamp
from data.items import ItemDatabase
from data.enemies import EnemyDatabase


class LootDrop:
    """Предмет из дропа."""

    def __init__(self, item_id: str, quantity: int = 1):
        self.item_id = item_id
        self.quantity = quantity
        self.item = ItemDatabase.get(item_id)

    def display(self) -> str:
        """Отображение предмета."""
        if self.item is None:
            return f"{self.item_id} x{self.quantity}"
        return f"{self.item.display_name()} x{self.quantity}"


class BattleResult:
    """Результат боя."""

    def __init__(
        self,
        victory: bool,
        loot: List[LootDrop],
        gold_earned: int,
        xp_earned: int
    ):
        self.victory = victory
        self.loot = loot
        self.gold_earned = gold_earned
        self.xp_earned = xp_earned


class EnemyGenerator:
    """Генератор врагов на основе новой системы."""

    @staticmethod
    def generate_for_location(
        location_id: str,
        player_level: int,
        count: int = 1
    ) -> List[Creature]:
        """Генерировать врагов для конкретной локации."""
        enemies = []
        location_enemies = EnemyDatabase.get_by_location(location_id)

        if not location_enemies:
            return enemies

        for _ in range(count):
            enemy_template = random.choice(location_enemies)
            level = clamp(
                player_level + random.randint(-1, 2),
                1,
                player_level + 3
            )

            # Создаём врага из шаблона
            enemy = Creature(
                enemy_template.name,
                enemy_template.base_health,
                enemy_template.base_damage,
                enemy_template.base_coins,
                level=level
            )

            # Сохраняем шаблон для дропа
            enemy._template = enemy_template

            enemies.append(enemy)

        return enemies

    @staticmethod
    def generate_boss(boss_id: str) -> Optional[Creature]:
        """Генерировать босса."""
        enemy_template = EnemyDatabase.get(boss_id)
        if enemy_template is None:
            return None

        enemy = Creature(
            enemy_template.name,
            enemy_template.base_health,
            enemy_template.base_damage,
            enemy_template.base_coins,
            level=10
        )
        enemy._template = enemy_template
        return enemy


class EventSystem:
    """Система событий в локациях."""

    FOREST_EVENTS = [
        ("found_potion", 0.15),
        ("ambush", 0.12),
        ("nothing", 0.73)
    ]

    SWAMP_EVENTS = [
        ("found_item", 0.10),
        ("poison_gas", 0.10),
        ("nothing", 0.80)
    ]

    MINES_EVENTS = [
        ("found_ore", 0.12),
        ("cave_in", 0.10),
        ("nothing", 0.78)
    ]

    @staticmethod
    def roll_event(location_id: str,
                   player: Player) -> Optional[str]:
        """Рассчитать событие в локации."""
        if location_id == "forest":
            events = EventSystem.FOREST_EVENTS
        elif location_id == "swamp":
            events = EventSystem.SWAMP_EVENTS
        elif location_id == "mines":
            events = EventSystem.MINES_EVENTS
        else:
            return None

        # Взвешенный выбор события
        choice = random.choices(
            [e[0] for e in events],
            weights=[e[1] for e in events],
            k=1
        )[0]

        if choice == "found_potion":
            potion = ItemDatabase.get("p_small")
            if player.inventory.has_space_for(1):
                player.inventory.add(potion, 1)
                return f"Вы нашли зелье! +{potion.display_name()}"
            return "Вы нашли зелье, но инвентарь полон."

        if choice == "poison_gas":
            damage = random.randint(10, 30)
            player.take_damage(damage)
            return f"Ядовитый газ! Вы получили {damage} урона."

        if choice == "cave_in":
            damage = random.randint(15, 40)
            player.take_damage(damage)
            return f"Обрушение! Вы получили {damage} урона."

        return None


class Battlefield:
    """Боевое поле."""

    def __init__(self, player: Player, enemies: List[Creature]):
        self.player = player
        self.enemies = enemies
        self.round = 0

    def alive_enemies(self) -> List[Creature]:
        """Живые враги."""
        return [e for e in self.enemies if e.is_alive]

    def is_over(self) -> bool:
        """Закончилась ли битва."""
        return not self.player.is_alive or not self.alive_enemies()

    def player_attack(self) -> Tuple[str, bool]:
        """Атака игрока."""
        enemies = self.alive_enemies()
        if not enemies:
            return "Нет врагов!", False

        target = random.choice(enemies)
        damage = self.player.damage + random.randint(-3, 5)
        damage = max(1, damage)
        dealt = target.take_damage(damage)

        log = f"Вы наносите {dealt} урона по {target.name}."
        killed = not target.is_alive

        if killed:
            log += f" 💥 {target.name} повержен!"
            self.player.update_quest_progress(target.name)

        return log, killed

    def enemy_turn(self) -> List[str]:
        """Ход всех врагов."""
        logs = []
        for enemy in self.alive_enemies():
            if self.player.is_alive:
                damage = enemy.damage + random.randint(-2, 3)
                damage = max(1, damage)
                dealt = self.player.take_damage(damage)
                logs.append(f"{enemy.name} наносит {dealt} урона!")

                if not self.player.is_alive:
                    logs.append("💀 Вы были повержены!")

        return logs

    def attempt_escape(self) -> Tuple[bool, List[str]]:
        """Попытка бегства."""
        logs = []
        if random.random() < 0.3:
            logs.append("Вы успешно сбежали!")
            return True, logs
        else:
            logs.append("Враги преследуют вас!")
            # Враги наносят урон убегающему персонажу
            for enemy in self.alive_enemies():
                damage = enemy.damage // 2
                dealt = self.player.take_damage(damage)
                logs.append(f"{enemy.name} наносит {dealt} урона!")
            return False, logs

    def generate_battle_loot(self) -> BattleResult:
        """Генерировать лут с побеждённых врагов."""
        loot_items = []
        total_gold = 0
        total_xp = 0

        for enemy in self.enemies:
            if not enemy.is_alive:
                continue

            # Золото и XP
            total_gold += enemy.coins
            template = getattr(enemy, '_template', None)
            if template:
                total_xp += template.xp_reward
            else:
                total_xp += enemy.level * 30

            # Дроп предметов
            if template:
                drops = template.generate_loot()
                for item_id, qty in drops:
                    loot_items.append(LootDrop(item_id, qty))

        return BattleResult(
            victory=True,
            loot=loot_items,
            gold_earned=total_gold,
            xp_earned=total_xp
        )
