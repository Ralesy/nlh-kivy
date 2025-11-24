#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for Ancient Cave location and bosses.
"""

from locations import LocationManager
from enemies import EnemyDatabase
from items import ItemDatabase
from battle import EnemyGenerator


def test_ancient_cave_location():
    """Test that Ancient Cave location exists and is accessible."""
    location_manager = LocationManager()
    ancient_cave = location_manager.get_location("ancient_cave")
    
    assert ancient_cave is not None, "Ancient Cave location not found"
    assert ancient_cave.name == "🏰 Пещера Древних", "Ancient Cave name mismatch"
    assert not ancient_cave.is_locked, "Ancient Cave should not be locked"
    print("✓ Ancient Cave location exists and is accessible")


def test_ancient_cave_bosses():
    """Test that all 4 bosses are available in Ancient Cave."""
    EnemyDatabase.initialize()
    enemies = EnemyDatabase.get_by_location("ancient_cave")
    
    assert len(enemies) == 4, f"Expected 4 bosses, got {len(enemies)}"
    
    boss_names = [e.name for e in enemies]
    expected_names = [
        "Безумный мародёр",
        "Хозяин Болота",
        "Король Шахт",
        "Повелитель Драконов"
    ]
    
    for expected in expected_names:
        assert expected in boss_names, f"Boss '{expected}' not found"
    
    print("✓ All 4 bosses registered for Ancient Cave")


def test_boss_drops():
    """Test that all bosses have proper loot drops."""
    EnemyDatabase.initialize()
    ItemDatabase.initialize()
    enemies = EnemyDatabase.get_by_location("ancient_cave")
    
    expected_drops = {
        "Безумный мародёр": "a_berserker_plate",
        "Хозяин Болота": "a_bog_mail",
        "Король Шахт": "w_mining_king_pickaxe",
        "Повелитель Драконов": "a_dragon_lord_plate"
    }
    
    for enemy in enemies:
        expected_item = expected_drops.get(enemy.name)
        assert expected_item is not None, f"No expected drop for {enemy.name}"
        
        assert expected_item in [item[0] for item in enemy.loot_table], \
            f"Boss {enemy.name} missing drop {expected_item}"
        
        item = ItemDatabase.get(expected_item)
        assert item is not None, f"Drop item {expected_item} not registered"
    
    print("✓ All bosses have proper unique loot drops")


def test_enemy_generator():
    """Test that EnemyGenerator can create enemies for Ancient Cave."""
    EnemyDatabase.initialize()
    
    enemies = EnemyGenerator.generate_for_location("ancient_cave", 5, 1)
    
    assert len(enemies) > 0, "No enemies generated for Ancient Cave"
    print(f"✓ EnemyGenerator created {len(enemies)} boss(es) for Ancient Cave")


if __name__ == "__main__":
    test_ancient_cave_location()
    test_ancient_cave_bosses()
    test_boss_drops()
    test_enemy_generator()
    print("\n✅ All Ancient Cave tests passed!")
