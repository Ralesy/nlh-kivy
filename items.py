#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Items: система предметов, инвентаря и базы данных.
"""

from typing import List, Dict, Tuple, Optional
from utils import RARITIES, RARITY_ICONS


class Item:
    """Базовый класс предмета."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        rarity: str = "Common",
        description: str = ""
    ):
        self.id = id_
        self.name = name
        self.price = price
        self.rarity = rarity if rarity in RARITIES else "Common"
        self.description = description

    def use(self, user, battlefield=None) -> str:
        """Использование предмета."""
        return f"{self.name} нельзя использовать."

    def on_equip(self, owner) -> None:
        """Событие надевания."""
        pass

    def on_unequip(self, owner) -> None:
        """Событие снятия."""
        pass

    def is_consumable(self) -> bool:
        """Расходный ли предмет."""
        return False

    def display_name(self) -> str:
        """Красивое отображение предмета."""
        icon = RARITY_ICONS.get(self.rarity, "")
        return f"{icon} {self.name} [{self.id}] ({self.rarity})"

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "type": self.__class__.__name__,
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "rarity": self.rarity,
            "description": self.description
        }


class Weapon(Item):
    """Оружие: добавляет урон."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        damage_bonus: int,
        rarity: str = "Common",
        description: str = ""
    ):
        super().__init__(id_, name, price, rarity, description)
        self.damage_bonus = damage_bonus

    def on_equip(self, owner) -> None:
        """При надевании добавляем урон."""
        owner.temp_damage += self.damage_bonus

    def on_unequip(self, owner) -> None:
        """При снятии убираем урон."""
        owner.temp_damage -= self.damage_bonus

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["damage_bonus"] = self.damage_bonus
        return data


class Armor(Item):
    """Броня: добавляет защиту."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        defense: int,
        rarity: str = "Common",
        description: str = ""
    ):
        super().__init__(id_, name, price, rarity, description)
        self.defense = defense

    def on_equip(self, owner) -> None:
        """При надевании добавляем защиту."""
        owner.temp_defense += self.defense

    def on_unequip(self, owner) -> None:
        """При снятии убираем защиту."""
        owner.temp_defense -= self.defense

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["defense"] = self.defense
        return data


class Potion(Item):
    """Зелье: восстанавливает здоровье."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        heal_amount: int,
        rarity: str = "Common",
        description: str = ""
    ):
        super().__init__(id_, name, price, rarity, description)
        self.heal_amount = heal_amount

    def use(self, user, battlefield=None) -> str:
        """Использование зелья."""
        if not user.is_alive:
            return (f"{user.name} мёртв — нельзя использовать "
                    f"{self.name}.")
        healed = user.heal(self.heal_amount)
        return (f"{user.name} использовал {self.name} и восстановил "
                f"{healed} HP.")

    def is_consumable(self) -> bool:
        """Зелья расходуются."""
        return True

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["heal_amount"] = self.heal_amount
        return data


class Inventory:
    """Система инвентаря."""
    
    def __init__(self, capacity: int = 40):
        # mapping: item_id -> (Item, qty)
        self.items: Dict[str, Tuple[Item, int]] = {}
        self.capacity = capacity

    def add(self, item: Item, qty: int = 1) -> bool:
        """Добавление предмета."""
        total = sum(q for _, q in self.items.values())
        if total + qty > self.capacity:
            return False
        entry = self.items.get(item.id)
        if entry:
            self.items[item.id] = (entry[0], entry[1] + qty)
        else:
            self.items[item.id] = (item, qty)
        return True

    def remove(self, item_id: str, qty: int = 1) -> bool:
        """Удаление предмета."""
        entry = self.items.get(item_id)
        if not entry:
            return False
        item, cur = entry
        if qty >= cur:
            del self.items[item_id]
        else:
            self.items[item_id] = (item, cur - qty)
        return True

    def get(self, item_id: str) -> Optional[Item]:
        """Получение предмета."""
        entry = self.items.get(item_id)
        return entry[0] if entry else None

    def qty(self, item_id: str) -> int:
        """Количество предмета."""
        entry = self.items.get(item_id)
        return entry[1] if entry else 0

    def list_items(self) -> List[Tuple[Item, int]]:
        """Список предметов."""
        return list(self.items.values())

    def has_space_for(self, qty: int = 1) -> bool:
        """Проверка свободного места."""
        total = sum(q for _, q in self.items.values())
        return total + qty <= self.capacity

    def __str__(self) -> str:
        """Строковое представление."""
        if not self.items:
            return "Пусто"
        lines = []
        for item, qty in self.list_items():
            desc = item.description or 'без описания'
            lines.append(f"{item.display_name()} x{qty} — {desc}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "items": {
                item_id: (item.to_dict(), qty)
                for item_id, (item, qty) in self.items.items()
            },
            "capacity": self.capacity
        }


class ItemDatabase:
    """База данных предметов."""
    
    ITEMS: Dict[str, Item] = {}

    @classmethod
    def register(cls, item: Item) -> None:
        """Регистрация предмета."""
        cls.ITEMS[item.id] = item

    @classmethod
    def get(cls, item_id: str) -> Optional[Item]:
        """Получение предмета по ID."""
        return cls.ITEMS.get(item_id)

    @classmethod
    def find_by_rarity(cls, rarity: str) -> List[Item]:
        """Поиск предметов по редкости."""
        return [it for it in cls.ITEMS.values() if it.rarity == rarity]

    @classmethod
    def initialize(cls) -> None:
        """Инициализация базовых предметов."""
        # Оружие
        cls.register(
            Weapon("w_fist", "Кулаки", 0, damage_bonus=2, rarity="Common",
                   description="Стартовое оружие")
        )
        cls.register(
            Weapon("w_short", "Короткий меч +", 25,
                   damage_bonus=4, rarity="Common")
        )
        cls.register(
            Weapon("w_sword", "Одноручный меч", 80,
                   damage_bonus=9, rarity="Uncommon")
        )
        cls.register(
            Weapon("w_staff", "Посох мага", 120,
                   damage_bonus=11, rarity="Rare")
        )
        cls.register(
            Weapon("w_axe", "Топор", 150, damage_bonus=14, rarity="Rare")
        )
        cls.register(
            Weapon("w_great_sword", "Огромный меч", 300,
                   damage_bonus=22, rarity="Epic")
        )
        cls.register(
            Weapon("w_legend", "Меч Легенд", 800,
                   damage_bonus=40, rarity="Legendary")
        )

        # Броня
        cls.register(
            Armor("a_leather", "Кожаная броня", 20, defense=2, rarity="Common")
        )
        cls.register(
            Armor("a_chain", "Кольчуга", 60, defense=5, rarity="Uncommon")
        )
        cls.register(
            Armor("a_plate", "Латы", 150, defense=9, rarity="Rare")
        )
        cls.register(
            Armor("a_epic", "Боевые доспехи", 300, defense=15, rarity="Epic")
        )
        cls.register(
            Armor("a_legend", "Доспех героя", 800,
                  defense=30, rarity="Legendary")
        )

        # Зелья (сбалансированы по эффективности)
        cls.register(
            Potion("p_small", "Малое зелье", 10,
                   heal_amount=25, rarity="Common")
        )
        cls.register(
            Potion("p_med", "Среднее зелье", 30,
                   heal_amount=70, rarity="Uncommon")
        )
        cls.register(
            Potion("p_large", "Большое зелье", 80,
                   heal_amount=180, rarity="Rare")
        )
        cls.register(
            Potion("p_mega", "Мега-зелье", 200, heal_amount=350, rarity="Epic")
        )
