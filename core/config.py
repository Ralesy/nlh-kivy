#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Config - центральные конфигурационные константы и типы.

Содержит:
- Константы игры (размеры экранов, цвета и т.д.)
- Типы данных (ItemRarity, LocationDifficulty и т.д.)
- Пути к ресурсам
"""

from enum import Enum
from pathlib import Path

# ============================================================================
# ПУТИ
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
SAVES_DIR = PROJECT_ROOT / "saves"
DOCS_DIR = PROJECT_ROOT / "docs"

# ============================================================================
# ПЕРЕЧИСЛЕНИЯ (ENUMS)
# ============================================================================


class ItemRarity(str, Enum):
    """Редкость предметов."""
    COMMON = "ОБЫЧНЫЙ"
    RARE = "РЕДКИЙ"
    LEGENDARY = "ЛЕГЕНДАРНЫЙ"
    UNIQUE = "УНИКАЛЬНАЯ"


class ItemType(str, Enum):
    """Тип предмета."""
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    MISC = "misc"


class LocationDifficulty(str, Enum):
    """Сложность локации."""
    EASY = "Легко"
    MEDIUM = "Средне"
    HARD = "Сложно"
    VERY_HARD = "Очень сложно"
    LEGENDARY = "Легендарно"


class CharacterClass(str, Enum):
    """Класс персонажа."""
    WARRIOR = "warrior"
    ROGUE = "rogue"
    MAGE = "mage"
    PALADIN = "paladin"


# ============================================================================
# ИГРОВЫЕ КОНСТАНТЫ
# ============================================================================

# Масштабирование характеристик
STAT_SCALE_FACTOR = 0.12

# Система опыта
BASE_EXPERIENCE_PER_LEVEL = 100
EXPERIENCE_MULTIPLIER_PER_LEVEL = 1.0

# Боевая система
MIN_DAMAGE_MULTIPLIER = 0.8
MAX_DAMAGE_MULTIPLIER = 1.2
DODGE_CHANCE_BASE = 0.05

# Инвентарь
INVENTORY_MAX_SLOTS = 20
EQUIPMENT_SLOTS = {
    "weapon": 1,
    "armor": 1,
}

# ============================================================================
# UI КОНСТАНТЫ
# ============================================================================

# Размеры
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Цвета (RGBA)
COLOR_BACKGROUND = (0.15, 0.2, 0.25, 1)
COLOR_PRIMARY = (0.9, 0.7, 0.1, 1)
COLOR_SUCCESS = (0.2, 0.5, 0.2, 1)
COLOR_DANGER = (0.5, 0.2, 0.2, 1)
COLOR_NEUTRAL = (0.4, 0.4, 0.4, 1)
COLOR_MUTED = (0.3, 0.3, 0.3, 1)

# Шрифты
FONT_SIZE_TITLE = 24
FONT_SIZE_SUBTITLE = 18
FONT_SIZE_BODY = 14
FONT_SIZE_SMALL = 12

# ============================================================================
# ЛОКАЦИИ
# ============================================================================

LOCATION_UNLOCK_CONDITIONS = {
    "forest": {
        "difficulty": LocationDifficulty.EASY,
        "quests_to_unlock_next": 3,
    },
    "swamp": {
        "difficulty": LocationDifficulty.MEDIUM,
        "quests_to_unlock_next": 4,
        "unlocked_after": "forest",
    },
    "mines": {
        "difficulty": LocationDifficulty.HARD,
        "quests_to_unlock_next": 3,
        "unlocked_after": "swamp",
    },
    "mountains": {
        "difficulty": LocationDifficulty.VERY_HARD,
        "unlocked_after": "boss_3",
    },
    "ancient_cave": {
        "difficulty": LocationDifficulty.LEGENDARY,
        "always_available": True,
    },
}

# ============================================================================
# БОССЫ
# ============================================================================

BOSS_UNLOCK_CONDITIONS = {
    1: {
        "name": "Безумный мародёр",
        "always_available": True,
        "drop_item": "a_berserker_plate",
    },
    2: {
        "name": "Хозяин Болота",
        "requires_location": "swamp",
        "drop_item": "a_bog_mail",
    },
    3: {
        "name": "Король Шахт",
        "requires_location": "mines",
        "drop_item": "w_mining_king_pickaxe",
        "unlocks_location": "mountains",
    },
    4: {
        "name": "Повелитель Драконов",
        "requires_location": "mountains",
        "drop_item": "a_dragon_lord_plate",
        "is_final_boss": True,
    },
}

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

DEBUG_MODE = False
LOG_LEVEL = "INFO"


# ============================================================================
# НАСТРОЙКИ ЛОКАЛЬНЫХ СЦЕН (СИСТЕМЫ ИИ, РАДИУСЫ, СТЕЛС)
# ============================================================================
SOCIAL_AGGRO_RADIUS = 120
DE_AGGRO_RADIUS = 250
PATROL_RADIUS = 150
CONE_ANGLE = 120
CONE_LENGTH = 200
HEARING_RADIUS = 95
PLAYER_BASE_RADIUS = 12
ENEMY_BASE_RADIUS = 12
BOSS_BASE_RADIUS = 18
NPC_BASE_RADIUS = 14
LOCAL_CAMERA_ZOOM = 1.3
LOCAL_CAMERA_LERP_SPEED = 8.0
ENTRY_POINT_X = 0.5
ENTRY_POINT_Y = 0.1
STUN_DURATION = 5.0
INVINCIBILITY_DURATION = 3.0

LOCAL_ENEMY_PATROL_SPEED = 20  # Число для dp()
LOCAL_ENEMY_CHASE_SPEED = 170  # Число для dp()

# ============================================================================
# НАСТРОЙКИ ГЛОБАЛЬНОЙ КАРТЫ (КАМЕРА И ДВИЖЕНИЕ)
# ============================================================================
GLOBAL_CAMERA_ZOOM = 2.5
GLOBAL_CAMERA_LERP_SPEED = 6.0
GLOBAL_MAP_SPEED_MULTIPLIER = 0.4
GLOBAL_PLAYER_MARKER_SIZE = 14  # Число для dp()
GLOBAL_PLAYER_MOVE_SPEED = 147  # Число для dp()


# ============================================================================
# РЕПЛИКИ СУЩЕСТВ (BARK SYSTEM)
# ============================================================================
ENEMY_BARKS = {
    "marauder": [
        "Ненавижу службу, хорошо, что сбежал.",
        "Опять эта похлебка из топора...",
        "Главное — чтобы босс не заметил, что я сплю.",
        "Кто-нибудь видел мою флягу?"
    ],
    "bandit": [
        "Вот бы ограбить караван...",
        "Эй, у тебя есть закурить?",
        "Если найду золото, сразу свалю в город.",
        "Тихо ты! Кажется, шорох был..."
    ],
    "wolf": [
        "Гав, ой... Ауууууууууууу!",
        "Ррррр...",
        "Хрусть... (грызет какую-то кость)",
        "Тяв!"
    ]
}

BARK_CHANCE_PER_CHECK = 0.5    # Шанс (7%), что враг заговорит при проверке
BARK_CHECK_INTERVAL = 3.0       # Как часто (в секундах) проверяется шанс
BARK_DURATION = 3.5             # Сколько секунд реплика висит над головой

# ============================================================================
# РЕПЛИКИ ТРЕВОГИ (ПРИ ОБНАРУЖЕНИИ ИГРОКА)
# ============================================================================
ENEMY_ALERT_BARKS = {
    "marauder": [
        "Стоять! Кто идет?!",
        "Ага, попался, шпион!",
        "Оружие к бою, у нас гость!",
        "Чужак в лагере! Хватай его!"
    ],
    "bandit": [
        "Опа, жирненький идет!",
        "Кошелек или жизнь!",
        "Парни, шухер! Тут кто-то есть!",
        "Стой, бить буду!"
    ],
    "wolf": [
        "Рррррааавр!",
        "Вуф! (злобно рычит)",
        "Аууууу! (бросается в атаку)"
    ]
}