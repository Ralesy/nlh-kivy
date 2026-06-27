#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Спутник игрока: роли танк / лучник / целитель с собственной экипировкой.
"""

from __future__ import annotations

from core.models.creature import Creature
from data.items import ItemDatabase


class Companion(Creature):
    """Нанятый боевой спутник."""

    ROLES = {
        "tank": {"hp": 50, "dmg": 3, "coins": 30, "name": "Танк"},
        "archer": {"hp": 37, "dmg": 4, "coins": 30, "name": "Лучник"},
        "healer": {"hp": 33, "dmg": 2, "coins": 35, "name": "Целитель"},
    }

    def __init__(self, name: str, role: str, level: int = 1):
        """Создать спутника с ролью и уровнем."""
        if role not in self.ROLES:
            role = "archer"
        role_data = self.ROLES[role]
        super().__init__(
            name,
            role_data["hp"],
            role_data["dmg"],
            role_data["coins"],
            level,
        )
        self.role = role
        # Стойка в real-time combat (по умолчанию агрессивная)
        self.stance = "aggressive"

    def to_dict(self) -> dict:
        """Сериализация для сохранения."""
        data = super().to_dict()
        data["role"] = self.role
        data["type"] = "companion"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Companion:
        """Восстановить спутника из сохранения."""
        companion = cls(data["name"], data["role"], data["level"])
        companion.health = data["health"]
        companion.max_health = companion._scale_stat(companion.base_health)
        companion.coins = data["coins"]
        companion.temp_damage = 0
        companion.temp_defense = 0

        ItemDatabase.initialize()
        if data.get("weapon_id"):
            weapon = ItemDatabase.get(data["weapon_id"])
            if weapon:
                companion.equip_weapon(weapon)

        if data.get("armor_id"):
            armor = ItemDatabase.get(data["armor_id"])
            if armor:
                companion.equip_armor(armor)

        return companion
