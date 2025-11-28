#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Location Service: сервис для управления логикой локаций.
Инкапсулирует логику выбора локации, генерацию врагов и создание боевого поля.
"""

from typing import Optional, Tuple
from systems.battle import Battlefield, EnemyGenerator
from data.locations import LocationManager


class LocationService:
    """Сервис управления логикой локаций.
    
    Разделяет логику выбора локации от UI.
    UI должен только вызывать методы этого сервиса и отображать результаты.
    """
    
    def __init__(self, location_manager: LocationManager, player):
        """Инициализация сервиса локаций.
        
        Args:
            location_manager: Manager для работы с локациями.
            player: Объект игрока.
        """
        self.location_manager = location_manager
        self.player = player
    
    def get_available_locations(self) -> list:
        """Получить список доступных локаций.
        
        Returns:
            list: Список доступных локаций.
        """
        return self.location_manager.get_available_locations()
    
    def get_location_info(self, location_id: str) -> dict:
        """Получить информацию о локации.
        
        Args:
            location_id: ID локации.
            
        Returns:
            dict: Информация о локации.
        """
        location = self.location_manager.get_location(location_id)
        if not location:
            return {}
        
        return {
            'id': location.id,
            'name': location.name,
            'description': location.description,
            'difficulty': location.difficulty,
            'is_unlocked': self.location_manager.is_location_unlocked(location_id),
            'unlock_condition': location.unlock_condition,
            'is_boss_location': getattr(location, 'is_boss', False),
        }
    
    def start_battle_for_location(self, location_id: str) -> Tuple[bool, Optional[Battlefield], Optional[str]]:
        """Начать боевое сражение для локации.
        
        Args:
            location_id: ID локации.
            
        Returns:
            Кортеж (успешно_ли, battlefield, сообщение_об_ошибке).
        """
        # Проверяем, разблокирована ли локация
        if not self.location_manager.is_location_unlocked(location_id):
            location = self.location_manager.get_location(location_id)
            unlock_text = (location.unlock_condition 
                          if location and location.unlock_condition 
                          else "Неизвестное требование")
            return False, None, f"Локация заблокирована. Требование: {unlock_text}"
        
        # Генерируем врагов
        enemies = EnemyGenerator.generate_for_location(
            location_id,
            self.player.level,
            count=self._get_enemy_count(location_id)
        )
        
        if not enemies:
            return False, None, "Не удалось сгенерировать врагов для локации"
        
        # Создаем боевое поле
        battlefield = Battlefield(self.player, enemies)
        
        return True, battlefield, None
    
    def _get_enemy_count(self, location_id: str) -> int:
        """Получить количество врагов для локации.
        
        Args:
            location_id: ID локации.
            
        Returns:
            int: Количество врагов.
        """
        # Стандартное количество врагов - от 2 до 4
        # Можно настроить на основе сложности локации
        base_count = 3
        
        location = self.location_manager.get_location(location_id)
        if location:
            if hasattr(location, 'difficulty'):
                difficulty = location.difficulty
                if difficulty == "Легко":
                    base_count = 2
                elif difficulty == "Средне":
                    base_count = 3
                elif difficulty == "Сложно":
                    base_count = 4
                elif difficulty == "Очень сложно":
                    base_count = 5
        
        return base_count
    
    def is_location_unlocked(self, location_id: str) -> bool:
        """Проверить, разблокирована ли локация.
        
        Args:
            location_id: ID локации.
            
        Returns:
            bool: True если разблокирована, False иначе.
        """
        return self.location_manager.is_location_unlocked(location_id)
    
    def get_boss_locations(self) -> list:
        """Получить список локаций с боссами.
        
        Returns:
            list: Список локаций с боссами.
        """
        available = self.get_available_locations()
        return [loc for loc in available if getattr(loc, 'is_boss', False)]
