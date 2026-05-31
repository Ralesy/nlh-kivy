#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты инвариантов доменного слоя: HP, монеты, инвентарь.
"""

import os
import sys

_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, ".."))
sys.path.insert(0, _proj_root)

from data.items import ItemDatabase, Potion
from core.models.creature import Creature
from core.models.inventory import Inventory
from core.models.player import Player


def test_health_clamped_on_creature():
    c = Creature("Test", 100, 10, 5)
    c.health = 999
    assert c.health == c.max_health
    c.health = -50
    assert c.health == 0


def test_coins_never_negative_on_creature():
    c = Creature("Test", 100, 10, 5)
    c.coins = 100
    c.coins = -20
    assert c.coins == 0


def test_take_damage_does_not_go_below_zero():
    c = Creature("Test", 50, 10, 5)
    c.take_damage(9999)
    assert c.health == 0
    assert not c.is_alive


def test_heal_respects_max_health():
    c = Creature("Test", 100, 10, 5)
    c.health = 50
    healed = c.heal(200)
    assert c.health == c.max_health
    assert healed == 50


def test_inventory_rejects_invalid_add():
    ItemDatabase.initialize()
    inv = Inventory(capacity=5)
    potion = ItemDatabase.get("p_small")
    assert inv.add(potion, 0) is False
    assert inv.add(None, 1) is False
    assert inv.add(potion, 6) is False
    assert inv.add(potion, 3) is True
    assert inv.add(potion, 2) is True
    assert inv.add(potion, 1) is False


def test_inventory_remove_prevents_overdraw():
    ItemDatabase.initialize()
    inv = Inventory(capacity=10)
    potion = ItemDatabase.get("p_small")
    inv.add(potion, 2)
    assert inv.remove("p_small", 0) is False
    assert inv.remove("p_small", 5) is False
    assert inv.qty("p_small") == 2
    assert inv.remove("p_small", 1) is True
    assert inv.qty("p_small") == 1


def test_player_coins_and_health_clamp():
    ItemDatabase.initialize()
    p = Player("Hero", "squire")

    p.coins = -10
    assert p.coins == 0

    p.health = p.max_health + 500
    assert p.health == p.max_health


def test_player_spend_coins():
    ItemDatabase.initialize()
    p = Player("Hero", "squire")
    p.coins = 100
    assert p.spend_coins(30) is True
    assert p.coins == 70
    assert p.spend_coins(100) is False
    assert p.coins == 70


def test_inventory_roundtrip():
    ItemDatabase.initialize()
    p = Player("Hero", "squire")
    potion = ItemDatabase.get("p_med")
    p.inventory.add(potion, 2)
    data = p.inventory.to_dict()
    restored = Inventory.from_dict(data)
    assert restored.qty("p_med") == 2
    assert restored.capacity == p.inventory.capacity
