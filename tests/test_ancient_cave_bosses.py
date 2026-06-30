#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test for Ancient Cave boss selection screen.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь Python
sys.path.insert(0, str(Path(__file__).parent))

from data.locations import LocationManager
from systems.battle import EnemyGenerator


def test_boss_unlock_conditions():
    """Test that bosses unlock with correct conditions."""
    lm = LocationManager()
    
    # Boss 1 should be available immediately
    assert lm.is_boss_unlocked(1), "Boss 1 should always be unlocked"
    print("✓ Boss 1 (Безумный мародёр) always available")
    
    # Следующие боссы открываются после победы над предыдущим
    assert not lm.is_boss_unlocked(2), "Boss 2 should be locked"
    assert not lm.is_boss_unlocked(3), "Boss 3 should be locked"
    assert not lm.is_boss_unlocked(4), "Boss 4 should be locked"

    lm.mark_boss_defeated(1)
    assert lm.is_boss_unlocked(2), "Boss 2 unlocks after boss 1 defeated"

    lm.mark_boss_defeated(2)
    assert lm.is_boss_unlocked(3), "Boss 3 unlocks after boss 2 defeated"

    lm.mark_boss_defeated(3)
    assert lm.is_boss_unlocked(4), "Boss 4 unlocks after boss 3 defeated"


def test_boss_generation():
    """Test that all bosses can be generated."""
    from data.enemies import EnemyDatabase
    
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
    print("\n[Да] All Ancient Cave boss tests passed!")
