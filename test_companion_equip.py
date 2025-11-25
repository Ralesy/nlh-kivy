#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест системы экипировки компаньонов.
Проверяет, что характеристики (damage и defense) обновляются при экипировке.
"""

import sys
import os

# Добавить корневую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.creatures import Player, Companion
from data.items import ItemDatabase


def test_companion_equip():
    """Тест экипировки компаньона."""
    print("\n=== ТЕСТ ЭКИПИРОВКИ КОМПАНЬОНОВ ===\n")
    
    # Инициализация БД
    ItemDatabase.initialize()
    
    # Создаем игрока
    player = Player("Герой", "warrior")
    print(f"✅ Создан игрок: {player.name} (класс: {player.cls})")
    
    # Нанимаем компаньона
    companion = Companion("Торг", "tank", level=1)
    player.companions.append(companion)
    print(f"✅ Нанят компаньон: {companion.name} (роль: {companion.role})")
    
    # Проверяем начальные характеристики
    print(f"\n📊 НАЧАЛЬНЫЕ ХАРАКТЕРИСТИКИ:")
    print(f"   Урон: {companion.damage}")
    print(f"   Защита: {companion.defense}")
    print(f"   HP: {companion.health}/{companion.max_health}")
    
    initial_damage = companion.damage
    initial_defense = companion.defense
    
    # Получаем оружие из БД
    sword = ItemDatabase.get("w_steel_sword")
    armor = ItemDatabase.get("a_iron_plate")
    
    if not sword or not armor:
        print("❌ ОШИБКА: Не найдены предметы в БД!")
        return False
    
    print(f"\n🔍 Найденные предметы:")
    print(f"   Оружие: {sword.display_name()}")
    print(f"   Броня: {armor.display_name()}")
    
    # Экипируем оружие
    print(f"\n⚔️  Экипируем оружие {sword.display_name()}...")
    companion.equip_weapon(sword)
    damage_after_weapon = companion.damage
    print(f"   Урон ДО: {initial_damage}, ПОСЛЕ: {damage_after_weapon}")
    
    if damage_after_weapon > initial_damage:
        print(f"   ✅ УСПЕХ: Урон увеличился на {damage_after_weapon - initial_damage}")
    else:
        print(f"   ❌ ОШИБКА: Урон не увеличился!")
        return False
    
    # Экипируем броню
    print(f"\n🛡️  Экипируем броню {armor.display_name()}...")
    companion.equip_armor(armor)
    defense_after_armor = companion.defense
    print(f"   Защита ДО: {initial_defense}, ПОСЛЕ: {defense_after_armor}")
    
    if defense_after_armor > initial_defense:
        print(f"   ✅ УСПЕХ: Защита увеличилась на {defense_after_armor - initial_defense}")
    else:
        print(f"   ❌ ОШИБКА: Защита не увеличилась!")
        return False
    
    # Снимаем оружие
    print(f"\n🗡️  Снимаем оружие...")
    companion.unequip_weapon()
    damage_after_unequip = companion.damage
    print(f"   Урон ДО: {damage_after_weapon}, ПОСЛЕ: {damage_after_unequip}")
    
    if damage_after_unequip == initial_damage:
        print(f"   ✅ УСПЕХ: Урон вернулся к исходному значению")
    else:
        print(f"   ❌ ОШИБКА: Урон не вернулся! Ожидался {initial_damage}, получено {damage_after_unequip}")
        return False
    
    # Снимаем броню
    print(f"\n⚔️  Снимаем броню...")
    companion.unequip_armor()
    defense_after_unequip = companion.defense
    print(f"   Защита ДО: {defense_after_armor}, ПОСЛЕ: {defense_after_unequip}")
    
    if defense_after_unequip == initial_defense:
        print(f"   ✅ УСПЕХ: Защита вернулась к исходному значению")
    else:
        print(f"   ❌ ОШИБКА: Защита не вернулась! Ожидалось {initial_defense}, получено {defense_after_unequip}")
        return False
    
    print(f"\n" + "="*50)
    print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("="*50)
    return True


if __name__ == "__main__":
    success = test_companion_equip()
    sys.exit(0 if success else 1)
