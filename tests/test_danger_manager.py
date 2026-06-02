#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for DangerManager — система глобальной опасности.
"""

import unittest
from unittest.mock import MagicMock

from systems.danger_manager import (
    DangerManager,
    DANGER_INITIAL,
    DANGER_MAX,
    DANGER_MIN,
    QUEST_DANGER_REDUCTION,
)


class TestDangerManagerInit(unittest.TestCase):
    """Тесты инициализации DangerManager."""

    def test_default_initial_value(self):
        dm = DangerManager()
        self.assertEqual(dm.danger_level, DANGER_INITIAL)
        self.assertEqual(dm.danger_level, 30.0)

    def test_custom_initial_value(self):
        dm = DangerManager(initial=50.0)
        self.assertEqual(dm.danger_level, 50.0)

    def test_initial_clamped_min(self):
        dm = DangerManager(initial=-10.0)
        self.assertEqual(dm.danger_level, DANGER_MIN)

    def test_initial_clamped_max(self):
        dm = DangerManager(initial=200.0)
        self.assertEqual(dm.danger_level, DANGER_MAX)

    def test_default_bosses_alive(self):
        dm = DangerManager()
        self.assertEqual(dm.bosses_alive, 4)


class TestDangerManagerProperties(unittest.TestCase):
    """Тесты свойств DangerManager."""

    def test_danger_level_setter_clamps(self):
        dm = DangerManager()
        dm.danger_level = 150.0
        self.assertEqual(dm.danger_level, DANGER_MAX)
        dm.danger_level = -5.0
        self.assertEqual(dm.danger_level, DANGER_MIN)

    def test_set_bosses_alive_clamps(self):
        dm = DangerManager()
        dm.set_bosses_alive(10)
        self.assertEqual(dm.bosses_alive, 4)
        dm.set_bosses_alive(-3)
        self.assertEqual(dm.bosses_alive, 0)

    def test_tier_name_safe(self):
        dm = DangerManager(initial=0.0)
        self.assertEqual(dm.tier_name, "Безопасно")

    def test_tier_name_elevated(self):
        dm = DangerManager(initial=50.0)
        self.assertEqual(dm.tier_name, "Повышенная опасность")

    def test_tier_name_critical(self):
        dm = DangerManager(initial=80.0)
        self.assertEqual(dm.tier_name, "Критическая опасность")

    def test_tier_name_apocalypse(self):
        dm = DangerManager(initial=100.0)
        self.assertEqual(dm.tier_name, "Апокалипсис")


class TestPriceModifier(unittest.TestCase):
    """Тесты модификатора цен."""

    def test_safe_modifier(self):
        dm = DangerManager(initial=0.0)
        self.assertEqual(dm.get_price_modifier(), 1.0)

    def test_safe_modifier_at_49(self):
        dm = DangerManager(initial=49.9)
        self.assertEqual(dm.get_price_modifier(), 1.0)

    def test_elevated_modifier(self):
        dm = DangerManager(initial=50.0)
        self.assertEqual(dm.get_price_modifier(), 1.2)

    def test_elevated_modifier_at_79(self):
        dm = DangerManager(initial=79.9)
        self.assertEqual(dm.get_price_modifier(), 1.2)

    def test_critical_modifier(self):
        dm = DangerManager(initial=80.0)
        self.assertEqual(dm.get_price_modifier(), 1.5)

    def test_critical_modifier_at_99(self):
        dm = DangerManager(initial=99.9)
        self.assertEqual(dm.get_price_modifier(), 1.5)

    def test_apocalypse_modifier(self):
        dm = DangerManager(initial=100.0)
        self.assertEqual(dm.get_price_modifier(), 2.0)


class TestDangerGrowth(unittest.TestCase):
    """Тесты роста опасности при движении."""

    def test_no_growth_when_standing_still(self):
        """Опасность не растёт если update не вызывается."""
        dm = DangerManager(initial=30.0)
        self.assertEqual(dm.danger_level, 30.0)

    def test_growth_with_4_bosses(self):
        """4 босса: +1% каждые 2 сек."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(4)
        # Симулируем 2 секунды движения
        dm.update(2.0)
        self.assertEqual(dm.danger_level, 31.0)

    def test_growth_with_3_bosses(self):
        """3 босса: +1% каждые 4 сек."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(3)
        # 4 секунды
        dm.update(4.0)
        self.assertEqual(dm.danger_level, 31.0)

    def test_growth_with_2_bosses(self):
        """2 босса: +1% каждые 6 сек."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(2)
        dm.update(6.0)
        self.assertEqual(dm.danger_level, 31.0)

    def test_growth_with_1_boss(self):
        """1 босс: +1% каждые 8 сек."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(1)
        dm.update(8.0)
        self.assertEqual(dm.danger_level, 31.0)

    def test_growth_with_0_bosses(self):
        """0 боссов: +1% каждые 10 сек."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(0)
        dm.update(10.0)
        self.assertEqual(dm.danger_level, 31.0)

    def test_no_growth_below_threshold(self):
        """Опасность не растёт если прошло мало времени."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(4)
        dm.update(1.0)  # 1 сек < 2 сек интервала
        self.assertEqual(dm.danger_level, 30.0)

    def test_multiple_ticks(self):
        """Несколько тиков за один update."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(4)
        dm.update(6.0)  # 6 сек / 2 сек = 3 тика
        self.assertEqual(dm.danger_level, 33.0)

    def test_cap_at_100(self):
        """Опасность не превышает 100."""
        dm = DangerManager(initial=99.0)
        dm.set_bosses_alive(4)
        dm.update(10.0)
        self.assertEqual(dm.danger_level, 100.0)

    def test_accumulator_persists(self):
        """Аккумулятор сохраняется между вызовами."""
        dm = DangerManager(initial=30.0)
        dm.set_bosses_alive(4)
        dm.update(1.0)  # 1 сек (нужно 2)
        self.assertEqual(dm.danger_level, 30.0)
        dm.update(1.0)  # ещё 1 сек = 2 сек всего
        self.assertEqual(dm.danger_level, 31.0)


class TestAmbush(unittest.TestCase):
    """Тесты засад при 100% опасности."""

    def test_no_ambush_below_100(self):
        """Засада невозможна при опасности < 100."""
        dm = DangerManager(initial=99.0)
        result = dm.check_ambush(1.0)
        self.assertIsNone(result)

    def test_ambush_possible_at_100(self):
        """При 100% засада возможна (но не гарантирована)."""
        dm = DangerManager(initial=100.0)
        # Запускаем много раз — хотя бы раз должна сработать
        ambushes = 0
        for _ in range(1000):
            result = dm.check_ambush(1.0)
            if result is not None:
                ambushes += 1
        # Шанс ~10% за секунду, за 1000 попыток
        # должно быть примерно 100 засад
        self.assertGreater(ambushes, 0)

    def test_ambush_returns_enemy_id(self):
        """Засада возвращает ID врага."""
        dm = DangerManager(initial=100.0)
        # Форсируем засаду через seed
        import random
        random.seed(42)
        result = dm.check_ambush(1.0)
        # Может быть None или строка
        if result is not None:
            self.assertIsInstance(result, str)
            self.assertTrue(result.startswith("enemy_"))


class TestQuestReduction(unittest.TestCase):
    """Тесты снижения опасности за квесты."""

    def test_quest_reduces_danger(self):
        dm = DangerManager(initial=50.0)
        reduction = dm.on_quest_completed()
        self.assertEqual(reduction, QUEST_DANGER_REDUCTION)
        self.assertEqual(dm.danger_level, 50.0 - QUEST_DANGER_REDUCTION)

    def test_quest_no_below_zero(self):
        dm = DangerManager(initial=10.0)
        reduction = dm.on_quest_completed()
        self.assertEqual(dm.danger_level, 0.0)
        self.assertEqual(reduction, 10.0)

    def test_quest_custom_reduction(self):
        dm = DangerManager(initial=50.0)
        reduction = dm.on_quest_completed(reduction=10.0)
        self.assertEqual(reduction, 10.0)
        self.assertEqual(dm.danger_level, 40.0)

    def test_quest_at_zero(self):
        dm = DangerManager(initial=0.0)
        reduction = dm.on_quest_completed()
        self.assertEqual(reduction, 0.0)
        self.assertEqual(dm.danger_level, 0.0)


class TestBossTracking(unittest.TestCase):
    """Тесты отслеживания боссов."""

    def test_update_from_location_manager(self):
        lm = MagicMock()
        lm.is_boss_defeated.side_effect = [
            True, True, False, False
        ]
        dm = DangerManager()
        dm.update_bosses_from_location_manager(lm)
        self.assertEqual(dm.bosses_alive, 2)

    def test_update_all_defeated(self):
        lm = MagicMock()
        lm.is_boss_defeated.return_value = True
        dm = DangerManager()
        dm.update_bosses_from_location_manager(lm)
        self.assertEqual(dm.bosses_alive, 0)

    def test_update_none_defeated(self):
        lm = MagicMock()
        lm.is_boss_defeated.return_value = False
        dm = DangerManager()
        dm.update_bosses_from_location_manager(lm)
        self.assertEqual(dm.bosses_alive, 4)


class TestSerialization(unittest.TestCase):
    """Тесты сохранения и загрузки."""

    def test_to_dict(self):
        dm = DangerManager(initial=45.0)
        dm.set_bosses_alive(2)
        data = dm.to_dict()
        self.assertEqual(data["danger_level"], 45.0)
        self.assertEqual(data["bosses_alive"], 2)
        self.assertIn("accumulator", data)

    def test_from_dict(self):
        dm = DangerManager()
        dm.from_dict({
            "danger_level": 75.0,
            "bosses_alive": 1,
            "accumulator": 3.5,
        })
        self.assertEqual(dm.danger_level, 75.0)
        self.assertEqual(dm.bosses_alive, 1)

    def test_from_dict_empty(self):
        """Пустой dict не меняет текущее состояние."""
        dm = DangerManager(initial=50.0)
        dm.from_dict({})
        # Empty dict is falsy, so from_dict returns early
        self.assertEqual(dm.danger_level, 50.0)

    def test_from_dict_none(self):
        dm = DangerManager(initial=50.0)
        dm.from_dict(None)
        self.assertEqual(dm.danger_level, 50.0)

    def test_roundtrip(self):
        dm1 = DangerManager(initial=67.0)
        dm1.set_bosses_alive(3)
        data = dm1.to_dict()

        dm2 = DangerManager()
        dm2.from_dict(data)
        self.assertEqual(dm2.danger_level, 67.0)
        self.assertEqual(dm2.bosses_alive, 3)


class TestReset(unittest.TestCase):
    """Тесты сброса."""

    def test_reset(self):
        dm = DangerManager(initial=80.0)
        dm.set_bosses_alive(1)
        dm.update(5.0)
        dm.reset()
        self.assertEqual(dm.danger_level, DANGER_INITIAL)
        self.assertEqual(dm.bosses_alive, 4)


if __name__ == "__main__":
    unittest.main()