#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест системы управления компаньонами через UI логику.
Имитирует то, как система экипировки работает в игре через CompanionManagementScreen.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.creatures import Player, Companion
from data.items import ItemDatabase


def simulate_ui_equip(player, companion, item, item_type):
    """Имитирует логику _equip_item из UI."""
    old_item = None
    
    if item_type == 'weapon':
        old_item = companion.weapon
        # Удалить из инвентаря перед экипировкой
        player.inventory.remove(item.id, 1)
        # Использовать метод equip_weapon
        companion.equip_weapon(item)
    elif item_type == 'armor':
        old_item = companion.armor
        # Удалить из инвентаря перед экипировкой
        player.inventory.remove(item.id, 1)
        # Использовать метод equip_armor
        companion.equip_armor(item)
    
    # Вернуть старый предмет в инвентарь
    if old_item:
        player.inventory.add(old_item, 1)


def simulate_ui_unequip(player, companion, item_type):
    """Имитирует логику _unequip_item из UI."""
    item = None
    
    if item_type == 'weapon':
        item = companion.weapon
        if item:
            companion.unequip_weapon()
    elif item_type == 'armor':
        item = companion.armor
        if item:
            companion.unequip_armor()
    
    if item:
        player.inventory.add(item, 1)


def test_ui_companion_equip():
    """Тест экипировки компаньона через UI логику."""
    print("\n=== ТЕСТ ЭКИПИРОВКИ ЧЕРЕЗ UI ЛОГИКУ ===\n")
    
    ItemDatabase.initialize()
    
    # Создаем игрока
    player = Player("Герой", "warrior")
    print(f"Создан игрок: {player.name}")
    
    # Нанимаем компаньона
    companion = Companion("Торг", "tank", level=5)
    player.companions.append(companion)
    print(f"Нанят компаньон: {companion.name} (уровень {companion.level})")
    
    # Даем игроку оружие и броню
    sword = ItemDatabase.get("w_steel_sword")
    armor = ItemDatabase.get("a_iron_plate")
    player.inventory.add(sword, 1)
    player.inventory.add(armor, 1)
    print(f"Добавлены в инвентарь: {sword.display_name()}, {armor.display_name()}")
    
    print(f"\nНАЧАЛЬНОЕ СОСТОЯНИЕ:")
    print(f" Компаньон - Урон: {companion.damage}, Защита: {companion.defense}")
    print(f" Оружие: {companion.weapon.name if companion.weapon else 'Нет'}")
    print(f" Броня: {companion.armor.name if companion.armor else 'Нет'}")
    
    initial_damage = companion.damage
    initial_defense = companion.defense
    
    # === ТЕСТ 1: Экипировка оружия ===
    print(f"\n ТЕСТ 1: Экипировка оружия...")
    simulate_ui_equip(player, companion, sword, 'weapon')
    
    print(f" Урон: {initial_damage} → {companion.damage}")
    if companion.damage > initial_damage:
        print(f" Урон увеличился на {companion.damage - initial_damage}")
    else:
        print(f" ОШИБКА: Урон не увеличился!")
        return False
    
    if companion.weapon == sword:
        print(f" Оружие успешно экипировано: {companion.weapon.display_name()}")
    else:
        print(f" ОШИБКА: Оружие не экипировано!")
        return False
    
    # === ТЕСТ 2: Экипировка брони ===
    print(f"\n ТЕСТ 2: Экипировка брони...")
    simulate_ui_equip(player, companion, armor, 'armor')
    
    print(f" Защита: {initial_defense} → {companion.defense}")
    if companion.defense > initial_defense:
        print(f" Защита увеличилась на {companion.defense - initial_defense}")
    else:
        print(f" ОШИБКА: Защита не увеличилась!")
        return False
    
    if companion.armor == armor:
        print(f" Броня успешно экипирована: {companion.armor.display_name()}")
    else:
        print(f" ОШИБКА: Броня не экипирована!")
        return False
    
    weapon_damage = companion.damage
    armor_defense = companion.defense
    
    # === ТЕСТ 3: Снятие оружия ===
    print(f"\n[Оружие] ТЕСТ 3: Снятие оружия...")
    simulate_ui_unequip(player, companion, 'weapon')
    
    print(f" Урон: {weapon_damage} → {companion.damage}")
    if companion.damage == initial_damage:
        print(f" Урон вернулся к исходному значению")
    else:
        print(f" ОШИБКА: Урон != {initial_damage}, получено {companion.damage}")
        return False
    
    if companion.weapon is None:
        print(f" Оружие снято")
    else:
        print(f" ОШИБКА: Оружие не снято!")
        return False
    
    # === ТЕСТ 4: Снятие брони ===
    print(f"\n ТЕСТ 4: Снятие брони...")
    simulate_ui_unequip(player, companion, 'armor')
    
    print(f" Защита: {armor_defense} → {companion.defense}")
    if companion.defense == initial_defense:
        print(f" Защита вернулась к исходному значению")
    else:
        print(f" ОШИБКА: Защита != {initial_defense}, получено {companion.defense}")
        return False
    
    if companion.armor is None:
        print(f" Броня снята")
    else:
        print(f" ОШИБКА: Броня не снята!")
        return False
    
    # === ТЕСТ 5: Проверка инвентаря ===
    print(f"\n📦 ТЕСТ 5: Проверка инвентаря...")
    sword_qty = player.inventory.qty(sword.id)
    armor_qty = player.inventory.qty(armor.id)
    
    print(f" Оружие в инвентаре: {sword_qty}")
    print(f" Броня в инвентаре: {armor_qty}")
    
    if sword_qty == 1 and armor_qty == 1:
        print(f" Все предметы вернулись в инвентарь")
    else:
        print(f" ОШИБКА: Предметы не в инвентаре!")
        return False
    
    print(f"\n" + "="*50)
    print("ВСЕ ТЕСТЫ UI ЛОГИКИ ПРОЙДЕНЫ УСПЕШНО!")
    print("="*50)
    return True


if __name__ == "__main__":
    success = test_ui_companion_equip()
    sys.exit(0 if success else 1)
