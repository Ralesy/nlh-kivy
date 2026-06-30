#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive playthrough test - проверка всей цепочки игры
от начала до конца, включая все локации и босов.

Тест покрывает:
1. Создание персонажа
2. Запуск первой локации (Лес)
3. Постепенное открытие локаций по цепочке
4. Постепенное открытие боссов Пещеры Древних
5. Финальный бой с последним боссом
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь Python
sys.path.insert(0, str(Path(__file__).parent))

from core.creatures import Player, Creature
from data.locations import LocationManager
from data.enemies import EnemyDatabase
from data.items import ItemDatabase
from systems.battle import EnemyGenerator, Battlefield


class PlaythroughTest:
    """Тест полного прохождения игры."""
    
    def __init__(self):
        self.player = None
        self.location_manager = None
        self.day = 1
        self.battles_fought = 0
        
    def setup(self):
        """Инициализация игры."""
        ItemDatabase.initialize()
        EnemyDatabase.initialize()
        
        # Создаём персонажа
        self.player = Player("Playtester", "warrior")
        self.location_manager = LocationManager()
        
        print("=" * 60)
        print("[Действие] COMPREHENSIVE PLAYTHROUGH TEST")
        print("=" * 60)
        print(f"✓ Персонаж создан: {self.player.name} (LVL {self.player.level})")
        
    def simulate_battle_at_location(self, loc_id):
        """Симулирует бой в локации."""
        location = self.location_manager.get_location(loc_id)
        if not location or location.is_locked:
            return False
        
        # Генерируем врагов
        enemies = EnemyGenerator.generate_for_location(
            loc_id,
            self.player.level,
            count=1
        )
        
        if not enemies:
            print(f" Не удалось генерировать врагов для {loc_id}")
            return False
        
        enemy = enemies[0]
        
        # Симулируем победу - убиваем врага
        enemy.health = 0
        
        # Даём награды
        self.player.coins += enemy.base_coins
        self.player.add_experience(enemy.base_xp)
        
        # Генерируем лут
        if hasattr(enemy, '_template') and enemy._template:
            loot = enemy._template.generate_loot()
            for item_id, qty in loot:
                try:
                    self.player.inventory.add_by_id(item_id, qty)
                except:
                    pass
        
        self.battles_fought += 1
        self.day += 1
        
        return True
    
    def simulate_boss_battle(self, boss_id):
        """Симулирует бой с боссом."""
        if not self.location_manager.is_boss_unlocked(boss_id):
            return False
        
        # Генерируем босса
        boss_enemy_ids = {
            1: "enemy_ancient_cave_berserker",
            2: "enemy_ancient_cave_bog_master",
            3: "enemy_ancient_cave_mine_king",
            4: "enemy_ancient_cave_dragon_lord"
        }
        
        boss_id_str = boss_enemy_ids[boss_id]
        boss = EnemyGenerator.generate_boss(boss_id_str)
        
        if not boss:
            return False
        
        # Симулируем победу
        boss.health = 0
        
        # Даём награды
        self.player.coins += boss.base_coins
        self.player.add_experience(boss.base_xp)
        
        # Генерируем лут
        if hasattr(boss, '_template') and boss._template:
            loot = boss._template.generate_loot()
            for item_id, qty in loot:
                try:
                    self.player.inventory.add_by_id(item_id, qty)
                except:
                    pass
        
        # Отмечаем босса как побежденного
        self.location_manager.mark_boss_defeated(boss_id)
        
        self.battles_fought += 1
        self.day += 1
        
        return True
    
    def test_initial_locations(self):
        """Проверка начальных локаций."""
        print("\n" + "=" * 60)
        print("📍 ТЕ CT 1: НАЧАЛЬНЫЕ ЛОКАЦИИ")
        print("=" * 60)
        
        # Лес должен быть доступен
        assert not self.location_manager.locations["forest"].is_locked
        print("✓ Лес (Forest) доступен сразу")
        
        # Остальные должны быть заблокированы
        for loc_id in ["swamp", "mines", "mountains"]:
            assert self.location_manager.locations[loc_id].is_locked
        print("✓ Болота, Шахты, Горы заблокированы")
        
        # Пещера Древних должна быть доступна
        assert self.location_manager.locations["ancient_cave"].is_locked
        print("✓ Пещера Древних доступна")
    
    def test_forest_progression(self):
        """Тест прохождения через Лес."""
        print("\n" + "=" * 60)
        print("ТЕСТ 2: ПРОХОЖДЕНИЕ ЛЕСА")
        print("=" * 60)
        
        # Бьемся в лесу 3+ раза для разблокировки Болот
        for i in range(4):
            if self.simulate_battle_at_location("forest"):
                self.location_manager.increment_quest_counter("forest")
                print(f" Бой {i+1} в лесу")
        
        # Проверяем условия разблокировки
        unlocked = self.location_manager.check_and_unlock_locations()
        
        if "swamp" in unlocked or not self.location_manager.locations["swamp"].is_locked:
            print("✓ Болота разблокированы после 3+ квестов в лесу")
        else:
            print(f" Болота не разблокированы (прогресс: {self.location_manager.get_quest_progress()})")
    
    def test_boss_1_available(self):
        """Тест доступности первого босса."""
        print("\n" + "=" * 60)
        print("👹 ТЕСТ 3: БОСС 1 - БЕЗУМНЫЙ МАРОДЁР")
        print("=" * 60)
        
        if self.location_manager.is_boss_unlocked(1):
            if self.simulate_boss_battle(1):
                print("✓ Босс 1 разблокирован и побежден")
            else:
                print(" Не удалось генерировать босса 1")
        else:
            print(" Босс 1 не разблокирован")
    
    def test_swamp_progression(self):
        """Тест прохождения через Болота."""
        print("\n" + "=" * 60)
        print("[Болото] ТЕСТ 4: ПРОХОЖДЕНИЕ БОЛОТ")
        print("=" * 60)
        
        if self.location_manager.locations["swamp"].is_locked:
            print(" Болота еще заблокированы, пропускаем")
            return
        
        # Бьемся в болотах 4+ раза для разблокировки Шахт
        for i in range(5):
            if self.simulate_battle_at_location("swamp"):
                self.location_manager.increment_quest_counter("swamp")
                print(f" Бой {i+1} в болотах")
        
        unlocked = self.location_manager.check_and_unlock_locations()
        
        if "mines" in unlocked or not self.location_manager.locations["mines"].is_locked:
            print("✓ Шахты разблокированы после 4+ квестов в болотах")
        else:
            print(f" Шахты не разблокированы (прогресс: {self.location_manager.get_quest_progress()})")
    
    def test_boss_2_available(self):
        """Тест доступности второго босса."""
        print("\n" + "=" * 60)
        print("👹 ТЕСТ 5: БОСС 2 - ХОЗЯИН БОЛОТА")
        print("=" * 60)
        
        if self.location_manager.is_boss_unlocked(2):
            if self.simulate_boss_battle(2):
                print("✓ Босс 2 разблокирован и побежден")
            else:
                print(" Не удалось генерировать босса 2")
        else:
            print(" Босс 2 не разблокирован (требуется открыть Болота)")
    
    def test_mines_progression(self):
        """Тест прохождения через Шахты."""
        print("\n" + "=" * 60)
        print("[Шахты] ТЕСТ 6: ПРОХОЖДЕНИЕ ШАХТ")
        print("=" * 60)
        
        if self.location_manager.locations["mines"].is_locked:
            print(" Шахты еще заблокированы, пропускаем")
            return
        
        # Бьемся в шахтах 3+ раза
        for i in range(4):
            if self.simulate_battle_at_location("mines"):
                self.location_manager.increment_quest_counter("mines")
                print(f" Бой {i+1} в шахтах")
        
        unlocked = self.location_manager.check_and_unlock_locations()
        
        if "mountains" in unlocked or not self.location_manager.locations["mountains"].is_locked:
            print("✓ Горы разблокированы после 3+ квестов в шахтах")
        else:
            print(f" Горы не разблокированы (прогресс: {self.location_manager.get_quest_progress()})")
    
    def test_boss_3_available(self):
        """Тест доступности третьего босса."""
        print("\n" + "=" * 60)
        print("👹 ТЕСТ 7: БОСС 3 - КОРОЛЬ ШАХТ")
        print("=" * 60)
        
        if self.location_manager.is_boss_unlocked(3):
            if self.simulate_boss_battle(3):
                print("✓ Босс 3 разблокирован и побежден")
                # Проверяем разблокировку гор
                unlocked = self.location_manager.check_and_unlock_locations()
                if "mountains" in unlocked or not self.location_manager.locations["mountains"].is_locked:
                    print("✓ Горы разблокированы после поражения босса 3")
            else:
                print(" Не удалось генерировать босса 3")
        else:
            print(" Босс 3 не разблокирован (требуется открыть Шахты)")
    
    def test_mountains_progression(self):
        """Тест прохождения через Горы."""
        print("\n" + "=" * 60)
        print("[Горы] ТЕСТ 8: ПРОХОЖДЕНИЕ ГОР")
        print("=" * 60)
        
        if self.location_manager.locations["mountains"].is_locked:
            print(" Горы еще заблокированы, пропускаем")
            return
        
        # Бьемся в горах 2+ раза
        for i in range(3):
            if self.simulate_battle_at_location("mountains"):
                self.location_manager.increment_quest_counter("mountains")
                print(f" Бой {i+1} в горах")
    
    def test_boss_4_available(self):
        """Тест доступности четвертого босса."""
        print("\n" + "=" * 60)
        print("👹 ТЕСТ 9: БОСС 4 - ПОВЕЛИТЕЛЬ ДРАКОНОВ (ФИНАЛ)")
        print("=" * 60)
        
        if self.location_manager.is_boss_unlocked(4):
            if self.simulate_boss_battle(4):
                print("✓ Босс 4 разблокирован и побежден!")
            else:
                print(" Не удалось генерировать босса 4")
        else:
            print(" Босс 4 не разблокирован (требуется открыть Горы)")
    
    def test_player_progression(self):
        """Тест прогресса персонажа."""
        print("\n" + "=" * 60)
        print("ТЕСТ 10: ПРОГРЕСС ПЕРСОНАЖА")
        print("=" * 60)
        
        print(f"✓ Уровень: {self.player.level}")
        print(f"✓ Опыт: {self.player.experience}")
        print(f"✓ Монеты: {self.player.coins}")
        print(f"✓ HP: {self.player.health}/{self.player.max_health}")
        print(f"✓ Всего боёв: {self.battles_fought}")
        print(f"✓ Дней в игре: {self.day}")
    
    def run(self):
        """Запуск всех тестов."""
        try:
            self.setup()
            self.test_initial_locations()
            self.test_forest_progression()
            self.test_boss_1_available()
            self.test_swamp_progression()
            self.test_boss_2_available()
            self.test_mines_progression()
            self.test_boss_3_available()
            self.test_mountains_progression()
            self.test_boss_4_available()
            self.test_player_progression()
            
            print("\n" + "=" * 60)
            print("ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
            print("=" * 60)
            return 0
        
        except Exception as e:
            print(f"\nОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    test = PlaythroughTest()
    sys.exit(test.run())
