#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Базовый класс существа: враги, спутники и игрок наследуют общую боевую логику.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from core.utils import clamp

if TYPE_CHECKING:
    from data.items import Armor, Weapon


class Creature:
    """Базовый класс существа (враг, спутник, игрок)."""

    def __init__(
        self,
        name: str,
        base_health: int,
        base_damage: int,
        base_coins: int,
        level: int = 1,
    ):
        """Инициализировать существо с базовыми характеристиками."""
        self.name = name
        self.level = max(1, int(level))
        self.base_health = max(1, int(base_health))
        self.base_damage = max(0, int(base_damage))
        self.base_coins = max(0, int(base_coins))

        self.max_health = self._scale_stat(self.base_health)
        self._health = self.max_health
        self._coins = self.base_coins + (self.level - 1) * (self.base_coins // 2)
        self.temp_damage = 0
        self.temp_defense = 0
        self.weapon: Optional[Weapon] = None
        self.armor: Optional[Armor] = None
        self.cause_of_death: Optional[str] = None
        self._template = None  # ссылка на шаблон врага для лута и XP

    def _scale_stat(self, base: int) -> int:
        """Масштабировать характеристику по уровню."""
        return int(base + (self.level - 1) * (base * 0.12))

    @property
    def damage(self) -> int:
        """Итоговый урон с учётом экипировки и временных модификаторов."""
        return max(0, self.base_damage + self.temp_damage)

    @property
    def defense(self) -> int:
        """Итоговая защита."""
        return max(0, self.temp_defense)

    @property
    def is_alive(self) -> bool:
        """Жив ли персонаж."""
        return self.health > 0

    @property
    def health(self) -> int:
        """Текущее здоровье."""
        return getattr(self, "_health", 0)

    @health.setter
    def health(self, value: int) -> None:
        """Установить здоровье с ограничением [0, max_health]."""
        self._health = int(clamp(value, 0, self.max_health))

    @property
    def coins(self) -> int:
        """Количество монет."""
        return getattr(self, "_coins", 0)

    @coins.setter
    def coins(self, value: int) -> None:
        """Установить монеты; отрицательные значения приводятся к 0."""
        self._coins = max(0, int(value))

    @property
    def base_xp(self) -> int:
        """Опыт за убийство (из шаблона врага или стандартная формула)."""
        if self._template:
            return self._template.xp_reward
        return int(self.base_health * 0.5 + self.base_damage * 0.8)

    def generate_loot(self) -> Optional[List[Tuple[str, int]]]:
        """Сгенерировать лут при убийстве, если есть шаблон врага."""
        if self._template:
            return self._template.generate_loot()
        return None

    def take_damage(self, dmg: int) -> int:
        """
        Получить урон с учётом защиты.

        Returns:
            Фактически нанесённый урон (после защиты).
        """
        if not self.is_alive:
            return 0
        raw = max(0, int(dmg))
        effective = max(0, raw - int(self.defense))
        self.health = self.health - effective
        if self.health == 0:
            self.die("combat")
        return effective

    def heal(self, amount: int) -> int:
        """
        Восстановить здоровье.

        Returns:
            Сколько HP фактически восстановлено.
        """
        if not self.is_alive or amount <= 0:
            return 0
        old = self.health
        self.health = old + int(amount)
        return self.health - old

    def die(self, cause: str = "combat") -> None:
        """Зафиксировать смерть существа."""
        self.cause_of_death = cause
        self.health = 0

    def equip_weapon(self, weapon: Weapon) -> None:
        """Надеть оружие, сняв предыдущее."""
        if self.weapon:
            self.weapon.on_unequip(self)
        self.weapon = weapon
        weapon.on_equip(self)

    def unequip_weapon(self) -> None:
        """Снять оружие."""
        if self.weapon:
            self.weapon.on_unequip(self)
            self.weapon = None

    def equip_armor(self, armor: Armor) -> None:
        """Надеть броню, сняв предыдущую."""
        if self.armor:
            self.armor.on_unequip(self)
        self.armor = armor
        armor.on_equip(self)

    def unequip_armor(self) -> None:
        """Снять броню."""
        if self.armor:
            self.armor.on_unequip(self)
            self.armor = None

    def description(self) -> str:
        """Краткое текстовое описание состояния."""
        eq = []
        if self.weapon:
            dmg_bonus = (
                self.weapon.damage_bonus
                if hasattr(self.weapon, "damage_bonus")
                else self.weapon.base_damage
            )
            eq.append(f"Weapon:{self.weapon.name}(+{dmg_bonus})")
        if self.armor:
            def_bonus = (
                self.armor.defense
                if hasattr(self.armor, "defense")
                else self.armor.base_defense
            )
            eq.append(f"Armor:{self.armor.name}(+{def_bonus})")
        eqs = "; ".join(eq) if eq else "No gear"
        return (
            f"{self.name} (Lv{self.level}) HP:{self.health}/"
            f"{self.max_health} DMG:{self.damage} DEF:{self.defense} "
            f"| {eqs}"
        )

    def to_dict(self) -> dict:
        """Сериализация для сохранения."""
        return {
            "name": self.name,
            "level": self.level,
            "base_health": self.base_health,
            "base_damage": self.base_damage,
            "base_coins": self.base_coins,
            "health": self.health,
            "coins": self.coins,
            "weapon_id": self.weapon.id if self.weapon else None,
            "armor_id": self.armor.id if self.armor else None,
        }
