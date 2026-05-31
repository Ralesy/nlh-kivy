#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Единая формула расчёта урона в бою.

Все атаки (игрок, враги, спутники) проходят через эти функции.
"""

import random
from typing import Tuple

from core.creatures import Creature


# Разброс урона по умолчанию
DEFAULT_VARIANCE = (-3, 5)
ENEMY_VARIANCE = (-2, 3)
MIN_DAMAGE = 1
DEFAULT_CRIT_MULTIPLIER = 2.0
DEFAULT_ENEMY_CRIT_CHANCE = 0.04


def roll_raw_damage(
    base_damage: int,
    variance: Tuple[int, int] = DEFAULT_VARIANCE,
    minimum: int = MIN_DAMAGE,
) -> int:
    """
    Сырой урон до защиты: база + случайный разброс, не ниже minimum.

    Args:
        base_damage: базовый урон атакующего.
        variance: пара (min_delta, max_delta) для random.randint.
        minimum: нижняя граница итогового значения.

    Returns:
        Целое значение сырого урона.
    """
    low, high = variance
    rolled = int(base_damage) + random.randint(low, high)
    return max(minimum, rolled)


def apply_critical(
    damage: int,
    crit_chance: float,
    multiplier: float = DEFAULT_CRIT_MULTIPLIER,
) -> Tuple[int, bool]:
    """
    Применить шанс критического удара.

    Returns:
        (итоговый урон, был ли крит).
    """
    chance = max(0.0, min(1.0, float(crit_chance)))
    is_critical = random.random() < chance
    if is_critical:
        return max(MIN_DAMAGE, int(damage * multiplier)), True
    return damage, False


def armor_ignore_bonus(target_defense: int, ignore_ratio: float) -> int:
    """
    Дополнительный урон от игнорирования брони (топоры и т.п.).

    Args:
        target_defense: защита цели.
        ignore_ratio: доля защиты, добавляемая к урону до вычета DEF.

    Returns:
        Добавочный урон.
    """
    if ignore_ratio <= 0:
        return 0
    return int(target_defense * ignore_ratio)


def resolve_hit(attacker_damage: int, target: Creature) -> int:
    """
    Применить урон к цели через take_damage (учитывает DEF цели).

    Returns:
        Фактически нанесённый урон.
    """
    return target.take_damage(attacker_damage)


def player_crit_chance(player) -> float:
    """Шанс крита игрока с учётом оружия."""
    base = getattr(player, "critical_chance", DEFAULT_ENEMY_CRIT_CHANCE)
    weapon = getattr(player, "weapon", None)
    if weapon and hasattr(weapon, "ability") and weapon.ability:
        ability = weapon.ability
        if getattr(ability, "crit_multiplier", None):
            return min(1.0, base * ability.crit_multiplier)
    return base
