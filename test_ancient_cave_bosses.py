#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for Ancient Cave boss selection screen.
"""

from locations import LocationManager
from battle import EnemyGenerator


def test_boss_unlock_conditions():
    """Test that bosses unlock with correct conditions."""
    lm = LocationManager()
    
    # Boss 1 should be available immediately
    assert lm.is_boss_unlocked(1), "Boss 1 should always be unlocked"
    print("✓ Boss 1 (Безумный мародёр) always available")
    
    # Boss 2 should be locked initially
    assert not lm.is_boss_unlocked(2), "Boss 2 should be locked"
    print("✓ Boss 2 (Хозяин Болота) locked until Swamp opens")
    
    # Boss 3 should be locked initially
    assert not lm.is_boss_unlocked(3), "Boss 3 should be locked"
    print("✓ Boss 3 (Король Шахт) locked until Mines open")
    
    # Boss 4 should be locked initially
    assert not lm.is_boss_unlocked(4), "Boss 4 should be locked"
    print("✓ Boss 4 (Повелитель Драконов) locked until Mountains open")
    
    # Simulate unlocking swamp and check boss 2
    lm.unlock_location("swamp")
    assert lm.is_boss_unlocked(2), "Boss 2 should unlock with swamp"
    print("✓ Boss 2 unlocks when Swamp is unlocked")
    
    # Simulate unlocking mines and check boss 3
    lm.unlock_location("mines")
    assert lm.is_boss_unlocked(3), "Boss 3 should unlock with mines"
    print("✓ Boss 3 unlocks when Mines are unlocked")
    
    # Simulate unlocking mountains and check boss 4
    lm.unlock_location("mountains")
    assert lm.is_boss_unlocked(4), "Boss 4 should unlock with mountains"
    print("✓ Boss 4 unlocks when Mountains are unlocked")


def test_boss_generation():
    """Test that all bosses can be generated."""
    from enemies import EnemyDatabase
    
    EnemyDatabase.initialize()
    
    boss_ids = {
        1: "enemy_ancient_cave_berserker",
        2: "enemy_ancient_cave_bog_master",
        3: "enemy_ancient_cave_mine_king",
        4: "enemy_ancient_cave_dragon_lord"
    }
    
    for bid, enemy_id in boss_ids.items():
        boss = EnemyGenerator.generate_boss(enemy_id)
        assert boss is not None, f"Failed to generate boss {bid}"
        assert boss.is_alive, f"Boss {bid} not alive"
        print(f"✓ Boss {bid} ({boss.name}) generated successfully")


if __name__ == "__main__":
    test_boss_unlock_conditions()
    test_boss_generation()
    print("\n✅ All Ancient Cave boss tests passed!")
