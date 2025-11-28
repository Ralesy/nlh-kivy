#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Battle Service: сервис для управления логикой боя.
Разделяет UI логику от игровой логики боя.
"""

from typing import Tuple, List, Optional
from systems.battle import Battlefield


class BattleService:
    """Сервис управления боевой логикой.
    
    Инкапсулирует всю логику боя, отделяя её от UI.
    UI должен только вызывать методы этого сервиса и отображать результаты.
    """
    
    def __init__(self, battlefield: Battlefield):
        """Инициализация сервиса боя.
        
        Args:
            battlefield: Объект боевого поля с игроком и врагами.
        """
        self.battlefield = battlefield
    
    def get_battle_status(self) -> dict:
        """Получить статус боя.
        
        Returns:
            dict с информацией о состоянии боя:
            - round: номер раунда
            - player_health: текущее здоровье игрока
            - player_max_health: максимальное здоровье игрока
            - player_damage: урон игрока
            - player_defense: защита игрока
            - companions: список спутников
            - enemies: список врагов
            - is_over: закончилась ли битва
            - player_alive: жив ли игрок
        """
        player = self.battlefield.player
        companions = []
        if player.companions:
            alive_companions = [c for c in player.companions if c.is_alive]
            for companion in alive_companions:
                companions.append({
                    'name': companion.name,
                    'health': companion.health,
                    'max_health': companion.max_health,
                })
        
        enemies = []
        for enemy in self.battlefield.alive_enemies():
            enemies.append({
                'name': enemy.name,
                'health': enemy.health,
                'max_health': enemy.max_health,
                'damage': enemy.damage,
                'defense': enemy.defense,
            })
        
        return {
            'round': self.battlefield.round,
            'player_health': player.health,
            'player_max_health': player.max_health,
            'player_damage': player.damage,
            'player_defense': player.defense,
            'companions': companions,
            'enemies': enemies,
            'is_over': self.battlefield.is_over(),
            'player_alive': player.is_alive,
        }
    
    def player_attack_enemy(self, enemy_index: int) -> Tuple[str, bool]:
        """Атака игрока по врагу.
        
        Args:
            enemy_index: Индекс врага в списке живых врагов.
            
        Returns:
            Кортеж (лог_сообщения, враг_убит).
        """
        return self.battlefield.player_attack()
    
    def use_ability(self) -> Tuple[bool, List[str]]:
        """Использовать способность оружия.
        
        Returns:
            Кортеж (успешно_ли, список_логов).
        """
        return self.battlefield.use_weapon_ability()
    
    def enemy_attack(self) -> Tuple[str, bool]:
        """Враги атакуют игрока.
        
        Returns:
            Кортеж (лог_сообщения, игрок_убит).
        """
        return self.battlefield.enemy_attack()
    
    def next_round(self) -> None:
        """Перейти на следующий раунд."""
        self.battlefield.round += 1
    
    def is_battle_over(self) -> bool:
        """Проверить, закончилась ли битва."""
        return self.battlefield.is_over()
    
    def get_winner(self) -> Optional[str]:
        """Получить победителя битвы.
        
        Returns:
            'player' если победил игрок, 'enemies' если враги, None если битва не окончена.
        """
        if not self.is_battle_over():
            return None
        
        if not self.battlefield.player.is_alive:
            return 'enemies'
        
        if not self.battlefield.alive_enemies():
            return 'player'
        
        return None
    
    def handle_escape(self) -> Tuple[bool, str]:
        """Обработка попытки бегства.
        
        Returns:
            Кортеж (успешно_ли_убежали, сообщение).
        """
        # В оригинальном коде это обрабатывается в UI
        # Здесь оставляем заглушку для совместимости
        return self.battlefield.handle_escape()
    
    def handle_surrender(self) -> Tuple[str, bool]:
        """Обработка сдачи.
        
        Returns:
            Кортеж (сообщение, игрок_убит).
        """
        message = f"{self.battlefield.player.name} сдался врагам..."
        self.battlefield.player.health = 0
        return message, True
