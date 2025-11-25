#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core module - основная логика существ и персонажей.

Re-exports из creatures.py для удобства импорта из папки core.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.creatures import Creature, Player  # noqa: F401, E402

__all__ = ["Creature", "Player"]
