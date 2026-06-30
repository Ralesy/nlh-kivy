#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Конфигурация боссов для глобальной карты.
Каждый босс — roaming-токен со своими координатами появления,
радиусом блуждания, enemy_id для генерации существа и уровнем.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class BossRoamConfig:
    """Конфигурация босса на глобальной карте."""

    boss_num: int
    name: str
    enemy_id: str
    location_id: str  # id локации для соответствия зоне (forest, swamp, mines, mountains)
    center_norm_x: float  # центр зоны патрулирования (норм. 0..1)
    center_norm_y: float
    roam_radius_norm: float = 0.05  # радиус зоны патрулирования
    level: int = 1
    color: Tuple[float, float, float] = (0.85, 0.2, 0.05)  # ярко-красный
    token_size: float = 14.0  # размер маркера на карте


# Все боссы в порядке цепочки
BOSS_ROAM_CONFIGS: list[BossRoamConfig] = [
    BossRoamConfig(
        boss_num=1,
        name="Безумный мародёр",
        enemy_id="enemy_ancient_cave_berserker",
        location_id="forest",
        center_norm_x=0.18, center_norm_y=0.45,
        roam_radius_norm=0.06,
        level=3,
        color=(0.85, 0.2, 0.05),
        token_size=14.0,
    ),
    BossRoamConfig(
        boss_num=2,
        name="Хозяин Болота",
        enemy_id="enemy_ancient_cave_bog_master",
        location_id="swamp",
        center_norm_x=0.50, center_norm_y=0.60,
        roam_radius_norm=0.06,
        level=5,
        color=(0.2, 0.6, 0.1),
        token_size=14.0,
    ),
    BossRoamConfig(
        boss_num=3,
        name="Король Шахт",
        enemy_id="enemy_ancient_cave_mine_king",
        location_id="mines",
        center_norm_x=0.70, center_norm_y=0.20,
        roam_radius_norm=0.06,
        level=8,
        color=(0.7, 0.5, 0.1),
        token_size=14.0,
    ),
    BossRoamConfig(
        boss_num=4,
        name="Повелитель Драконов",
        enemy_id="enemy_ancient_cave_dragon_lord",
        location_id="mountains",
        center_norm_x=0.70, center_norm_y=0.90,
        roam_radius_norm=0.06,
        level=12,
        color=(0.9, 0.3, 0.1),
        token_size=16.0,
    ),
]


def get_boss_config(boss_num: int) -> BossRoamConfig | None:
    """Получить конфигурацию босса по номеру."""
    for cfg in BOSS_ROAM_CONFIGS:
        if cfg.boss_num == boss_num:
            return cfg
    return None