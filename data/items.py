#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Items: система предметов, инвентаря и базы данных.
Новая система с категориями материалов и состояниями предметов.
"""

from typing import List, Dict, Tuple, Optional


# === СИСТЕМНЫЕ КОНСТАНТЫ ===

# Категории материалов для оружия
WEAPON_MATERIALS = {
    "iron": "железное",
    "steel": "стальное",
    "goblin": "гоблинское",
    "orc": "орчье",
    "elf": "эльфийское",
    "dwarf": "гномье",
    "dragon": "драконье"
}

# Категории материалов для брони
ARMOR_MATERIALS = {
    "rags": "трепьё",
    "leather": "кожаная",
    "iron": "железная",
    "steel": "стальная",
    "orc": "орчья",
    "elf": "эльфийская",
    "dwarf": "гномья"
}

# Состояния оружия и их модификаторы урона
WEAPON_CONDITIONS = {
    "sharp": ("заострённое", 1.25),      # +25% урон
    "normal": ("обычное", 1.0),           # базовый урон
    "blunt": ("затупленное", 0.75),       # -25% урон
    "rusted": ("ржавое", 0.5),            # -50% урон
    "masterwork": ("мастерская работа", 1.5)  # +50% урон
}

# Состояния брони и их модификаторы защиты
ARMOR_CONDITIONS = {
    "torn": ("порванная", 0.5),           # -50% защита
    "normal": ("обычная", 1.0),           # базовая защита
    "reinforced": ("укреплённая", 1.3),   # +30% защита
    "enhanced": ("улучшенная", 1.6),      # +60% защита
    "legendary": ("легендарная обработка", 2.0)  # +100% защита
}


class Item:
    """Базовый класс предмета."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        description: str = "",
        is_unique: bool = False
    ):
        self.id = id_
        self.name = name
        self.price = price
        self.description = description
        self.is_unique = is_unique  # Уникальные предметы не продаются

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

    def is_quest_item(self) -> bool:
        """Является ли предмет квестовым."""
        return False

    def display_name(self) -> str:
        """Красивое отображение предмета."""
        unique_mark = " [УНИКАЛЬНЫЙ]" if self.is_unique else ""
        return f"{self.name}{unique_mark}"

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "type": self.__class__.__name__,
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "is_unique": self.is_unique
        }


class Weapon(Item):
    """Оружие: добавляет урон в зависимости от материала и состояния."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        material: str,
        base_damage: int,
        condition: str = "normal",
        description: str = "",
        is_unique: bool = False
    ):
        super().__init__(id_, name, price, description, is_unique)
        # iron, steel, goblin, orc, elf, dwarf, dragon
        self.material = material
        self.base_damage = base_damage
        cond = condition if condition in WEAPON_CONDITIONS else "normal"
        self.condition = cond

    @property
    def damage_bonus(self) -> int:
        """Итоговый бонус урона с учётом состояния."""
        _, multiplier = WEAPON_CONDITIONS.get(
            self.condition, ("normal", 1.0)
        )
        return int(self.base_damage * multiplier)

    @property
    def condition_display(self) -> str:
        """Отображение состояния."""
        cond_name, _ = WEAPON_CONDITIONS.get(
            self.condition, ("неизвестное", 1.0)
        )
        return cond_name

    def on_equip(self, owner) -> None:
        """При надевании добавляем урон."""
        owner.temp_damage += self.damage_bonus

    def on_unequip(self, owner) -> None:
        """При снятии убираем урон."""
        owner.temp_damage -= self.damage_bonus

    def display_name(self) -> str:
        """Красивое отображение с материалом и состоянием."""
        unique_mark = " [УНИКАЛЬНОЕ]" if self.is_unique else ""
        mat = WEAPON_MATERIALS.get(self.material, 'неизвестное')
        return (f"{self.name} ({mat}, "
                f"{self.condition_display}){unique_mark}")

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data.update({
            "material": self.material,
            "base_damage": self.base_damage,
            "condition": self.condition
        })
        return data


class Armor(Item):
    """Броня: добавляет защиту в зависимости от материала и состояния."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        material: str,
        base_defense: int,
        condition: str = "normal",
        description: str = "",
        is_unique: bool = False
    ):
        super().__init__(id_, name, price, description, is_unique)
        # rags, leather, iron, steel, orc, elf, dwarf
        self.material = material
        self.base_defense = base_defense
        cond = condition if condition in ARMOR_CONDITIONS else "normal"
        self.condition = cond

    @property
    def defense(self) -> int:
        """Итоговая защита с учётом состояния."""
        _, multiplier = ARMOR_CONDITIONS.get(
            self.condition, ("normal", 1.0)
        )
        return int(self.base_defense * multiplier)

    @property
    def condition_display(self) -> str:
        """Отображение состояния."""
        cond_name, _ = ARMOR_CONDITIONS.get(
            self.condition, ("неизвестное", 1.0)
        )
        return cond_name

    def on_equip(self, owner) -> None:
        """При надевании добавляем защиту."""
        owner.temp_defense += self.defense

    def on_unequip(self, owner) -> None:
        """При снятии убираем защиту."""
        owner.temp_defense -= self.defense

    def display_name(self) -> str:
        """Красивое отображение с материалом и состоянием."""
        unique_mark = " [УНИКАЛЬНАЯ]" if self.is_unique else ""
        mat = ARMOR_MATERIALS.get(self.material, 'неизвестная')
        return (f"{self.name} ({mat}, "
                f"{self.condition_display}){unique_mark}")

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data.update({
            "material": self.material,
            "base_defense": self.base_defense,
            "condition": self.condition
        })
        return data


class Potion(Item):
    """Зелье: восстанавливает здоровье."""
    
    def __init__(
        self,
        id_: str,
        name: str,
        price: int,
        heal_amount: int,
        description: str = ""
    ):
        super().__init__(id_, name, price, description, False)
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

    @classmethod
    def from_dict(cls, data: dict) -> 'Inventory':
        """Загрузка из словаря."""
        inventory = cls(capacity=data.get("capacity", 40))
        if "items" in data:
            ItemDatabase.initialize()
            for item_id, item_entry in data["items"].items():
                # Handle both tuple and list formats from JSON
                if isinstance(item_entry, (list, tuple)):
                    item_data, qty = item_entry[0], item_entry[1]
                else:
                    # Shouldn't happen but safe fallback
                    continue
                
                # Восстанавливаем предмет из данных
                item_type = item_data.get("type")
                if item_type == "Weapon":
                    item = Weapon(
                        item_data["id"],
                        item_data["name"],
                        item_data["price"],
                        item_data["material"],
                        item_data["base_damage"],
                        item_data.get("condition", "normal"),
                        item_data.get("description", ""),
                        item_data.get("is_unique", False)
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
                        item_data.get("is_unique", False)
                    )
                elif item_type == "Potion":
                    item = Potion(
                        item_data["id"],
                        item_data["name"],
                        item_data["price"],
                        item_data["heal_amount"],
                        item_data.get("description", "")
                    )
                else:
                    continue  # Пропускаем неизвестные типы
                inventory.items[item_id] = (item, qty)
        return inventory


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
    def find_by_material(
        cls, material: str, item_type: str = "weapon"
    ) -> List[Item]:
        """Поиск предметов по материалу."""
        if item_type == "weapon":
            return [
                it for it in cls.ITEMS.values()
                if isinstance(it, Weapon) and it.material == material
            ]
        elif item_type == "armor":
            return [
                it for it in cls.ITEMS.values()
                if isinstance(it, Armor) and it.material == material
            ]
        return []

    @classmethod
    def initialize(cls) -> None:
        """Инициализация базовых предметов."""
        # === ЖЕЛЕЗНОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_iron_sword", "Железный меч", 50,
                   "iron", 8, "normal",
                   description="Стандартное железное оружие")
        )
        cls.register(
            Weapon("w_iron_axe", "Железный топор", 45,
                   "iron", 9, "normal")
        )

        # === СТАЛЬНОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_steel_sword", "Стальной меч", 120,
                   "steel", 15, "normal")
        )
        cls.register(
            Weapon("w_steel_axe", "Стальной топор", 130,
                   "steel", 17, "normal")
        )

        # === ГОБЛИНСКОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_goblin_cleaver", "Гоблинское тесло", 80,
                   "goblin", 11, "normal")
        )
        cls.register(
            Weapon("w_goblin_dagger", "Гоблинский кинжал", 60,
                   "goblin", 9, "normal")
        )

        # === ОРЧЬЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_orc_maul", "Орчий молот", 150,
                   "orc", 18, "normal")
        )
        cls.register(
            Weapon("w_orc_sword", "Орчий меч", 140,
                   "orc", 16, "normal")
        )

        # === ЭЛЬФИЙСКОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_elf_bow", "Эльфийский лук", 160,
                   "elf", 14, "normal")
        )
        cls.register(
            Weapon("w_elf_sword", "Эльфийский клинок", 170,
                   "elf", 16, "normal")
        )

        # === ГНОМЬЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_dwarf_axe", "Гномий боевой топор", 180,
                   "dwarf", 19, "normal")
        )
        cls.register(
            Weapon("w_dwarf_hammer", "Гномий молот", 190,
                   "dwarf", 20, "normal")
        )

        # === ДРАКОНЬЕ ОРУЖИЕ (УНИКАЛЬНОЕ) ===
        cls.register(
            Weapon("w_dragon_sword", "Клинок Драконоборца", 500,
                   "dragon", 35, "masterwork",
                   description="Уникальное оружие, добытое у драконов",
                   is_unique=True)
        )

        # === ТРЕПЬЁ (БРОНЯ) ===
        cls.register(
            Armor("a_rags_leather", "Тряпичная броня", 15,
                  "rags", 2, "normal")
        )

        # === КОЖАНАЯ БРОНЯ ===
        cls.register(
            Armor("a_leather_armor", "Кожаная броня", 50,
                  "leather", 5, "normal")
        )

        # === ЖЕЛЕЗНАЯ БРОНЯ ===
        cls.register(
            Armor("a_iron_plate", "Железные латы", 100,
                  "iron", 10, "normal")
        )

        # === СТАЛЬНАЯ БРОНЯ ===
        cls.register(
            Armor("a_steel_plate", "Стальные доспехи", 180,
                  "steel", 15, "normal")
        )

        # === ОРЧЬЯ БРОНЯ ===
        cls.register(
            Armor("a_orc_mail", "Орчья кольчуга", 160,
                  "orc", 14, "normal")
        )

        # === ЭЛЬФИЙСКАЯ БРОНЯ ===
        cls.register(
            Armor("a_elf_mail", "Эльфийская броня", 170,
                  "elf", 13, "normal")
        )

        # === ГНОМЬЯ БРОНЯ (ЛУЧШАЯ) ===
        cls.register(
            Armor("a_dwarf_plate", "Гномьи доспехи", 200,
                  "dwarf", 18, "normal")
        )

        # === УНИКАЛЬНЫЕ БОЕВЫЕ ПРЕДМЕТЫ ОТ БОССОВ ===
        
        # От босса 1 (Безумный мародёр) - Меч безумного мародёра
        cls.register(
            Weapon("w_mad_raider_sword",
                   "Меч безумного мародёра", 350,
                   "steel", 28, "masterwork",
                   description="Уникальный меч от Безумного Мародёра. "
                               "Истошает ярость и отчаяние.",
                   is_unique=True)
        )

        # От босса 2 (Хозяин Болота) - Посох Хозяина Болота
        cls.register(
            Weapon("w_bog_master_staff",
                   "Посох Хозяина Болота", 340,
                   "orc", 26, "masterwork",
                   description="Уникальный посох от Хозяина Болота. "
                               "Пахнет грязью и тиной.",
                   is_unique=True)
        )

        # От босса 3 (Король Шахт) - Молот короля гномов
        cls.register(
            Weapon("w_dwarf_king_hammer",
                   "Молот короля гномов", 360,
                   "dwarf", 30, "masterwork",
                   description="Уникальный молот от Короля Шахт. "
                               "Выкован из драгоценных гномьих металлов.",
                   is_unique=True)
        )

        # От босса 4 (Повелитель Драконов) - Доспех Повелителя Драконов
        cls.register(
            Armor("a_dragon_lord_plate",
                  "Доспех Повелителя Драконов", 400,
                  "dragon", 28, "legendary",
                  description="Уникальная броня от Повелителя Драконов. "
                              "Скованы из драконьей чешуи.",
                  is_unique=True)
        )

        # === ЗЕЛЬЯ ===
        cls.register(
            Potion("p_small", "Малое зелье", 25,
                   heal_amount=40, description="Восстанавливает 40 HP")
        )
        cls.register(
            Potion("p_med", "Среднее зелье", 60,
                   heal_amount=100, description="Восстанавливает 100 HP")
        )
        cls.register(
            Potion("p_large", "Большое зелье", 150,
                   heal_amount=250, description="Восстанавливает 250 HP")
        )
        cls.register(
            Potion("p_mega", "Мега-зелье", 300,
                   heal_amount=500, description="Восстанавливает 500 HP")
        )
