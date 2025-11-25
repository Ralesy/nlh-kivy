#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Weapon abilities: система способностей оружия.
"""

from enum import Enum


class WeaponType(Enum):
    """Типы оружия с их способностями."""
    SWORD = "sword"           # Двойной удар
    AXE = "axe"               # Игнорирование брони
    BOW = "bow"               # Две стрелы (двум врагам)
    SPEAR = "spear"           # Без способностей, но сильнее
    DAGGER = "dagger"         # Повышенный крит
    MACE = "mace"             # Молот - без способностей
    STAFF = "staff"           # Посох - урон всем


# Способности оружия
class WeaponAbility:
    """Базовый класс способности оружия."""
    
    def __init__(self, name: str, ability_type: str):
        self.name = name
        self.ability_type = ability_type  # "passive" или "active"
        # Для активных способностей - использована ли за битву
        self.is_used = False
    
    def reset_usage(self):
        """Сброс использования способности на новую битву."""
        self.is_used = False


# Пассивные способности
class ArmorIgnoreAbility(WeaponAbility):
    """Топоры: игнорирование 30% брони."""
    
    def __init__(self):
        super().__init__("Игнорирование брони", "passive")
        self.armor_ignore = 0.30  # 30% брони игнорируется


class CriticalBoostAbility(WeaponAbility):
    """Кинжалы: x2 шанс критического удара."""
    
    def __init__(self):
        super().__init__("Боевое искусство", "passive")
        self.crit_multiplier = 2.0  # x2 шанс крита


class DamageScalingAbility(WeaponAbility):
    """Меч безумного мародёра: урон +2 за каждый удар."""
    
    def __init__(self):
        super().__init__("Ярость", "passive")
        self.damage_per_hit = 2  # +2 урона за удар


# Активные способности (1 раз за битву)
class DoubleStrikeAbility(WeaponAbility):
    """Мечи: двойной удар."""
    
    def __init__(self):
        super().__init__("Двойной удар", "active")


class DoubleArrowAbility(WeaponAbility):
    """Луки: две стрелы по двум врагам."""
    
    def __init__(self):
        super().__init__("Две стрелы", "active")


class StaffAoEAbility(WeaponAbility):
    """Посох: урон всем врагам на поле."""
    
    def __init__(self):
        super().__init__("Магический взрыв", "active")


def get_weapon_ability(
    weapon_type: str,
    is_unique: bool = False,
    unique_id: str = None
) -> WeaponAbility:
    """Получить способность оружия по типу."""
    
    # Уникальное боссовое оружие
    if is_unique and unique_id == "w_dragon_sword":
        return DoubleStrikeAbility()  # Как обычный меч
    elif is_unique and unique_id == "w_mad_raider_sword":
        return DamageScalingAbility()  # Ярость
    elif is_unique and unique_id == "w_bog_master_staff":
        return StaffAoEAbility()  # Магический взрыв
    elif is_unique and unique_id == "w_dwarf_king_hammer":
        return None  # Без способностей
    
    # Обычное оружие по типу
    if weapon_type == "sword":
        return DoubleStrikeAbility()
    elif weapon_type == "axe":
        return ArmorIgnoreAbility()
    elif weapon_type == "bow":
        return DoubleArrowAbility()
    elif weapon_type == "spear":
        return None  # Без способностей
    elif weapon_type == "dagger":
        return CriticalBoostAbility()
    elif weapon_type == "mace":
        return None  # Без способностей
    elif weapon_type == "staff":
        return StaffAoEAbility()
    
    return None
