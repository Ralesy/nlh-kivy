#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Active Quests System: система активных квестов игрока.
"""

from typing import Dict, List, Optional
from quests import Quest
from creatures import Player


class ActiveQuests:
    """Система активных квестов игрока."""
    
    def __init__(self):
        self.active_quests: Dict[str, Quest] = {}
        self.completed_quests: Dict[str, Quest] = {}
        self.npc_assignments: Dict[str, str] = {}  # quest_id -> npc_id
    
    def add_quest(self, quest: Quest, npc_id: str = "") -> bool:
        """Добавить активный квест."""
        if quest.id in self.active_quests:
            return False  # Уже активен
        
        quest.status = "active"
        self.active_quests[quest.id] = quest
        
        if npc_id:
            self.npc_assignments[quest.id] = npc_id
        
        return True
    
    def remove_quest(self, quest_id: str) -> bool:
        """Удалить квест из активных."""
        if quest_id in self.active_quests:
            del self.active_quests[quest_id]
            if quest_id in self.npc_assignments:
                del self.npc_assignments[quest_id]
            return True
        return False
    
    def complete_quest(self, quest_id: str) -> bool:
        """Отметить квест как завершенный."""
        if quest_id in self.active_quests:
            quest = self.active_quests[quest_id]
            quest.status = "completed"
            quest.complete = True
            
            # Перемещаем в завершенные
            self.completed_quests[quest_id] = quest
            self.remove_quest(quest_id)
            
            return True
        return False
    
    def claim_quest_reward(self, quest_id: str, player: Player) -> str:
        """Получить награду за квест."""
        if quest_id not in self.completed_quests:
            return "Квест не найден."
        
        quest = self.completed_quests[quest_id]
        if quest.claimed:
            return "Награда уже получена."
        
        result = quest.claim(player)
        quest.claimed = True
        
        return result
    
    def register_kill(self, enemy_name: str) -> None:
        """Регистрация убийства для всех активных квестов."""
        for quest in self.active_quests.values():
            if hasattr(quest, 'target_enemy_type') and quest.target_enemy_type:
                if enemy_name == quest.target_enemy_type:
                    quest.register_kill(enemy_name)
                    if quest.complete:
                        self.complete_quest(quest.id)
    
    def register_item_found(self, item_id: str) -> None:
        """Регистрация найденного предмета для всех активных квестов."""
        for quest in self.active_quests.values():
            if hasattr(quest, 'target_item_id') and quest.target_item_id:
                if item_id == quest.target_item_id:
                    # Увеличиваем прогресс для предметов
                    quest.progress[item_id] = quest.progress.get(item_id, 0) + 1
                    quest.check_complete()
                    if quest.complete:
                        self.complete_quest(quest.id)
    
    def get_active_quests(self) -> List[Quest]:
        """Получить список активных квестов."""
        return list(self.active_quests.values())
    
    def get_completed_quests(self) -> List[Quest]:
        """Получить список завершенных квестов."""
        return list(self.completed_quests.values())
    
    def get_quest_by_npc(self, npc_id: str) -> List[Quest]:
        """Получить квесты от конкретного NPC."""
        quests = []
        for quest_id, assigned_npc in self.npc_assignments.items():
            if assigned_npc == npc_id:
                if quest_id in self.active_quests:
                    quests.append(self.active_quests[quest_id])
                elif quest_id in self.completed_quests:
                    quests.append(self.completed_quests[quest_id])
        return quests
    
    def has_active_quest_from_npc(self, npc_id: str) -> bool:
        """Проверить, есть ли активный квест от NPC."""
        for quest_id, assigned_npc in self.npc_assignments.items():
            if assigned_npc == npc_id and quest_id in self.active_quests:
                return True
        return False
    
    def get_quest_status_text(self, quest: Quest) -> str:
        """Получить текст статуса квеста."""
        if quest.status == "completed":
            return "Завершён - получите награду"
        elif quest.complete:
            return "Готов к сдаче"
        else:
            return quest.progress_display()
    
    def get_all_quests_summary(self) -> str:
        """Получить краткую сводку всех квестов."""
        active_count = len(self.active_quests)
        completed_count = len(self.completed_quests)
        claimed_count = sum(1 for q in self.completed_quests.values() if q.claimed)
        
        return f"Активных: {active_count} | Завершено: {completed_count} | Получено наград: {claimed_count}"
