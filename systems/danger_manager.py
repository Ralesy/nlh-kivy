#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DangerManager — система «Глобальной Опасности» (Global Danger).

Шкала опасности (0.0–100.0) растёт, пока игрок перемещается по глобальной
карте, и влияет на цены в магазине.  При 100% возможны случайные засады.
Скорость роста зависит от количества живых боссов.
Снижение — через сдачу квестов NPC.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from data.locations import LocationManager


# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

DANGER_MIN: float = 0.0
DANGER_MAX: float = 100.0
DANGER_INITIAL: float = 30.0

# Базовый интервал (в секундах) между +1% при 4 живых боссах
BASE_TICK_SECONDS: float = 2.0

# Множители интервала в зависимости от живых боссов
# bosses_alive -> multiplier  (итоговый интервал = BASE * multiplier)
BOSS_MULTIPLIERS = {
    4: 1,   # +1% каждые 2 сек
    3: 2,   # +1% каждые 4 сек
    2: 3,   # +1% каждые 6 сек
    1: 4,   # +1% каждые 8 сек
    0: 5,   # +1% каждые 10 сек (эндгейм)
}

# Пороги градаций и соответствующие модификаторы цен
THRESHOLDS: List[Tuple[float, float, str]] = [
    # (нижняя граница, модификатор цен, название)
    (100.0, 2.0, "Апокалипсис"),
    (80.0,  1.5, "Критическая опасность"),
    (50.0,  1.2, "Повышенная опасность"),
    (0.0,   1.0, "Безопасно"),
]

# Снижение опасности за сдачу квеста
QUEST_DANGER_REDUCTION: float = 25.0

# Шанс засады за секунду движения при danger == 100 (10%)
AMBUSH_CHANCE_PER_SECOND: float = 0.10


class DangerManager:
    """Менеджер глобальной опасности.

    Использование::

        dm = DangerManager()
        dm.set_bosses_alive(4)

        # В игровом цикле (каждый кадр при движении по глобальной карте):
        ambush_enemy = dm.update(dt, location_manager)
        if ambush_enemy:
            # начать бой с ambush_enemy

        # Модификатор цен:
        price_mod = dm.get_price_modifier()

        # Сдача квеста:
        dm.on_quest_completed()
    """

    def __init__(self, initial: float = DANGER_INITIAL):
        self._danger_level: float = max(DANGER_MIN, min(DANGER_MAX, initial))
        self._bosses_alive: int = 4
        self._accumulator: float = 0.0  # накопитель времени для тика

    # ------------------------------------------------------------------
    # Свойства
    # ------------------------------------------------------------------

    @property
    def danger_level(self) -> float:
        """Текущий уровень опасности (0.0–100.0)."""
        return self._danger_level

    @danger_level.setter
    def danger_level(self, value: float) -> None:
        self._danger_level = max(DANGER_MIN, min(DANGER_MAX, value))

    @property
    def bosses_alive(self) -> int:
        """Количество живых боссов."""
        return self._bosses_alive

    @property
    def tier_name(self) -> str:
        """Название текущей градации опасности."""
        for threshold, _, name in THRESHOLDS:
            if self._danger_level >= threshold:
                return name
        return "Безопасно"

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------

    def set_bosses_alive(self, count: int) -> None:
        """Установить количество живых боссов (0–4)."""
        self._bosses_alive = max(0, min(4, count))

    def update_bosses_from_location_manager(
        self, location_manager: "LocationManager"
    ) -> None:
        """Определить кол-во живых боссов из LocationManager."""
        defeated = 0
        for boss_id in range(1, 5):
            if location_manager.is_boss_defeated(boss_id):
                defeated += 1
        self._bosses_alive = 4 - defeated

    def get_price_modifier(self) -> float:
        """Множитель цен для магазина."""
        for threshold, modifier, _ in THRESHOLDS:
            if self._danger_level >= threshold:
                return modifier
        return 1.0

    def update(
        self,
        dt: float,
        location_manager: Optional["LocationManager"] = None,
    ) -> Optional[str]:
        """Обновить опасность при движении по глобальной карте.

        Args:
            dt: дельта времени (секунды) с прошлого кадра.
            location_manager: опционально — для авто-обновления боссов.

        Returns:
            ID случайного врага для засады, или None.
        """
        if location_manager is not None:
            self.update_bosses_from_location_manager(location_manager)

        # Рост опасности
        interval = self._get_tick_interval()
        self._accumulator += dt

        while self._accumulator >= interval and self._danger_level < DANGER_MAX:
            self._danger_level = min(DANGER_MAX, self._danger_level + 1.0)
            self._accumulator -= interval

        # Если достигли максимума — сбрасываем аккумулятор
        if self._danger_level >= DANGER_MAX:
            self._accumulator = 0.0

        # Проверка засады
        return self.check_ambush(dt)

    def check_ambush(self, dt: float) -> Optional[str]:
        """Проверить шанс засады.

        Вызывается автоматически из update(), но можно вызвать и вручную.

        Args:
            dt: дельта времени (секунды).

        Returns:
            ID врага для засады или None.
        """
        if self._danger_level < DANGER_MAX:
            return None

        # Шанс засады пропорционален dt
        base = 1.0 - AMBUSH_CHANCE_PER_SECOND
        chance = 1.0 - base ** dt
        if random.random() < chance:
            return self._pick_random_enemy()
        return None

    def on_quest_completed(
        self, reduction: float = QUEST_DANGER_REDUCTION
    ) -> float:
        """Вызвать при сдаче квеста NPC.

        Args:
            reduction: на сколько процентов снизить опасность.

        Returns:
            Фактическое снижение (для отображения в UI).
        """
        old = self._danger_level
        self._danger_level = max(DANGER_MIN, self._danger_level - reduction)
        return old - self._danger_level

    def reset(self) -> None:
        """Сбросить к начальному состоянию (новая игра)."""
        self._danger_level = DANGER_INITIAL
        self._bosses_alive = 4
        self._accumulator = 0.0

    # ------------------------------------------------------------------
    # Сериализация
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "danger_level": self._danger_level,
            "bosses_alive": self._bosses_alive,
            "accumulator": self._accumulator,
        }

    def from_dict(self, data: dict) -> None:
        """Восстановить из сохранения."""
        if not data:
            return
        self._danger_level = float(data.get("danger_level", DANGER_INITIAL))
        self._bosses_alive = int(data.get("bosses_alive", 4))
        self._accumulator = float(data.get("accumulator", 0.0))

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    def _get_tick_interval(self) -> float:
        """Интервал (сек) между +1% в зависимости от живых боссов."""
        mult = BOSS_MULTIPLIERS.get(self._bosses_alive, BOSS_MULTIPLIERS[0])
        return BASE_TICK_SECONDS * mult

    @staticmethod
    def _pick_random_enemy() -> str:
        """Случайный враг из любого биома для засады."""
        # Все враги из всех биомов (forest, swamp, mines, mountains)
        all_enemies = [
            # Лес
            "enemy_forest_wolf",
            "enemy_forest_raider",
            "enemy_forest_bandit",
            "enemy_forest_scout",
            # Болота
            "enemy_swamp_goblin",
            "enemy_swamp_toad",
            "enemy_swamp_shamanic",
            # Шахты
            "enemy_mines_orc",
            "enemy_mines_draugr",
            "enemy_mines_golem",
            "enemy_mines_skeleton",
            "enemy_mines_greyling",
            # Горы
            "enemy_mountains_dragon",
            "enemy_mountains_specter",
            "enemy_mountains_troll",
            "enemy_mountains_giant",
            "enemy_mountains_drake",
        ]
        return random.choice(all_enemies)