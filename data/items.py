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
        is_unique: bool = False,
        weapon_type: str = None
    ):
        super().__init__(id_, name, price, description, is_unique)
        # iron, steel, goblin, orc, elf, dwarf, dragon
        self.material = material
        self.base_damage = base_damage
        cond = condition if condition in WEAPON_CONDITIONS else "normal"
        self.condition = cond
        
        # Определяем тип оружия автоматически если не указан
        if weapon_type is None:
            weapon_type = self._detect_weapon_type(id_, name)
        self.weapon_type = weapon_type
        
        # Инициализируем способность оружия
        from data.weapon_abilities import get_weapon_ability
        self.ability = get_weapon_ability(
            weapon_type, is_unique, id_
        )
    
    @staticmethod
    def _detect_weapon_type(item_id: str, name: str) -> str:
        """Автоматически определить тип оружия по ID или названию."""
        name_lower = name.lower()
        id_lower = item_id.lower()
        
        if "меч" in name_lower or "sword" in id_lower:
            return "sword"
        elif "топор" in name_lower or "axe" in id_lower:
            return "axe"
        elif "лук" in name_lower or "bow" in id_lower:
            return "bow"
        elif "копье" in name_lower or "spear" in id_lower:
            return "spear"
        elif "кинжал" in name_lower or "dagger" in id_lower:
            return "dagger"
        elif "молот" in name_lower or "hammer" in id_lower \
             or "maul" in id_lower:
            return "mace"
        elif "посох" in name_lower or "staff" in id_lower:
            return "staff"
        else:
            return "sword"  # По умолчанию

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
            Weapon("w_iron_sword", "Железный меч", 120,
                   "iron", 12, "normal",
                   description="Простой, но эффективный в умелых руках")
        )
        cls.register(
            Weapon("w_iron_axe", "Железный топор", 100,
                   "iron", 9, "normal",
                   description="Выглядит круто. Это его единственное достоинство")
        )
        cls.register(
            Weapon("w_iron_spear", "Железное копье", 110,
                   "iron", 10, "normal",
                   description="Длинное и острое, хорошая дистанция")
        )
        cls.register(
            Weapon("w_iron_bow", "Железный лук", 130,
                   "iron", 11, "normal",
                   description="Простой деревянный лук с железными усилениями")
        )
        cls.register(
            Weapon("w_iron_staff", "Железный посох", 125,
                   "iron", 11, "normal",
                   description="Простой посох, используемый для магии и ударов")
        )
        cls.register(
            Weapon("w_iron_dagger", "Железный кинжал", 80,
                   "iron", 7, "normal",
                   description="Короткий и острый, хорош для скрытных атак")
        )

        # === СТАЛЬНОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_steel_sword", "Стальной меч", 280,
                   "steel", 22, "normal",
                   description="Красивый и эффективный")
        )
        cls.register(
            Weapon("w_steel_axe", "Стальной топор", 250,
                   "steel", 19, "normal",
                   description="Значительно тяжелее железного топора")
        )
        cls.register(
            Weapon("w_steel_spear", "Стальное копье", 270,
                   "steel", 25, "normal",
                   description="Прочное копье с острым наконечником")
        )
        cls.register(
            Weapon("w_steel_bow", "Стальной лук", 300,
                   "steel", 21, "normal",
                   description="Мощный лук со стальными плечами")
        )
        cls.register(
            Weapon("w_steel_staff", "Стальной посох", 290,
                   "steel", 20, "normal",
                   description="Прочный посох, усиленный металлической оплёткой")
        )
        cls.register(
            Weapon("w_steel_dagger", "Стальной кинжал", 220,
                   "steel", 16, "normal",
                   description="Идеально сбалансированный для метания")
        )

        # === ГОБЛИНСКОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_goblin_cleaver", "Гоблинский топорик", 180,
                   "goblin", 16, "normal",
                   description="Смахивает на игрушечный")
        )
        cls.register(
            Weapon("w_goblin_dagger", "Гоблинский короткий меч", 200,
                   "goblin", 19, "normal",
                   description="Не выглядит надежно")
        )
        cls.register(
            Weapon("w_goblin_spear", "Гоблинское копье", 320,
                   "goblin", 30, "normal",
                   description="Неожиданно качественное для "
                               "гоблинского оружия")
        )
        cls.register(
            Weapon("w_goblin_bow", "Гоблинский лук", 170,
                   "goblin", 15, "normal",
                   description="Кривой и ненадежный, как и его владельцы")
        )
        cls.register(
            Weapon("w_goblin_kris", "Гоблинский кинжал", 150,
                   "goblin", 13, "normal",
                   description="Ржавый и кривой, но острее, чем кажется")
        )
        cls.register(
            Weapon("w_goblin_staff", "Гоблинский посох", 160,
                   "goblin", 14, "normal",
                   description="Изогнутый посох, покрытый плесенью")
        )

        # === ОРЧЬЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_orc_maul", "Орчий топор", 450,
                   "orc", 32, "normal",
                   description="Устрашает своим видом")
        )
        cls.register(
            Weapon("w_orc_sword", "Орчий меч", 480,
                   "orc", 35, "normal",
                   description="Уродливый, но очень острый")
        )
        cls.register(
            Weapon("w_orc_spear", "Орчье копье", 460,
                   "orc", 39, "normal",
                   description="Массивное и тяжелое, пробивает "
                               "любую броню")
        )
        cls.register(
            Weapon("w_orc_bow", "Орчий лук", 440,
                   "orc", 31, "normal",
                   description="Требует огромной силы для натяжения")
        )
        cls.register(
            Weapon("w_orc_dagger", "Орчий кинжал", 380,
                   "orc", 28, "normal",
                   description="Скорее короткий меч, чем кинжал")
        )
        cls.register(
            Weapon("w_orc_staff", "Орчий посох", 420,
                   "orc", 33, "normal",
                   description="Массивный посох, пропитан кровью")
        )

        # === ЭЛЬФИЙСКОЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_elf_sword", "Эльфийский меч", 650,
                   "elf", 40, "normal",
                   description="Очень красивый и легкий")
        )
        cls.register(
            Weapon("w_elf_axe", "Эльфийский топорик", 620,
                   "elf", 37, "normal",
                   description="Небольшой. Изящный")
        )
        cls.register(
            Weapon("w_elf_spear", "Эльфийское копье", 640,
                   "elf", 45, "normal",
                   description="Идеально сбалансированное, "
                               "словно продолжение руки")
        )
        cls.register(
            Weapon("w_elf_bow", "Эльфийский лук", 950,
                   "elf", 54, "normal",
                   description="Величайшее творение эльфийских мастеров")
        )
        cls.register(
            Weapon("w_elf_dagger", "Эльфийский кинжал", 580,
                   "elf", 34, "normal",
                   description="Искусно выкованный, почти невесомый")
        )

        # === ГНОМЬЕ ОРУЖИЕ ===
        cls.register(
            Weapon("w_dwarf_sword", "Гномий широкий меч", 890,
                   "dwarf", 54, "normal",
                   description="Шедевр гномьих кузнецов")
        )
        cls.register(
            Weapon("w_dwarf_axe", "Гномий боевой топор", 840,
                   "dwarf", 51, "normal",
                   description="Невероятно прочный и смертоносный")
        )
        cls.register(
            Weapon("w_dwarf_spear", "Гномье копье", 870,
                   "dwarf", 59, "normal",
                   description="Короткое, но невероятно прочное")
        )
        cls.register(
            Weapon("w_dwarf_bow", "Гномий арбалет", 810,
                   "dwarf", 47, "normal",
                   description="Мощный механический арбалет")
        )
        cls.register(
            Weapon("w_dwarf_dagger", "Гномий кинжал", 780,
                   "dwarf", 46, "normal",
                   description="Солидный и надежный, как и все гномье")
        )
        cls.register(
            Weapon("w_dwarf_staff", "Гномий посох", 800,
                   "dwarf", 39, "normal",
                   description="Короткий посох с рунами кузнецов")
        )

        # === ДРАКОНЬЕ ОРУЖИЕ (УНИКАЛЬНОЕ) ===
        cls.register(
            Weapon("w_dragon_sword", "Клинок Драконоборца", 1200,
                   "dragon", 60, "masterwork",
                   description="Выкован из драконьей кости. Уникальное изделие",
                   is_unique=True)
        )

        # === УНИКАЛЬНЫЕ БОЕВЫЕ ПРЕДМЕТЫ ОТ БОССОВ ===
        cls.register(
            Weapon("w_mad_raider_sword",
                   "Меч безумного мародёра", 850,
                   "steel", 35, "normal",
                   description="Уникальный меч от Безумного Мародёра. "
                               "Истошает ярость и отчаяние.",
                   is_unique=True)
        )
        cls.register(
            Weapon("w_bog_master_staff",
                   "Посох Хозяина Болота", 820,
                   "orc", 40, "normal",
                   description="Уникальный посох от Хозяина Болота. "
                               "Пахнет грязью и тиной.",
                   is_unique=True)
        )
        cls.register(
            Weapon("w_dwarf_king_hammer",
                   "Молот короля гномов", 1100,
                   "dwarf", 58, "normal",
                   description="Уникальный Молот от Короля Шахт. "
                               "Выкован из драгоценных гномьих металлов.",
                   is_unique=True)
        )

        # === БРОНЯ ===
        cls.register(
            Armor("a_rags_leather", "Тряпичная броня", 30,
                  "rags", 1, "normal",
                  description="Простая тряпичная броня, лучше чем ничего")
        )
        cls.register(
            Armor("a_leather_armor", "Кожаная броня", 80,
                  "leather", 3, "normal",
                  description="Прочная кожаная броня")
        )
        cls.register(
            Armor("a_iron_plate", "Железные латы", 180,
                  "iron", 6, "normal",
                  description="Надежные железные доспехи")
        )
        cls.register(
            Armor("a_steel_plate", "Стальные доспехи", 350,
                  "steel", 10, "normal",
                  description="Качественные стальные доспехи")
        )
        cls.register(
            Armor("a_orc_mail", "Орчья кольчуга", 400,
                  "orc", 11, "normal",
                  description="Грубая, но очень прочная орчья броня")
        )
        cls.register(
            Armor("a_elf_mail", "Эльфийская броня", 400,
                  "elf", 11, "normal",
                  description="Изысканная и легкая эльфийская броня")
        )
        cls.register(
            Armor("a_dwarf_plate", "Гномьи доспехи", 600,
                  "dwarf", 14, "normal",
                  description="Невероятно прочные гномьи доспехи")
        )

        # === УНИКАЛЬНАЯ БРОНЯ ===
        cls.register(
            Armor("a_dragon_lord_plate",
                  "Доспех Повелителя Драконов", 1500,
                  "dragon", 20, "legendary",
                  description="Уникальная броня от Повелителя Драконов. "
                              "Скованы из драконьей чешуи.",
                  is_unique=True)
        )

        # === ЗЕЛЬЯ ===
        cls.register(
            Potion("p_small", "Малое зелье", 25,
                   heal_amount=40,
                   description="Восстанавливает 40 HP")
        )
        cls.register(
            Potion("p_med", "Среднее зелье", 60,
                   heal_amount=100,
                   description="Восстанавливает 100 HP")
        )
        cls.register(
            Potion("p_large", "Большое зелье", 150,
                   heal_amount=250,
                   description="Восстанавливает 250 HP")
        )
        cls.register(
            Potion("p_mega", "Мега-зелье", 300,
                   heal_amount=500,
                   description="Восстанавливает 500 HP")
        )


# Инвентарь живёт в core.models; re-export для обратной совместимости.
from core.models.inventory import Inventory  # noqa: E402,F401
