#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
core.combat — боевая логика без зависимостей от Kivy.
"""

from core.combat.battlefield import Battlefield
from core.combat.battle_service import BattleService
from core.combat.enemy_spawner import EnemyGenerator
from core.combat.events import EventSystem
from core.combat.loot import BattleResult, LootDrop

__all__ = [
    "Battlefield",
    "BattleService",
    "EnemyGenerator",
    "EventSystem",
    "BattleResult",
    "LootDrop",
]
