#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Battle system: боевая система, враги и события.
"""

import random
from typing import List, Tuple, Optional
from creatures import Creature, Player
from utils import clamp, rnd_choice_weighted, rarity_weighted_choice
from items import ItemDatabase


class EnemyGenerator:
    """Генератор врагов."""

    POOLS = {
        "forest": [
            {"id": "goblin", "name": "Лесной гоблин",
             "hp": 30, "dmg": 8, "coins": 12},
            {"id": "wolf", "name": "Волк",
             "hp": 25, "dmg": 10, "coins": 8},
            {"id": "bandit", "name": "Бандит",
             "hp": 34, "dmg": 11, "coins": 14},
            {"id": "bear", "name": "Бурый медведь",
             "hp": 55, "dmg": 16, "coins": 30},
            {"id": "spider", "name": "Паук-гигант",
             "hp": 22, "dmg": 12, "coins": 10},
            {"id": "orc", "name": "Орк", "hp": 45,
             "dmg": 13, "coins": 20}
        ],
        "cave": [
            {"id": "bat", "name": "Летучая мышь",
             "hp": 15, "dmg": 5, "coins": 2},
            {"id": "troll", "name": "Тролль",
             "hp": 75, "dmg": 14, "coins": 25},
            {"id": "skeleton", "name": "Скелет",
             "hp": 28, "dmg": 9, "coins": 6},
            {"id": "golem", "name": "Голем",
             "hp": 90, "dmg": 12, "coins": 40}
        ],
        "ruins": [
            {"id": "ghost", "name": "Привидение",
             "hp": 35, "dmg": 14, "coins": 18},
            {"id": "knight", "name": "Призрачный рыцарь",
             "hp": 70, "dmg": 18, "coins": 50},
            {"id": "mage", "name": "Минотавр",
             "hp": 60, "dmg": 16, "coins": 35}
        ]
    }

    @staticmethod
    def generate(
        location: str,
        player_level: int,
        num: int = 1
    ) -> List[Creature]:
        """Генерирование врагов для локации."""
        pool = EnemyGenerator.POOLS.get(
            location, EnemyGenerator.POOLS["forest"]
        )
        enemies = []
        for _ in range(num):
            b = random.choice(pool)
            lvl = clamp(
                player_level + random.randint(-1, 1),
                1,
                player_level + 2
            )
            e = Creature(
                b["name"], b["hp"], b["dmg"], b["coins"], level=lvl
            )
            enemies.append(e)
        return enemies


class EventSystem:
    """Система событий в локациях."""

    FOREST_EVENTS = [
        ("found_chest", 0.12),
        ("ambush", 0.10),
        ("healing_spring", 0.08),
        ("cursed_area", 0.05),
        ("nothing", 0.65)
    ]

    CAVE_EVENTS = [
        ("found_treasure", 0.10),
        ("trap", 0.15),
        ("scholar", 0.08),
        ("nothing", 0.67)
    ]

    @staticmethod
    def roll_forest(player: Player) -> Optional[str]:
        """Событие в лесу."""
        choice = rnd_choice_weighted(EventSystem.FOREST_EVENTS)

        if choice == "found_chest":
            rar = rarity_weighted_choice()
            candidates = [
                it for it in ItemDatabase.ITEMS.values()
                if it.rarity == rar
            ]
            if not candidates:
                item = random.choice(list(ItemDatabase.ITEMS.values()))
            else:
                item = random.choice(candidates)

            if player.inventory.has_space_for(1):
                player.inventory.add(item, 1)
                return (f"Вы нашли сундук и получили "
                        f"{item.display_name()}!")
            else:
                return "Вы нашли сундук, но инвентарь полон."

        if choice == "ambush":
            enemies = EnemyGenerator.generate(
                "forest", player.level, num=1
            )
            return f"Засада! Появился {enemies[0].name}."

        if choice == "healing_spring":
            healed = player.heal(int(player.max_health * 0.2))
            return (f"Вы нашли целебный источник и восстановили "
                    f"{healed} HP.")

        if choice == "cursed_area":
            damage = int(player.max_health * 0.15)
            player.take_damage(damage)
            return f"Проклятая область! Вы получили {damage} урона!"

        return None

    @staticmethod
    def roll_cave(player: Player) -> Optional[str]:
        """Событие в пещере."""
        choice = rnd_choice_weighted(EventSystem.CAVE_EVENTS)

        if choice == "found_treasure":
            coins = random.randint(50, 150)
            player.coins += coins
            return f"Вы нашли клад! +{coins} монет."

        if choice == "trap":
            damage = random.randint(10, 30)
            player.take_damage(damage)
            return f"Вы попали в ловушку! Получили {damage} урона."

        if choice == "scholar":
            exp = random.randint(50, 100)
            msgs = player.add_experience(exp)
            return (f"Вы встретили учёного. Получили опыт: "
                    f"{', '.join(msgs)}")

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
        """Боевая сцена закончена."""
        return (not self.player.is_alive) or (
            len(self.alive_enemies()) == 0
        )

    def player_attack(self, targ_index: int) -> str:
        """Атака игрока."""
        enemies = self.alive_enemies()
        if targ_index < 0 or targ_index >= len(enemies):
            return "Неверная цель."
        target = enemies[targ_index]
        dealt, raw = self.player.attack(target)
        s = f"Вы нанесли {dealt} урона ({raw} базовый) по {target.name}."
        if not target.is_alive:
            self.player.coins += target.base_coins
            lvlexp = target.max_health // 2
            msgs = self.player.add_experience(lvlexp)
            s += (f" {target.name} повержен! +{target.base_coins} монет, "
                  f"+{lvlexp} опыта.")
            self.player.enemies_defeated += 1
            for m in msgs:
                s += " " + m
        return s

    def enemy_turn(self) -> List[str]:
        """Ход врагов."""
        logs = []
        for e in self.alive_enemies():
            if not self.player.is_alive:
                break
            dmg = e.damage
            taken = self.player.take_damage(dmg)
            self.player.total_damage_taken += taken
            logs.append(f"{e.name} наносит {taken} урона вам.")
        return logs

    def attempt_escape(self) -> Tuple[bool, List[str]]:
        """Попытка бегства."""
        chance = 0.30
        logs = []
        if random.random() < chance:
            logs.append("Удачный побег!")
            return True, logs
        else:
            logs.append("Попытка побега провалена! "
                        "Враги наносят ответную атаку.")
            logs.extend(self.enemy_turn())
            return False, logs

    def use_item(self, item_id: str) -> str:
        """Использование предмета в бою."""
        return self.player.use_item(item_id, battlefield=self)
