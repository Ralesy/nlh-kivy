#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генерация врагов и боссов для локаций.
"""

import random
from typing import List, Optional

from core.creatures import Creature
from core.utils import clamp
from data.enemies import EnemyDatabase
from data.items import Armor, ItemDatabase, Weapon


class EnemyGenerator:
    """Генератор врагов на основе шаблонов EnemyDatabase."""

    @staticmethod
    def _equip_from_loot_table(enemy: Creature) -> None:
        """Экипировать врага предметами из таблицы лута шаблона."""
        template = getattr(enemy, "_template", None)
        if not template or not template.loot_table:
            return

        ItemDatabase.initialize()
        for item_id, _chance in template.loot_table:
            item = ItemDatabase.get(item_id)
            if item is None:
                continue
            if isinstance(item, Armor) and enemy.armor is None:
                enemy.equip_armor(item)
            elif isinstance(item, Weapon) and enemy.weapon is None:
                enemy.equip_weapon(item)
            if enemy.weapon and enemy.armor:
                break

    @staticmethod
    def generate_for_location(
        location_id: str,
        player_level: int,
        count: int = 1,
    ) -> List[Creature]:
        """
        Сгенерировать группу врагов для локации.

        Args:
            location_id: ID локации.
            player_level: уровень игрока для масштабирования.
            count: количество врагов.

        Returns:
            Список существ Creature.
        """
        enemies: List[Creature] = []
        location_enemies = EnemyDatabase.get_by_location(location_id)
        if not location_enemies:
            return enemies

        count = max(1, int(count))
        for _ in range(count):
            enemy_template = random.choice(location_enemies)
            level = clamp(
                player_level + random.randint(-1, 2),
                1,
                player_level + 3,
            )
            enemy = Creature(
                enemy_template.name,
                enemy_template.base_health,
                enemy_template.base_damage,
                enemy_template.base_coins,
                level=level,
            )
            enemy._template = enemy_template
            EnemyGenerator._equip_from_loot_table(enemy)
            enemies.append(enemy)

        return enemies

    @staticmethod
    def generate_boss(boss_id: str) -> Optional[Creature]:
        """
        Сгенерировать босса по ID шаблона.

        Returns:
            Creature или None, если шаблон не найден.
        """
        enemy_template = EnemyDatabase.get(boss_id)
        if enemy_template is None:
            return None

        enemy = Creature(
            enemy_template.name,
            enemy_template.base_health,
            enemy_template.base_damage,
            enemy_template.base_coins,
            level=10,
        )
        enemy._template = enemy_template
        EnemyGenerator._equip_from_loot_table(enemy)
        return enemy
