#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_battle_system.py - Тест боевой системы с новой системой врагов и дропа.
"""

import sys
from creatures import Player
from items import ItemDatabase
from battle import Battlefield, EnemyGenerator
from enemies import EnemyDatabase
from locations import LocationManager


def test_enemy_generation():
    """Тест генерации врагов."""
    print("=" * 60)
    print("ТЕСТ 1: Генерация врагов по локациям")
    print("=" * 60)

    EnemyDatabase.initialize()
    LocationManager()

    locations = ["forest", "swamp", "mines", "mountains"]

    for location in locations:
        print(f"\n{location.upper()}:")
        enemies = EnemyGenerator.generate_for_location(
            location, player_level=1, count=2
        )
        for enemy in enemies:
            print(f"  - {enemy.name} "
                  f"(HP: {enemy.health}, DMG: {enemy.damage})")

    print("\n✅ Враги генерируются успешно!")


def test_loot_generation():
    """Тест генерации лута."""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Генерация лута")
    print("=" * 60)

    EnemyDatabase.initialize()
    ItemDatabase.initialize()

    # Создаём врагов разных типов
    player = Player("Тестовый Герой", "warrior")
    player.coins = 1000

    # Тест с гуманоидом
    enemies = EnemyGenerator.generate_for_location("forest", 1, 1)
    print(f"\nГенерируем лут с {enemies[0].name}:")
    battlefield = Battlefield(player, enemies)
    result = battlefield.generate_battle_loot()

    print(f"Золото: {result.gold_earned}")
    print(f"Опыт: {result.xp_earned}")
    print(f"Лут ({len(result.loot)} предметов):")
    for loot in result.loot:
        print(f"  - {loot.display()}")

    print("\n✅ Лут генерируется успешно!")


def test_locations():
    """Тест системы локаций."""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Система локаций")
    print("=" * 60)

    location_manager = LocationManager()

    print("\nВсе локации:")
    for loc in location_manager.get_all_locations():
        status = "🔒 ЗАКРЫТА" if loc.is_locked else "📍 ОТКРЫТА"
        print(f"  {status} - {loc.name}")
        if loc.is_locked:
            print(f"    Условие: {loc.unlock_description()}")

    print("\nТест разблокировки локаций:")
    location_manager.increment_quest_counter("forest")
    location_manager.increment_quest_counter("forest")
    location_manager.increment_quest_counter("forest")

    unlocked = location_manager.check_and_unlock_locations()
    if unlocked:
        print(f"Разблокированы: {unlocked}")
    else:
        print("Локации не разблокированы (нужно больше квестов)")

    print("\n✅ Система локаций работает!")


def test_items():
    """Тест системы предметов."""
    print("\n" + "=" * 60)
    print("ТЕСТ 4: Система предметов с материалами и состояниями")
    print("=" * 60)

    ItemDatabase.initialize()

    print("\nОружие разных материалов:")
    materials = ["iron", "steel", "goblin", "orc", "dwarf", "dragon"]
    for material in materials:
        weapons = ItemDatabase.find_by_material(material, "weapon")
        if weapons:
            weapon = weapons[0]
            print(f"  {weapon.name}")
            print(f"    Урон: {weapon.damage_bonus} "
                  f"(материал: {weapon.material})")
            print(f"    Состояние: {weapon.condition_display}")

    print("\nПроверка уникальных предметов:")
    unique_items = [
        item for item in ItemDatabase.ITEMS.values()
        if item.is_unique
    ]
    for item in unique_items:
        print(f"  ✨ {item.display_name()} (цена: {item.price})")

    print("\n✅ Система предметов работает!")


def main():
    """Запуск всех тестов."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🧪 ТЕСТИРОВАНИЕ НОВОЙ БОЕВОЙ СИСТЕМЫ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        test_items()
        test_enemy_generation()
        test_loot_generation()
        test_locations()

        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
