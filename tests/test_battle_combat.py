#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты боевой системы: выбор цели, урон, лут.
"""

import os
import sys

_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, ".."))
sys.path.insert(0, _proj_root)

from core.combat.battle_service import BattleService
from core.combat.battlefield import Battlefield
from core.combat.damage import roll_raw_damage, apply_critical
from core.creatures import Creature, Player
from data.items import ItemDatabase


def _make_battle(enemy_count=2):
    ItemDatabase.initialize()
    player = Player("Hero", "squire")
    enemies = [
        Creature(f"Goblin{i}", 30, 5, 10, level=1)
        for i in range(enemy_count)
    ]
    return BattleService(Battlefield(player, enemies))


def test_player_attack_targets_selected_enemy():
    service = _make_battle(2)
    first_name = service.battlefield.alive_enemies()[0].name
    second = service.battlefield.alive_enemies()[1]
    second.health = 1

    log, killed = service.player_attack_enemy(1)
    assert second.name in log
    assert killed is True
    assert service.battlefield.alive_enemies()[0].name == first_name


def test_invalid_enemy_index_returns_error():
    service = _make_battle(1)
    log, killed = service.player_attack_enemy(5)
    assert "Неверная" in log
    assert killed is False


def test_damage_roll_minimum():
    for _ in range(20):
        value = roll_raw_damage(10, variance=(-100, -50))
        assert value >= 1


def test_generate_loot_from_dead_enemies_only():
    ItemDatabase.initialize()
    player = Player("Hero", "squire")
    enemy = Creature("LootMob", 20, 3, 25, level=2)
    enemy.health = 0
    enemy._template = None
    battlefield = Battlefield(player, [enemy])

    result = battlefield.generate_battle_loot()
    assert result.gold_earned > 0
    assert result.xp_earned > 0


def test_enemy_phase_includes_companion_attack():
    ItemDatabase.initialize()
    player = Player("Hero", "squire")
    from core.models.companion import Companion

    player.companions.append(Companion("Archer", "archer", 1))
    enemy = Creature("Target", 500, 1, 1, level=1)
    service = BattleService(Battlefield(player, [enemy]))

    logs = service.run_enemy_phase()
    assert any("Archer" in line for line in logs)


def test_surrender_kills_player():
    service = _make_battle(1)
    msg, dead = service.surrender()
    assert dead is True
    assert service.battlefield.player.health == 0
    assert "сдался" in msg.lower()
