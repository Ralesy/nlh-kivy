#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locations: система локаций с блокировками и условиями открытия.
"""

from typing import List, Optional, Dict
from enum import Enum


class LocationStatus(Enum):
    """Статус локации."""
    LOCKED = "locked"
    AVAILABLE = "available"
    DISCOVERED = "discovered"


class Location:
    """Описание локации."""

    def __init__(
        self,
        id_: str,
        name: str,
        description: str,
        difficulty: int = 1,
        is_locked: bool = False,
        unlock_condition: Optional[str] = None,
        enemy_types: Optional[List[str]] = None
    ):
        self.id = id_
        self.name = name
        self.description = description
        self.difficulty = difficulty  # Относительная сложность
        self.is_locked = is_locked
        self.unlock_condition = unlock_condition  # Условие разблокировки
        self.visited = False
        self.enemy_types = enemy_types or []  # Типы врагов в локации

    def display_status(self) -> str:
        """Отображение статуса локации."""
        if self.is_locked:
            return f"🔒 {self.name}"
        elif self.visited:
            return f"✅ {self.name}"
        else:
            return f"📍 {self.name}"

    def unlock_description(self) -> str:
        """Описание условия разблокировки."""
        if not self.is_locked:
            return "Открыта"
        return self.unlock_condition or "Неизвестное условие"


class LocationManager:
    """Менеджер локаций с системой разблокировок."""

    def __init__(self):
        """Инициализация менеджера локаций."""
        self.locations: Dict[str, Location] = {}
        self._quest_counters: Dict[str, int] = {
            "forest_quests": 0,
            "swamp_quests": 0,
            "mines_quests": 0,
            "mountains_quests": 0,
            "boss_1_defeated": False,
            "boss_2_defeated": False,
            "boss_3_defeated": False,
            "boss_4_defeated": False
        }
        self._initialize_locations()

    def _initialize_locations(self) -> None:
        """Инициализация всех локаций."""
        # 1. ЛЕС "КРИВОЛЕСЬЕ" - открыт сразу
        self.locations["forest"] = Location(
            "forest",
            "🌲 Лес Криволесье",
            "Густой лес полный дикобразов и мародёров",
            difficulty=1,
            is_locked=False,
            enemy_types=[
                "enemy_forest_wolf",
                "enemy_forest_raider",
                "enemy_forest_bandit",
                "enemy_forest_scout"
            ]
        )

        # 2. БОЛОТА "ГНИЮЩИЕ ТОПИ" - открыть после 3 квестов из леса
        self.locations["swamp"] = Location(
            "swamp",
            "🏞️ Болота Гниющие Топи",
            "Топкое болото полное гоблинов и гигантских жаб",
            difficulty=2,
            is_locked=True,
            unlock_condition="Победите первого босса (Безумный мародёр)",
            enemy_types=[
                "enemy_swamp_goblin",
                "enemy_swamp_toad",
                "enemy_swamp_shamanic"
            ]
        )

        # 3. ШАХТЫ "ПОДСКАЛЬНЫЕ ГРОТЫ" - после 4 квестов в болотах
        self.locations["mines"] = Location(
            "mines",
            "⛏️ Шахты Подскальные Гроты",
            "Тёмные подземные шахты с орками и гномами-драуграми",
            difficulty=3,
            is_locked=True,
            unlock_condition="Победите босса Хозяин Болота (второй босс)",
            enemy_types=[
                "enemy_mines_orc",
                "enemy_mines_draugr",
                "enemy_mines_golem",
                "enemy_mines_skeleton",
                "enemy_mines_greyling"
            ]
        )

        # 4. ГОРЫ "ХРЕБЕТ ДРАКОНОВ" - после победы над боссом шахт
        self.locations["mountains"] = Location(
            "mountains",
            "⛰️ Горы Хребет Драконов",
            "Высокие горы с драконами и ледяными приведениями",
            difficulty=4,
            is_locked=True,
            unlock_condition="Победите босса Короля Шахт",
            enemy_types=[
                "enemy_mountains_dragon",
                "enemy_mountains_specter",
                "enemy_mountains_troll",
                "enemy_mountains_giant",
                "enemy_mountains_drake"
            ]
        )

        # 5. ПЕЩЕРА ДРЕВНИХ — устарела: боссы перенесены в боевые локации
        self.locations["ancient_cave"] = Location(
            "ancient_cave",
            "🏰 Пещера Древних",
            "Древняя пещера (боссы теперь в своих локациях)",
            difficulty=5,
            is_locked=True,
            unlock_condition="Боссы перенесены в лес, болота, шахты и горы",
            enemy_types=[
                "enemy_ancient_boss_lich",
                "enemy_ancient_boss_archlich",
                "enemy_ancient_boss_illidari"
            ]
        )

    def unlock_location(self, location_id: str) -> bool:
        """Разблокировать локацию."""
        if location_id not in self.locations:
            return False
        self.locations[location_id].is_locked = False
        return True

    def is_location_available(self, location_id: str) -> bool:
        """Доступна ли локация."""
        from data.local_scenes import CITY_SCENES

        # Город и подлокации не блокируются прогрессом региона
        if location_id in CITY_SCENES:
            return True
        if location_id not in self.locations:
            return False
        return not self.locations[location_id].is_locked

    def get_all_locations(self) -> List[Location]:
        """Получить все локации."""
        return list(self.locations.values())

    def get_location(self, location_id: str) -> Optional[Location]:
        """Получить локацию по ID."""
        return self.locations.get(location_id)

    def check_and_unlock_locations(self) -> List[str]:
        """
        Проверить условия разблокировки и разблокировать локации.
        Возвращает список разблокированных локаций.
        """
        unlocked = []

        # Новая логика разблокировки локаций по цепочке побед над боссами:
        # - Победа над боссом 1 открывает БОЛОТА и делает доступным босса 2
        # - Победа над боссом 2 открывает ШАХТЫ и делает доступным босса 3
        # - Победа над боссом 3 открывает ГОРЫ и делает доступным босса 4
        # Эта логика заменяет предыдущие зависимости от счётчиков квестов.

        # БОЛОТА: если побежден босс 1
        if (self._quest_counters.get("boss_1_defeated")
                and self.locations["swamp"].is_locked):
            self.unlock_location("swamp")
            unlocked.append("swamp")

        # ШАХТЫ: если побежден босс 2
        if (self._quest_counters.get("boss_2_defeated")
                and self.locations["mines"].is_locked):
            self.unlock_location("mines")
            unlocked.append("mines")

        # ГОРЫ: если побежден босс 3
        if (self._quest_counters.get("boss_3_defeated")
                and self.locations["mountains"].is_locked):
            self.unlock_location("mountains")
            unlocked.append("mountains")

        return unlocked

    def increment_quest_counter(self, location_id: str) -> None:
        """Увеличить счётчик квестов для локации."""
        if location_id == "forest":
            self._quest_counters["forest_quests"] += 1
        elif location_id == "swamp":
            self._quest_counters["swamp_quests"] += 1
        elif location_id == "mines":
            self._quest_counters["mines_quests"] += 1
        elif location_id == "mountains":
            self._quest_counters["mountains_quests"] += 1

    def mark_boss_defeated(self, boss_id: int) -> None:
        """Отметить босса как побежденного."""
        if 1 <= boss_id <= 4:
            self._quest_counters[f"boss_{boss_id}_defeated"] = True

    def is_boss_unlocked(self, boss_id: int) -> bool:
        """Разблокирован ли босс."""
        # Новая логика: каждый следующий босс доступен после победы над предыдущим
        if boss_id == 1:
            return True
        if boss_id == 2:
            return bool(self._quest_counters.get("boss_1_defeated"))
        if boss_id == 3:
            return bool(self._quest_counters.get("boss_2_defeated"))
        if boss_id == 4:
            return bool(self._quest_counters.get("boss_3_defeated"))
        return False

    def is_boss_defeated(self, boss_id: int) -> bool:
        """Побежден ли босс."""
        if 1 <= boss_id <= 4:
            return self._quest_counters[f"boss_{boss_id}_defeated"]
        return False

    def get_quest_progress(self) -> Dict[str, int]:
        """Получить прогресс квестов."""
        return {
            "forest": self._quest_counters["forest_quests"],
            "swamp": self._quest_counters["swamp_quests"],
            "mines": self._quest_counters["mines_quests"],
            "mountains": self._quest_counters["mountains_quests"]
        }

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "quest_counters": self._quest_counters,
            "locations": {
                loc_id: {
                    "visited": loc.visited,
                    "is_locked": loc.is_locked
                }
                for loc_id, loc in self.locations.items()
            }
        }

    def from_dict(self, data: dict) -> None:
        """Восстановление из сохранения."""
        if "quest_counters" in data:
            self._quest_counters = data["quest_counters"]
        if "locations" in data:
            for loc_id, loc_data in data["locations"].items():
                if loc_id in self.locations:
                    self.locations[loc_id].visited = loc_data.get(
                        "visited", False
                    )
                    self.locations[loc_id].is_locked = loc_data.get(
                        "is_locked", False
                    )
