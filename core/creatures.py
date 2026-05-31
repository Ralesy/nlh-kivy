#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Обратная совместимость: re-export доменных моделей из core.models.

Новый код должен импортировать из core.models напрямую.
"""

from core.models.companion import Companion
from core.models.creature import Creature
from core.models.inventory import Inventory
from core.models.player import Player, TestPlayer

__all__ = [
    "Creature",
    "Companion",
    "Player",
    "TestPlayer",
    "Inventory",
]
