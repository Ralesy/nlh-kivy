#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
demo_new_systems.py - Демонстрация всех новых систем RPG.
"""

import sys
from creatures import Player
from items import ItemDatabase
from enemies import EnemyDatabase
from locations import LocationManager
from npcs import NPCManager


def demo_locations():
    """Демонстрация системы локаций."""
    print("\n" + "=" * 70)
    print("🗺️  ДЕМОНСТРАЦИЯ СИСТЕМЫ ЛОКАЦИЙ")
    print("=" * 70)

    loc_mgr = LocationManager()

    print("\n📍 Все доступные локации в игре:")
    for i, loc in enumerate(loc_mgr.get_all_locations(), 1):
        if loc.is_locked:
            print(f"\n{i}. 🔒 {loc.name}")
            print(f"   └─ Условие: {loc.unlock_description()}")
        else:
            print(f"\n{i}. 📍 {loc.name}")
            print(f"   Описание: {loc.description}")


def demo_npcs():
    """Демонстрация системы NPC."""
    print("\n" + "=" * 70)
    print("🧙 ДЕМОНСТРАЦИЯ СИСТЕМЫ NPC И КВЕСТОВ")
    print("=" * 70)

    npc_mgr = NPCManager()
    npcs_list = npc_mgr.get_available_npcs()

    for npc in npcs_list:
        print(f"\n{'='*70}")
        print(f"📋 {npc.get_introduction()}")
        print(f"{'='*70}")

        # Генерируем пример квеста
        quest = npc.generate_quest()
        print(f"\n📜 Пример квеста:")
        print(f"   Название: {quest.title}")
        print(f"   Описание: {quest.description}")
        print(f"   Цель: {quest.progress_display()}")
        print(f"   Награда: {quest.reward_gold} золота, {quest.reward_xp} опыта")


def demo_enemies():
    """Демонстрация системы врагов."""
    print("\n" + "=" * 70)
    print("👹 ДЕМОНСТРАЦИЯ СИСТЕМЫ ВРАГОВ")
    print("=" * 70)

    locations = [
        ("forest", "Лес"),
        ("swamp", "Болота"),
        ("mines", "Шахты"),
        ("mountains", "Горы")
    ]

    for loc_id, loc_name in locations:
        print(f"\n📍 {loc_name}:")
        enemies = EnemyDatabase.get_by_location(loc_id)
        for enemy in enemies[:3]:  # Показываем первых 3
            print(f"   • {enemy.name} (HP: {enemy.base_health}, "
                  f"DMG: {enemy.base_damage})")
        if len(enemies) > 3:
            print(f"   ... и ещё {len(enemies) - 3}")


def demo_items():
    """Демонстрация системы предметов."""
    print("\n" + "=" * 70)
    print("⚔️  ДЕМОНСТРАЦИЯ СИСТЕМЫ ПРЕДМЕТОВ И МАТЕРИАЛОВ")
    print("=" * 70)

    print("\n🔨 МАТЕРИАЛЫ ОРУЖИЯ:")
    materials = {
        "iron": "Железное",
        "steel": "Стальное",
        "goblin": "Гоблинское",
        "orc": "Орчье",
        "dwarf": "Гномье",
        "dragon": "Драконье"
    }
    for mat_id, mat_name in materials.items():
        weapons = ItemDatabase.find_by_material(mat_id, "weapon")
        if weapons:
            print(f"  {mat_name}: {len(weapons)} предмет(ов)")

    print("\n🛡️  МАТЕРИАЛЫ БРОНИ:")
    armor_materials = {
        "rags": "Трепьё",
        "leather": "Кожаная",
        "iron": "Железная",
        "steel": "Стальная",
        "orc": "Орчья",
        "dwarf": "Гномья"
    }
    for mat_id, mat_name in armor_materials.items():
        armors = ItemDatabase.find_by_material(mat_id, "armor")
        if armors:
            print(f"  {mat_name}: {len(armors)} предмет(ов)")

    print("\n✨ УНИКАЛЬНЫЕ ПРЕДМЕТЫ:")
    unique_items = [
        item for item in ItemDatabase.ITEMS.values()
        if item.is_unique
    ]
    for item in unique_items:
        print(f"  • {item.name} ({item.material if hasattr(item, 'material') else 'уникальное'})")


def demo_equipment_system():
    """Демонстрация системы экипировки с состояниями."""
    print("\n" + "=" * 70)
    print("🛠️  ДЕМОНСТРАЦИЯ СИСТЕМЫ СОСТОЯНИЙ ПРЕДМЕТОВ")
    print("=" * 70)

    player = Player("Герой Демо", "warrior")
    ItemDatabase.initialize()

    # Надеваем разное оружие в разных состояниях
    print("\n⚔️  ПРИМЕРЫ ОРУЖИЯ С СОСТОЯНИЯМИ:")

    weapons = [
        ItemDatabase.get("w_iron_sword"),
        ItemDatabase.get("w_steel_sword"),
        ItemDatabase.get("w_dragon_sword")
    ]

    for weapon in weapons:
        if weapon:
            player.equip_weapon(weapon)
            print(f"\n  Оружие: {weapon.display_name()}")
            print(f"  └─ Урон: {player.damage} (базовый урон оружия: "
                  f"{weapon.base_damage})")
            player.unequip_weapon()


def main():
    """Запуск демонстрации."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🎮 ДЕМОНСТРАЦИЯ ПОЛНОЙ ПЕРЕРАБОТКИ RPG".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Инициализируем базы данных
        ItemDatabase.initialize()
        EnemyDatabase.initialize()

        demo_locations()
        demo_npcs()
        demo_enemies()
        demo_items()
        demo_equipment_system()

        print("\n" + "=" * 70)
        print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("=" * 70)
        print("\n📖 Для полного тестирования запустите:")
        print("   python main.py --console")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
