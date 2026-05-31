#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Обратная совместимость: re-export из core.combat.

Новый код должен импортировать из core.combat напрямую.
"""

from core.combat.battlefield import Battlefield
from core.combat.enemy_spawner import EnemyGenerator
from core.combat.events import EventSystem
from core.combat.loot import BattleResult, LootDrop

__all__ = [
    "Battlefield",
    "EnemyGenerator",
    "EventSystem",
    "BattleResult",
    "LootDrop",
]
