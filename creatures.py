#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creatures: система существ, персонажа и спутников.
"""

from typing import List, Optional, Tuple
from items import Weapon, Armor, Inventory, ItemDatabase
from utils import clamp


class Creature:
    """Базовый класс существа (враг, спутник, игрок)."""

    def __init__(
        self,
        name: str,
        base_health: int,
        base_damage: int,
        base_coins: int,
        level: int = 1
    ):
        self.name = name
        self.level = level
        self.base_health = base_health
        self.base_damage = base_damage
        self.base_coins = base_coins

        self.max_health = self._scale_stat(self.base_health)
        self.health = self.max_health
        self.coins = self.base_coins + (self.level - 1) * (
            self.base_coins // 2)
        self.temp_damage = 0
        self.temp_defense = 0
        self.weapon: Optional[Weapon] = None
        self.armor: Optional[Armor] = None
        self.cause_of_death: Optional[str] = None

    def _scale_stat(self, base: int) -> int:
        """Масштабирование характеристики по уровню."""
        return int(base + (self.level - 1) * (base * 0.12))

    @property
    def damage(self) -> int:
        """Итоговый урон."""
        return max(0, self.base_damage + self.temp_damage)

    @property
    def defense(self) -> int:
        """Итоговая защита."""
        return max(0, self.temp_defense)

    @property
    def is_alive(self) -> bool:
        """Жив ли персонаж."""
        return self.health > 0

    def take_damage(self, dmg: int) -> int:
        """Получение урона."""
        if not self.is_alive:
            return 0
        effective = max(0, dmg - int(self.defense))
        self.health = max(0, self.health - effective)
        if self.health == 0:
            self.die("combat")
        return effective

    def heal(self, amount: int) -> int:
        """Восстановление здоровья."""
        if not self.is_alive:
            return 0
        old = self.health
        self.health = clamp(
            self.health + amount, 0, self.max_health
        )
        return self.health - old

    def die(self, cause: str = "combat") -> None:
        """Смерть персонажа."""
        self.cause_of_death = cause
        self.health = 0

    def equip_weapon(self, weapon: Weapon) -> None:
        """Надевание оружия."""
        if self.weapon:
            self.weapon.on_unequip(self)
        self.weapon = weapon
        weapon.on_equip(self)

    def unequip_weapon(self) -> None:
        """Снятие оружия."""
        if self.weapon:
            self.weapon.on_unequip(self)
            self.weapon = None

    def equip_armor(self, armor: Armor) -> None:
        """Надевание брони."""
        if self.armor:
            self.armor.on_unequip(self)
        self.armor = armor
        armor.on_equip(self)

    def unequip_armor(self) -> None:
        """Снятие брони."""
        if self.armor:
            self.armor.on_unequip(self)
            self.armor = None

    def description(self) -> str:
        """Описание статуса персонажа."""
        eq = []
        if self.weapon:
            eq.append(
                f"Weapon:{self.weapon.name}(+{self.weapon.damage_bonus})"
            )
        if self.armor:
            eq.append(f"Armor:{self.armor.name}(+{self.armor.defense})")
        eqs = "; ".join(eq) if eq else "No gear"
        return (f"{self.name} (Lv{self.level}) HP:{self.health}/"
                f"{self.max_health} DMG:{self.damage} DEF:{self.defense} "
                f"| {eqs}")

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "name": self.name,
            "level": self.level,
            "base_health": self.base_health,
            "base_damage": self.base_damage,
            "base_coins": self.base_coins,
            "health": self.health,
            "coins": self.coins,
            "weapon_id": self.weapon.id if self.weapon else None,
            "armor_id": self.armor.id if self.armor else None
        }


class Companion(Creature):
    """Нанятый спутник."""

    ROLES = {
        "tank": {"hp": 150, "dmg": 9, "coins": 40, "name": "Танк"},
        "archer": {"hp": 110, "dmg": 12, "coins": 40, "name": "Лучник"},
        "healer": {"hp": 100, "dmg": 6, "coins": 50, "name": "Целитель"}
    }

    def __init__(
        self,
        name: str,
        role: str,
        level: int = 1
    ):
        if role not in self.ROLES:
            role = "archer"
        r = self.ROLES[role]
        super().__init__(name, r["hp"], r["dmg"], r["coins"], level)
        self.role = role

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["role"] = self.role
        data["type"] = "companion"
        return data


class Player(Creature):
    """Игровой персонаж."""

    CLASS_STATS = {
        "warrior": {"hp": 140, "dmg": 12, "coins": 80,
                    "name": "Воин"},
        "mage": {"hp": 100, "dmg": 16, "coins": 60,
                 "name": "Маг"},
        "archer": {"hp": 120, "dmg": 11, "coins": 70,
                   "name": "Лучник"}
    }

    def __init__(self, name: str, cls: str):
        if cls not in self.CLASS_STATS:
            cls = "warrior"
        stats = self.CLASS_STATS[cls]
        super().__init__(
            name,
            stats["hp"],
            stats["dmg"],
            stats["coins"],
            level=1
        )
        self.cls = cls
        self.inventory = Inventory(capacity=40)

        # Стартовое оборудование
        starter_w = ItemDatabase.get("w_fist")
        starter_a = ItemDatabase.get("a_leather")
        if starter_w:
            self.equip_weapon(starter_w)
        if starter_a:
            self.equip_armor(starter_a)

        # Стартовые зелья
        self.inventory.add(ItemDatabase.get("p_small"), 2)

        self.experience = 0
        self.companions: List[Companion] = []
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.enemies_defeated = 0
        self.battles_fought = 0

    def add_experience(self, exp: int) -> List[str]:
        """Получение опыта и увеличение уровня."""
        msgs = []
        if exp <= 0:
            return msgs
        self.experience += exp
        msgs.append(f"+{exp} XP")
        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            self.max_health = self._scale_stat(self.base_health)
            self.base_damage = int(
                self.base_damage + (self.level - 1) *
                (self.base_damage * 0.05)
            )
            self.health = self.max_health
            msgs.append(f"🎉 Уровень! {self.name} Lv {self.level}")
        return msgs

    def attack(self, target: Creature) -> Tuple[int, int]:
        """Атака цели."""
        raw = self.damage
        dealt = target.take_damage(raw)
        self.total_damage_dealt += dealt
        return dealt, raw

    def use_item(self, item_id: str, battlefield=None) -> str:
        """Использование предмета из инвентаря."""
        item = self.inventory.get(item_id)
        if not item:
            return "У тебя нет такого предмета."
        msg = item.use(self, battlefield)
        if item.is_consumable():
            self.inventory.remove(item_id, 1)
        return msg

    def buy(self, shop, item_id: str, qty: int = 1) -> str:
        """Покупка в магазине."""
        return shop.buy(self, item_id, qty)

    def sell(self, shop, item_id: str, qty: int = 1) -> str:
        """Продажа в магазине."""
        return shop.sell(self, item_id, qty)

    def get_session_stats(self) -> dict:
        """Получить статистику сессии."""
        return {
            "name": self.name,
            "class": self.CLASS_STATS[self.cls]["name"],
            "level": self.level,
            "experience": self.experience,
            "coins": self.coins,
            "total_damage_dealt": self.total_damage_dealt,
            "total_damage_taken": self.total_damage_taken,
            "enemies_defeated": self.enemies_defeated,
            "battles_fought": self.battles_fought,
            "inventory_items": sum(q for _, q in
                                   self.inventory.list_items())
        }

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["type"] = "player"
        data["cls"] = self.cls
        data["inventory"] = self.inventory.to_dict()
        data["experience"] = self.experience
        data["companions"] = [c.to_dict() for c in self.companions]
        data["session_stats"] = self.get_session_stats()
        return data
