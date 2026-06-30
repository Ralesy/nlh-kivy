#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Конфигурация локальных проходимых сцен (только город).
Боевые локации удалены — боссы перемещены на глобальную карту как roaming-сущности.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ui.ui_styles import BACKGROUNDS_DIR

# Только город (NPC перенесены в город)
CITY_SCENES = frozenset({"city"})

# Фоны локаций (город + для засад на глобальной карте)
SCENE_BACKGROUND_FILES: Dict[str, Tuple[str, ...]] = {
    "forest": ("locations", "forest", "bg_forest.png"),
    "swamp": ("locations", "swamp", "bg_swamp.png"),
    "mines": ("locations", "mines", "bg_mines.png"),
    "mountains": ("locations", "mountains", "bg_mountains.png"),
    "city": ("locations", "town", "bg_town.png"),
}

_GLOBAL_MAP_CANDIDATES = [
    os.path.join(BACKGROUNDS_DIR, "global_map", "bg_Emberfall_global_map.jpg"),
    os.path.join(BACKGROUNDS_DIR, "global_map", "bg_Emberfall_global_map.jpeg"),
    os.path.join(BACKGROUNDS_DIR, "global_map", "bg_Emberfall_global_map.png"),
]


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
    scene_type: str  # city | tavern | shop
    exit_target: str  # location_select | parent
    player_scale: float = 0.7
    enemy_scale: float = 0.7
    npc_scale: float = 0.7
    camera_zoom: float = 1.3
    zones: List[ZoneConfig] = field(default_factory=list)
    npcs: List[NpcSpawnConfig] = field(default_factory=list)
    background_candidates: List[str] = field(default_factory=list)


SCENE_TITLES = {
    "city": "[Город] Город",
    "tavern": "[Таверна] Таверна",
    "shop": "[Магазин] Магазин",
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
    if scene_id not in CITY_SCENES:
        return None

    title = SCENE_TITLES.get(scene_id, scene_id)

    if scene_id == "city":
        return LocalSceneConfig(
            scene_id=scene_id,
            title=title,
            scene_type="city",
            exit_target="location_select",
            npcs=[
                # NPC из бывшей таверны
                NpcSpawnConfig("npc_captain", "Капитан Редард", 0.10, 0.62),
                NpcSpawnConfig("npc_tracker", "Болотный следопыт", 0.28, 0.44),
                NpcSpawnConfig("npc_miner", "Безумный шахтёр", 0.42, 0.58),
                NpcSpawnConfig("npc_collector", "Коллекционер", 0.62, 0.36),
                NpcSpawnConfig("npc_dragonslayer", "Драконоборец", 0.80, 0.52),
                NpcSpawnConfig("bartender", "Бармен", 0.22, 0.75, action="tavern_menu"),
                # NPC из бывшего магазина
                NpcSpawnConfig("shopkeeper", "Торговец", 0.72, 0.72, action="shop"),
            ],
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