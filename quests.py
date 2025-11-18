#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quests: система квестов и таверна.
"""

from typing import Dict, Optional
from creatures import Player
from items import ItemDatabase


class Quest:
    """Квест."""

    def __init__(
        self,
        id_: str,
        desc: str,
        goal: Dict[str, int],
        reward: Dict,
        progress: Optional[Dict[str, int]] = None
    ):
        self.id = id_
        self.desc = desc
        self.goal = goal
        self.reward = reward
        self.progress = progress or {k: 0 for k in goal.keys()}
        self.complete = False
        self.claimed = False

    def register_kill(self, enemy_name: str) -> None:
        """Регистрация убийства врага."""
        if enemy_name in self.goal:
            self.progress[enemy_name] = min(
                self.goal[enemy_name],
                self.progress.get(enemy_name, 0) + 1
            )
            self.check_complete()

    def register_win(self) -> None:
        """Регистрация победы в бою."""
        if "wins" in self.goal:
            self.progress["wins"] = min(
                self.goal["wins"],
                self.progress.get("wins", 0) + 1
            )
            self.check_complete()

    def check_complete(self) -> None:
        """Проверка завершения квеста."""
        self.complete = all(
            self.progress.get(k, 0) >= v for k, v in self.goal.items()
        )

    def claim(self, player: Player) -> str:
        """Получить награду."""
        if not self.complete:
            return "Квест не завершён."
        if self.claimed:
            return "Награда уже получена."

        self.claimed = True
        msg = []

        if "coins" in self.reward:
            player.coins += self.reward["coins"]
            msg.append(f"+{self.reward['coins']} монет")

        if "exp" in self.reward:
            msgs = player.add_experience(self.reward["exp"])
            msg.extend(msgs)

        if "item" in self.reward:
            item = ItemDatabase.get(self.reward["item"])
            if item and player.inventory.has_space_for(1):
                player.inventory.add(item, 1)
                msg.append(f"получен {item.display_name()}")

        return "Награда: " + ", ".join(msg)

    def progress_display(self) -> str:
        """Отображение прогресса."""
        if self.complete:
            return "Завершён"
        total_goal = sum(self.goal.values())
        total_progress = sum(self.progress.values())
        return f"{total_progress}/{total_goal}"


class Tavern:
    """Таверна с квестами и спутниками."""

    COMPANIONS = [
        ("Thorg", "tank"),
        ("Lyra", "healer"),
        ("Rook", "archer"),
        ("Kira", "archer"),
        ("Brom", "tank"),
        ("Elara", "healer")
    ]

    def __init__(self):
        self.available_quests: Dict[str, Quest] = {}
        self._initialize_quests()

    def _initialize_quests(self) -> None:
        """Инициализация квестов."""
        quests = [
            Quest("q_kill_wolves", "Убей 3 волков",
                  {"Волк": 3},
                  {"coins": 150, "exp": 120}),
            Quest("q_kill_goblins", "Избави лес от 5 гоблинов",
                  {"Лесной гоблин": 5},
                  {"coins": 200, "exp": 150}),
            Quest("q_win3", "Выиграй 3 битвы подряд",
                  {"wins": 3},
                  {"coins": 250, "exp": 200, "item": "w_sword"}),
            Quest("q_cave_explorer", "Исследуй пещеру (5 победы)",
                  {"wins": 5},
                  {"coins": 400, "exp": 300, "item": "p_large"}),
            Quest("q_legendary", "Победи 10 врагов",
                  {"wins": 10},
                  {"coins": 1000, "exp": 500, "item": "w_great_sword"})
        ]
        for q in quests:
            self.available_quests[q.id] = q

    def list_quests(self) -> str:
        """Список квестов."""
        lines = []
        for q in self.available_quests.values():
            status = q.progress_display()
            claimed = " [ПОЛУЧЕНО]" if q.claimed else ""
            lines.append(f"{q.id}: {q.desc} - {status}{claimed}")
        return "\n".join(lines)

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Получить квест по ID."""
        return self.available_quests.get(quest_id)

    def get_random_companion(self) -> tuple:
        """Получить случайного спутника."""
        import random
        return random.choice(self.COMPANIONS)

    def list_companions(self) -> str:
        """Список доступных спутников."""
        lines = []
        roles_desc = {
            "tank": "Танк (высокая защита)",
            "archer": "Лучник (высокий урон)",
            "healer": "Целитель (восстанавливает HP)"
        }
        seen_roles = set()
        for i, (name, role) in enumerate(self.COMPANIONS, 1):
            if role not in seen_roles:
                lines.append(f"{role}: {roles_desc[role]}")
                seen_roles.add(role)
        lines.append("")
        for i, (name, role) in enumerate(self.COMPANIONS, 1):
            lines.append(f"{i}) {name} — {role} (цена: 50 монет)")
        return "\n".join(lines)
