#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Тесты GameSession: создание, бой, сохранение, поражение."""

import os
import sys
import tempfile

_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, ".."))
sys.path.insert(0, _proj_root)

from core.session import GameSession
from core.creatures import Creature
from data.items import ItemDatabase


def test_start_new_game():
    session = GameSession()
    player = session.start_new_game("Hero", "squire")
    assert session.has_player
    assert player.name == "Hero"
    assert session.day == 1


def test_create_battle_advances_day():
    session = GameSession()
    session.start_new_game("Hero", "squire")
    enemy = Creature("Goblin", 30, 5, 10)
    battlefield, service = session.create_battle([enemy])
    assert session.day == 2
    assert session.player.battles_fought == 1
    assert battlefield is not None
    assert service is not None


def test_save_and_load_roundtrip():
    session = GameSession()
    session.start_new_game("Saver", "hunter")
    session.day = 7
    session.player.coins = 333

    with tempfile.TemporaryDirectory() as tmp:
        from systems import save_system
        old_dir = save_system.SAVES_DIR
        save_system.SAVES_DIR = __import__("pathlib").Path(tmp) / "saves"
        try:
            assert session.save_to_file("test_slot") is True
            loaded = GameSession()
            assert loaded.load_from_file("test_slot") is True
            assert loaded.player.name == "Saver"
            assert loaded.day == 7
            assert loaded.player.coins == 333
        finally:
            save_system.SAVES_DIR = old_dir


def test_death_penalty_clamps_gold_and_restores_hp():
    ItemDatabase.initialize()
    session = GameSession()
    session.start_new_game("Hero", "squire")
    session.player.coins = 100
    session.player.health = 0

    result = session.apply_death_penalty()
    assert result.gold_lost == 10
    assert session.player.coins == 90
    assert session.player.health >= 1
    assert result.message
