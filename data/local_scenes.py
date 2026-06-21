#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Конфигурация локальных проходимых сцен (карты локаций, город, таверна, магазин).
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ui.ui_styles import BACKGROUNDS_DIR

# Боевые локации с проходимой картой
COMBAT_SCENES = frozenset({"forest", "swamp", "mines", "mountains"})

# Городские подлокации
CITY_SCENES = frozenset({"city", "tavern", "shop"})

ALL_LOCAL_SCENES = COMBAT_SCENES | CITY_SCENES

# Новые фоны (префикс bg_). Ключ — scene_id, значение — подпуть от BACKGROUNDS_DIR.
SCENE_BACKGROUND_FILES: Dict[str, Tuple[str, ...]] = {
    "forest": ("locations", "forest", "bg_forest.png"),
    "swamp": ("locations", "swamp", "bg_swamp.png"),
    "mines": ("locations", "mines", "bg_mines.png"),
    "mountains": ("locations", "mountains", "bg_mountains.png"),
    "city": ("locations", "town", "bg_town.png"),
    "tavern": ("locations", "tavern", "bg_tavern.png"),
    "shop": ("locations", "town", "bg_trading_area.png"),
}

_GLOBAL_MAP_CANDIDATES = [
    os.path.join(BACKGROUNDS_DIR, "global_map", "bg_Emberfall_global_map.jpg"),
    os.path.join(BACKGROUNDS_DIR, "global_map", "bg_Emberfall_global_map.jpeg"),
    os.path.join(BACKGROUNDS_DIR, "global_map", "bg_Emberfall_global_map.png"),
]


@dataclass
class BossSceneConfig:
    """Босс, привязанный к боевой локации."""

    boss_num: int
    enemy_id: str
    name: str
    x_norm: float = 0.78
    y_norm: float = 0.72


@dataclass
class ZoneConfig:
    """Зона перехода (дверь, вход)."""

    zone_id: str
    label: str
    target_scene: str
    x_norm: float
    y_norm: float
    radius_norm: float = 0.08


@dataclass
class NpcSpawnConfig:
    """NPC на проходимой карте."""

    npc_id: str
    name: str
    x_norm: float
    y_norm: float
    action: str = "dialogue"  # dialogue | shop | tavern_menu


@dataclass
class LocalSceneConfig:
    """Описание одной проходимой сцены."""

    scene_id: str
    title: str
    scene_type: str  # combat | city | tavern | shop
    exit_target: str  # location_select | parent
    enemy_count: int = 0
    enemy_location_id: Optional[str] = None
    player_scale: float = 0.8
    enemy_scale: float = 0.8
    boss_scale: float = 0.8
    npc_scale: float = 0.85
    camera_zoom: float = 1.3
    zones: List[ZoneConfig] = field(default_factory=list)
    npcs: List[NpcSpawnConfig] = field(default_factory=list)
    background_candidates: List[str] = field(default_factory=list)


# Боссы перенесены из Пещеры Древних в соответствующие локации
LOCATION_BOSSES: Dict[str, BossSceneConfig] = {
    "forest": BossSceneConfig(1, "enemy_ancient_cave_berserker", "Безумный мародёр", 0.72, 0.68),
    "swamp": BossSceneConfig(2, "enemy_ancient_cave_bog_master", "Хозяин Болота", 0.75, 0.70),
    "mines": BossSceneConfig(3, "enemy_ancient_cave_mine_king", "Король Шахт", 0.78, 0.65),
    "mountains": BossSceneConfig(
        4, "enemy_ancient_cave_dragon_lord", "Повелитель Драконов", 0.80, 0.72
    ),
}

SCENE_TITLES = {
    "forest": "🌲 Лес Криволесье",
    "swamp": "🏞️ Болота Гниющие Топи",
    "mines": "⛏️ Шахты Подскальные Гроты",
    "mountains": "⛰️ Горы Хребет Драконов",
    "city": "🏛️ Город",
    "tavern": "🏰 Таверна",
    "shop": "🛒 Магазин",
}


def scene_background_path(scene_id: str) -> Optional[str]:
    """Абсолютный путь к bg-файлу сцены, если он задан в SCENE_BACKGROUND_FILES."""
    parts = SCENE_BACKGROUND_FILES.get(scene_id)
    if not parts:
        return None
    return os.path.join(BACKGROUNDS_DIR, *parts)


def _bg_candidates(scene_id: str) -> List[str]:
    """Пути к фоновым изображениям сцены (первый существующий используется)."""
    path = scene_background_path(scene_id)
    return [path] if path else []


def resolve_background(scene_id: str) -> Optional[str]:
    """Найти существующий файл фона для сцены."""
    for path in _bg_candidates(scene_id):
        if path and os.path.isfile(path):
            return path
    return None


def resolve_global_map_background() -> Optional[str]:
    """Фон глобальной карты региона."""
    for path in _GLOBAL_MAP_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


def build_scene_config(scene_id: str) -> Optional[LocalSceneConfig]:
    """Собрать конфигурацию сцены по ID."""
    if scene_id not in ALL_LOCAL_SCENES:
        return None

    title = SCENE_TITLES.get(scene_id, scene_id)

    if scene_id in COMBAT_SCENES:
        return LocalSceneConfig(
            scene_id=scene_id,
            title=title,
            scene_type="combat",
            exit_target="location_select",
            enemy_count=10,
            enemy_location_id=scene_id,
            background_candidates=_bg_candidates(scene_id),
        )

    if scene_id == "city":
        return LocalSceneConfig(
            scene_id=scene_id,
            title=title,
            scene_type="city",
            exit_target="location_select",
            zones=[
                ZoneConfig("tavern_door", "Таверна", "tavern", 0.19, 0.22, 0.06),
                ZoneConfig("shop_door", "Торговый квартал", "shop", 0.79, 0.20, 0.2),
            ],
            background_candidates=_bg_candidates(scene_id),
        )

    if scene_id == "tavern":
        return LocalSceneConfig(
            scene_id=scene_id,
            title=title,
            scene_type="tavern",
            exit_target="parent",
            npcs=[
                NpcSpawnConfig("npc_captain", "Капитан Редард", 0.1, 0.41),
                NpcSpawnConfig("npc_tracker", "Болотный следопыт", 0.39, 0.53),
                NpcSpawnConfig("npc_miner", "Безумный шахтёр", 0.575, 0.48),
                NpcSpawnConfig("npc_collector", "Коллекционер", 0.74, 0.32),
                NpcSpawnConfig("npc_dragonslayer", "Драконоборец", 0.85, 0.40),
                NpcSpawnConfig("bartender", "Бармен", 0.34, 0.58, action="tavern_menu"),
            ],
            background_candidates=_bg_candidates(scene_id),
        )

    if scene_id == "shop":
        return LocalSceneConfig(
            scene_id=scene_id,
            title=title,
            scene_type="shop",
            exit_target="parent",
            npcs=[
                NpcSpawnConfig("shopkeeper", "Торговец", 0.52, 0.66, action="shop"),
            ],
            # Отдельного bg_shop пока нет — однотонная заливка на экране.
            background_candidates=_bg_candidates(scene_id),
        )

    return None


def enter_local_scene(app, scene_id: str, parent_scene: Optional[str] = None) -> bool:
    """
    Подготовить и открыть проходимую сцену.

    Returns:
        True, если переход выполнен.
    """
    screen = getattr(app, "local_location_screen", None)
    if not screen:
        return False
    mgr = getattr(screen, "manager", None)
    if not mgr:
        return False

    already_on_screen = mgr.current == "local_location"
    try:
        if already_on_screen:
            # Сохранить состояние текущей сцены до смены scene_id.
            screen.on_leave()
        screen.setup_scene(scene_id, parent_scene=parent_scene)
        if already_on_screen:
            # Kivy не вызывает on_enter при повторном выборе того же экрана.
            screen.on_enter()
        else:
            mgr.current = "local_location"
        return True
    except Exception:
        return False
