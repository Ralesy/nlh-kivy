#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Обратная совместимость: BattleService перенесён в core.combat.
"""

from core.combat.battle_service import BattleService

__all__ = ["BattleService"]
