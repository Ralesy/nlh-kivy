#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Инвентарь игрока: хранение предметов с проверкой вместимости и количества.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from data.items import Item


class Inventory:
    """Система инвентаря с защитой от некорректных операций."""

    def __init__(self, capacity: int = 20):
        """Создать инвентарь с заданной вместимостью."""
        self.items: Dict[str, Tuple[Item, int]] = {}
        self.capacity = max(1, int(capacity))

    @property
    def used_slots(self) -> int:
        """Сколько слотов занято (сумма количеств всех предметов)."""
        return sum(qty for _, qty in self.items.values())

    @property
    def free_slots(self) -> int:
        """Сколько слотов свободно."""
        return max(0, self.capacity - self.used_slots)

    def add(self, item: Item, qty: int = 1) -> bool:
        """
        Добавить предмет в инвентарь.

        Returns:
            True, если предмет добавлен; False при переполнении или неверных аргументах.
        """
        if item is None or qty <= 0:
            return False
        if not self.has_space_for(qty):
            return False

        entry = self.items.get(item.id)
        if entry:
            self.items[item.id] = (entry[0], entry[1] + qty)
        else:
            self.items[item.id] = (item, qty)
        return True

    def remove(self, item_id: str, qty: int = 1) -> bool:
        """
        Удалить указанное количество предмета.

        Returns:
            False, если предмета нет, qty <= 0 или запрошено больше, чем есть.
        """
        if qty <= 0:
            return False

        entry = self.items.get(item_id)
        if not entry:
            return False

        item, current_qty = entry
        if qty > current_qty:
            return False

        if qty == current_qty:
            del self.items[item_id]
        else:
            self.items[item_id] = (item, current_qty - qty)
        return True

    def get(self, item_id: str) -> Optional[Item]:
        """Получить объект предмета по ID или None."""
        entry = self.items.get(item_id)
        return entry[0] if entry else None

    def qty(self, item_id: str) -> int:
        """Количество предмета с данным ID."""
        entry = self.items.get(item_id)
        return entry[1] if entry else 0

    def list_items(self) -> List[Tuple[Item, int]]:
        """Список пар (предмет, количество)."""
        return list(self.items.values())

    def has_space_for(self, qty: int = 1) -> bool:
        """Проверить, поместится ли qty предметов."""
        if qty <= 0:
            return True
        return self.used_slots + qty <= self.capacity

    def __str__(self) -> str:
        """Текстовое представление содержимого."""
        if not self.items:
            return "Пусто"
        lines = []
        for item, qty in self.list_items():
            desc = item.description or "без описания"
            lines.append(f"{item.display_name()} x{qty} — {desc}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Сериализация для сохранения."""
        return {
            "items": {
                item_id: (item.to_dict(), qty)
                for item_id, (item, qty) in self.items.items()
            },
            "capacity": self.capacity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Inventory:
        """Восстановить инвентарь из словаря сохранения."""
        from data.items import Armor, ItemDatabase, Potion, Weapon

        inventory = cls(capacity=data.get("capacity", 40))
        if "items" not in data:
            return inventory

        ItemDatabase.initialize()
        for item_id, item_entry in data["items"].items():
            if not isinstance(item_entry, (list, tuple)) or len(item_entry) < 2:
                continue

            item_data, qty = item_entry[0], item_entry[1]
            if not isinstance(qty, int) or qty <= 0:
                continue

            item_type = item_data.get("type")
            item = None
            if item_type == "Weapon":
                item = Weapon(
                    item_data["id"],
                    item_data["name"],
                    item_data["price"],
                    item_data["material"],
                    item_data["base_damage"],
                    item_data.get("condition", "normal"),
                    item_data.get("description", ""),
                    item_data.get("is_unique", False),
                )
            elif item_type == "Armor":
                item = Armor(
                    item_data["id"],
                    item_data["name"],
                    item_data["price"],
                    item_data["material"],
                    item_data["base_defense"],
                    item_data.get("condition", "normal"),
                    item_data.get("description", ""),
                    item_data.get("is_unique", False),
                )
            elif item_type == "Potion":
                item = Potion(
                    item_data["id"],
                    item_data["name"],
                    item_data["price"],
                    item_data["heal_amount"],
                    item_data.get("description", ""),
                )

            if item is not None:
                inventory.items[item_id] = (item, qty)

        return inventory
