#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locations: система локаций с блокировками и условиями открытия.
Боевые локации (forest, swamp, mines, mountains) удалены — 
боссы перемещены на глобальную карту как roaming-сущности.
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
        self.difficulty = difficulty
        self.is_locked = is_locked
        self.unlock_condition = unlock_condition
        self.visited = False
        self.enemy_types = enemy_types or []

    def display_status(self) -> str:
        """Отображение статуса локации."""
        if self.is_locked:
            return f"{self.name}"
        elif self.visited:
            return f"{self.name}"
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
        self._boss_flags: Dict[str, bool] = {
            "boss_1_defeated": False,
            "boss_2_defeated": False,
            "boss_3_defeated": False,
            "boss_4_defeated": False
        }
        self._initialize_locations()

    def _initialize_locations(self) -> None:
        """Инициализация локаций (только город и вспомогательные)."""
        # Город — всегда доступен
        self.locations["city"] = Location(
            "city",
            "Город",
            "Главный город региона",
            difficulty=0,
            is_locked=False,
        )

        # Деревня — в разработке
        self.locations["village"] = Location(
            "village",
            "🏘️ Деревня",
            "Небольшая деревня",
            difficulty=1,
            is_locked=True,
            unlock_condition="В разработке",
        )

    def unlock_location(self, location_id: str) -> bool:
        """Разблокировать локацию."""
        if location_id not in self.locations:
            return False
        self.locations[location_id].is_locked = False
        return True

    def is_location_available(self, location_id: str) -> bool:
        """Доступна ли локация."""
        # Город не блокируется
        if location_id == "city":
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
        (Боевые локации удалены, но метод оставлен для совместимости.)
        Возвращает список разблокированных локаций.
        """
        unlocked = []
        return unlocked

    def mark_boss_defeated(self, boss_id: int) -> None:
        """Отметить босса как побежденного."""
        if 1 <= boss_id <= 4:
            self._boss_flags[f"boss_{boss_id}_defeated"] = True

    def is_boss_unlocked(self, boss_id: int) -> bool:
        """Разблокирован ли босс (цепочка: каждый следующий после победы над предыдущим)."""
        if boss_id == 1:
            return True
        if boss_id == 2:
            return bool(self._boss_flags.get("boss_1_defeated"))
        if boss_id == 3:
            return bool(self._boss_flags.get("boss_2_defeated"))
        if boss_id == 4:
            return bool(self._boss_flags.get("boss_3_defeated"))
        return False

    def is_boss_defeated(self, boss_id: int) -> bool:
        """Побежден ли босс."""
        if 1 <= boss_id <= 4:
            return self._boss_flags[f"boss_{boss_id}_defeated"]
        return False

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "boss_flags": self._boss_flags,
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
        if "boss_flags" in data:
            self._boss_flags = data["boss_flags"]
        elif "quest_counters" in data:
            # Совместимость со старыми сохранениями
            old = data["quest_counters"]
            self._boss_flags["boss_1_defeated"] = old.get("boss_1_defeated", False)
            self._boss_flags["boss_2_defeated"] = old.get("boss_2_defeated", False)
            self._boss_flags["boss_3_defeated"] = old.get("boss_3_defeated", False)
            self._boss_flags["boss_4_defeated"] = old.get("boss_4_defeated", False)
        if "locations" in data:
            for loc_id, loc_data in data["locations"].items():
                if loc_id in self.locations:
                    self.locations[loc_id].visited = loc_data.get(
                        "visited", False
                    )
                    self.locations[loc_id].is_locked = loc_data.get(
                        "is_locked", False
                    )