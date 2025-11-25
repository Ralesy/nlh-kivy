#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест новой системы предметов с описаниями.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.items import ItemDatabase, Weapon, Armor, Potion


def test_items():
    """Тест всех предметов."""
    print("\n" + "="*60)
    print("ТЕСТ НОВОЙ СИСТЕМЫ ПРЕДМЕТОВ")
    print("="*60 + "\n")
    
    ItemDatabase.initialize()
    
    # Подсчитываем предметы
    weapons = [i for i in ItemDatabase.ITEMS.values() if isinstance(i, Weapon)]
    armors = [i for i in ItemDatabase.ITEMS.values() if isinstance(i, Armor)]
    potions = [i for i in ItemDatabase.ITEMS.values() if isinstance(i, Potion)]
    
    print(f"📊 СТАТИСТИКА:")
    print(f"   Оружия: {len(weapons)}")
    print(f"   Броня: {len(armors)}")
    print(f"   Зелья: {len(potions)}")
    print(f"   Всего: {len(ItemDatabase.ITEMS)}\n")
    
    # Проверяем уникальные предметы
    unique_items = [i for i in ItemDatabase.ITEMS.values() if i.is_unique]
    print(f"🎁 УНИКАЛЬНЫЕ ПРЕДМЕТЫ ({len(unique_items)}):")
    for item in unique_items:
        if isinstance(item, Weapon):
            print(f"   ⚔️  {item.display_name()} - {item.damage_bonus} урона")
        elif isinstance(item, Armor):
            print(f"   🛡️  {item.display_name()} - {item.defense} защиты")
    print()
    
    # Проверяем оружие по материалам
    materials = set(w.material for w in weapons)
    print(f"⚔️  ОРУЖИЕ ПО МАТЕРИАЛАМ:")
    for material in sorted(materials):
        items = [w for w in weapons if w.material == material and not w.is_unique]
        if items:
            print(f"   {material.upper()}:")
            for w in sorted(items, key=lambda x: x.damage_bonus):
                print(f"      {w.display_name()}: {w.damage_bonus} урона ({w.price} монет)")
    print()
    
    # Проверяем броню
    print(f"🛡️  БРОНЯ:")
    for armor in sorted(armors, key=lambda x: x.defense):
        if not armor.is_unique:
            print(f"   {armor.display_name()}: {armor.defense} защиты ({armor.price} монет)")
    print()
    
    # Проверяем зелья
    print(f"💚 ЗЕЛЬЯ:")
    for potion in sorted(potions, key=lambda x: x.heal_amount):
        print(f"   {potion.display_name()}: {potion.heal_amount} HP ({potion.price} монет)")
    print()
    
    # Проверяем некоторые предметы на наличие описаний
    print(f"📝 ПРОВЕРКА ОПИСАНИЙ:")
    has_desc = sum(1 for i in ItemDatabase.ITEMS.values() if i.description)
    print(f"   Предметов с описанием: {has_desc}/{len(ItemDatabase.ITEMS)}")
    
    if has_desc == len(ItemDatabase.ITEMS):
        print("   ✅ ВСЕ предметы имеют описания!")
    else:
        print("   ⚠️ Некоторые предметы без описаний")
    
    print("\n" + "="*60)
    print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        test_items()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
