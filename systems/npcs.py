#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NPCs: система NPC в таверне с диалогами и генерацией квестов.
"""

from typing import List, Optional, Dict
import random
from enum import Enum


class QuestType(Enum):
    """Тип квеста."""
    KILL_ENEMIES = "kill_enemies"
    COLLECT_ITEM = "collect_item"


class QuestState(Enum):
    """Состояние квеста."""
    NOT_TAKEN = "not_taken"
    ACTIVE = "active"
    COMPLETED = "completed"


class GeneratedQuest:
    """Сгенерированный квест от NPC."""

    def __init__(
        self,
        id_: str,
        title: str,
        description: str,
        quest_type: QuestType,
        target: str,
        required_count: int,
        reward_gold: int,
        reward_xp: int = 0,
        npc_id: str = ""
    ):
        self.id = id_
        self.title = title
        self.description = description
        self.quest_type = quest_type
        self.target = target  # Имя врага или ID предмета
        self.required_count = required_count
        self.current_progress = 0
        self.reward_gold = reward_gold
        self.reward_xp = reward_xp
        self.npc_id = npc_id
        self.state = QuestState.NOT_TAKEN

    def is_complete(self) -> bool:
        """Завершён ли квест."""
        return self.current_progress >= self.required_count

    def progress_display(self) -> str:
        """Отображение прогресса."""
        if self.quest_type == QuestType.KILL_ENEMIES:
            return (f"Убить {self.target}: "
                    f"{self.current_progress}/{self.required_count}")
        elif self.quest_type == QuestType.COLLECT_ITEM:
            return (f"Найти {self.target}: "
                    f"{self.current_progress}/{self.required_count}")
        return "Неизвестный квест"

    def update_progress(self, enemy_name: str):
        """Обновить прогресс квеста."""
        if self.state == QuestState.ACTIVE and self.quest_type == QuestType.KILL_ENEMIES:
            target_lower = self.target.lower()
            enemy_lower = enemy_name.lower()
            # Совпадение по полному имени или вхождению target в имя врага
            # (например "волк" содержится в "Лесной волк")
            matched = target_lower == enemy_lower or target_lower in enemy_lower
            if matched:
                self.current_progress = min(self.required_count, self.current_progress + 1)
            return matched
        return False

    def is_complete(self):
        """Проверить, выполнен ли квест."""
        return self.current_progress >= self.required_count

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "quest_type": self.quest_type.value,
            "target": self.target,
            "required_count": self.required_count,
            "current_progress": self.current_progress,
            "reward_gold": self.reward_gold,
            "reward_xp": self.reward_xp,
            "npc_id": self.npc_id,
            "state": self.state.value
        }

    @classmethod
    def from_dict(cls, data):
        quest = cls(
            id_=data["id"],
            title=data["title"],
            description=data["description"],
            quest_type=QuestType(data["quest_type"]),
            target=data["target"],
            required_count=data["required_count"],
            reward_gold=data["reward_gold"],
            reward_xp=data["reward_xp"],
            npc_id=data["npc_id"]
        )
        quest.current_progress = data["current_progress"]
        quest.state = QuestState(data["state"])
        return quest


class NPC:
    """NPC в таверне."""

    def __init__(
        self,
        id_: str,
        name: str,
        title: str,
        background: str
    ):
        self.id = id_
        self.name = name
        self.title = title
        self.background = background
        self.current_quest: Optional[GeneratedQuest] = None
        self.completed_quests_count = 0

    def get_introduction(self) -> str:
        """Получить интро NPC."""
        return f"{self.name}, {self.title}:\n\"{self.background}\""

    def offer_quest(self, quest: GeneratedQuest) -> str:
        """Предложить квест игроку."""
        self.current_quest = quest
        quest.state = QuestState.NOT_TAKEN
        return f"{self.name}: \"{quest.description}\"\n\nПринять квест?"

    def accept_quest(self) -> bool:
        """Игрок принимает квест."""
        if self.current_quest is None:
            return False
        self.current_quest.state = QuestState.ACTIVE
        return True

    def reject_quest(self) -> bool:
        """Игрок отказывает от квеста."""
        if self.current_quest is None:
            return False
        self.current_quest.state = QuestState.NOT_TAKEN
        self.current_quest = None
        return True

    def is_quest_active(self) -> bool:
        """Есть ли квест у NPC (активный или предложенный)."""
        return self.current_quest is not None

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "background": self.background,
            "current_quest": (self.current_quest.to_dict()
                              if self.current_quest else None),
            "completed_quests_count": self.completed_quests_count
        }


class CaptainGuard(NPC):
    """NPC #1 - Капитан городской стражи (лесные враги)."""

    ENEMY_TYPES = ["волк", "мародёр", "бандит", "дезертир"]
    BACKSTORIES = [
        "Эти мерзавцы опять оборзели на дороге!",
        "Нужна помощь - враги атакуют караваны.",
        "Граждане просят защиты от разбойников.",
        "Слишком много дезертиров в лесу.",
    ]

    def __init__(self):
        super().__init__(
            "npc_captain",
            "Капитан Редард",
            "Капитан городской стражи",
            "Опытный боевой офицер, защищающий город от угроз."
        )

    def generate_quest(self) -> GeneratedQuest:
        """Генерировать новый квест."""
        enemy = random.choice(self.ENEMY_TYPES)
        backstory = random.choice(self.BACKSTORIES)
        count = random.randint(3, 10)
        reward = count * 50 + random.randint(20, 50)

        quest_id = f"q_captain_{self.completed_quests_count}"
        quest = GeneratedQuest(
            quest_id,
            f"Истребить {count} {enemy}",
            backstory,
            QuestType.KILL_ENEMIES,
            enemy,
            count,
            reward,
            count * 25,
            self.id
        )
        return quest


class SwampTracker(NPC):
    """NPC #2 - Старый болотный следопыт (враги болот)."""

    ENEMY_TYPES = ["гоблин", "гигантская жаба", "шаман болот"]
    BACKSTORIES = [
        "Болото полно неприятных тварей!",
        "Помогите - жабы атакуют посёлки.",
        "Гоблины воруют припасы из болота.",
    ]

    def __init__(self):
        super().__init__(
            "npc_tracker",
            "Артем Болотник",
            "Старый болотный следопыт",
            "Жизнь в болоте научила его видеть опасность издалека."
        )

    def generate_quest(self) -> GeneratedQuest:
        """Генерировать новый квест."""
        enemy = random.choice(self.ENEMY_TYPES)
        backstory = random.choice(self.BACKSTORIES)
        count = random.randint(4, 12)
        reward = count * 60 + random.randint(30, 60)

        quest_id = f"q_tracker_{self.completed_quests_count}"
        quest = GeneratedQuest(
            quest_id,
            f"Истребить {count} {enemy}",
            backstory,
            QuestType.KILL_ENEMIES,
            enemy,
            count,
            reward,
            count * 30,
            self.id
        )
        return quest


class CrazeMiner(NPC):
    """NPC #3 - Сумасшедший шахтёр (враги шахт)."""

    ENEMY_TYPES = [
        "орк",
        "драугр-шахтёр",
        "скелет",
        "каменный голем",
    ]
    BACKSTORIES = [
        "Шахты наполнены ужасными монстрами!",
        "Нужна помощь - орки захватили туннели.",
        "Камнежор снова беспокоит мой район.",
        "Скелеты восстали из глубин!",
    ]

    def __init__(self):
        super().__init__(
            "npc_miner",
            "Хромой Гарик",
            "Сумасшедший шахтёр",
            "Проведя половину жизни под землёй, он знает каждый туннель."
        )

    def generate_quest(self) -> GeneratedQuest:
        """Генерировать новый квест."""
        enemy = random.choice(self.ENEMY_TYPES)
        backstory = random.choice(self.BACKSTORIES)
        count = random.randint(3, 8)
        reward = count * 80 + random.randint(40, 80)

        quest_id = f"q_miner_{self.completed_quests_count}"
        quest = GeneratedQuest(
            quest_id,
            f"Истребить {count} {enemy}",
            backstory,
            QuestType.KILL_ENEMIES,
            enemy,
            count,
            reward,
            count * 40,
            self.id
        )
        return quest


class CurioCollector(NPC):
    """NPC #4 - Коллекционер уродливых вещей (поиск предметов)."""

    ITEM_TARGETS = [
        ("гоблинское оружие", "w_goblin_cleaver", 100),
        ("орчий шлем", "a_orc_mail", 120),
        ("гномий топор", "w_dwarf_axe", 150),
        ("стальная кираса", "a_steel_plate", 140),
    ]
    BACKSTORIES = [
        "Мне нужно пополнить мою коллекцию редких предметов!",
        "Найди мне уникальный артефакт - и я щедро награжу.",
        "Коллекционирование - мое увлечение и моя страсть.",
    ]

    def __init__(self):
        super().__init__(
            "npc_collector",
            "Престон Кураж",
            "Коллекционер уродливых вещей",
            "Богатый меценат, собирающий предметы со всего мира."
        )

    def generate_quest(self) -> GeneratedQuest:
        """Генерировать новый квест из доступных локаций."""
        item_name, item_id, base_price = random.choice(self.ITEM_TARGETS)
        backstory = random.choice(self.BACKSTORIES)
        reward = int(base_price * 2)  # 200% магазинной стоимости

        quest_id = f"q_collector_{self.completed_quests_count}"
        quest = GeneratedQuest(
            quest_id,
            f"Принести {item_name}",
            backstory,
            QuestType.COLLECT_ITEM,
            item_id,
            1,
            reward,
            100,
            self.id
        )
        return quest


class DragonSlayerChampion(NPC):
    """NPC #5 - Член клуба драконоборцев (только после открытия гор)."""

    def __init__(self):
        super().__init__(
            "npc_dragonslayer",
            "Райхан Золотой",
            "Чемпион драконоборцев",
            "Ветеран множества боёв с драконами, ищет наследника."
        )
        self.is_available = False

    def generate_quest(self) -> GeneratedQuest:
        """Генерировать единственный квест."""
        quest_id = "q_dragonslayer_final"
        quest = GeneratedQuest(
            quest_id,
            "Убить 10 драконов",
            ("Докажи, что ты достоин звания драконоборца! "
             "Убей 10 драконов и верни мне доказательство."),
            QuestType.KILL_ENEMIES,
            "дракон",
            10,
            1000,
            500,
            self.id
        )
        return quest


class NPCManager:
    """Менеджер NPC в таверне."""

    def __init__(self):
        """Инициализация менеджера NPC."""
        self.npcs: Dict[str, NPC] = {
            "npc_captain": CaptainGuard(),
            "npc_tracker": SwampTracker(),
            "npc_miner": CrazeMiner(),
            "npc_collector": CurioCollector(),
            "npc_dragonslayer": DragonSlayerChampion()
        }

    def get_available_npcs(self, location_available: bool = True) -> List[NPC]:
        """Получить доступных NPC."""
        if location_available:
            # Дракономорец доступен только если открыты горы
            return [
                self.npcs["npc_captain"],
                self.npcs["npc_tracker"],
                self.npcs["npc_miner"],
                self.npcs["npc_collector"],
                self.npcs["npc_dragonslayer"]
            ]
        else:
            return [
                self.npcs["npc_captain"],
                self.npcs["npc_tracker"],
                self.npcs["npc_miner"],
                self.npcs["npc_collector"]
            ]

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Получить NPC по ID."""
        return self.npcs.get(npc_id)

    def activate_dragonslayer(self) -> None:
        """Активировать NPC драконоборца (когда открыты горы)."""
        self.npcs["npc_dragonslayer"].is_available = True

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            npc_id: npc.to_dict()
            for npc_id, npc in self.npcs.items()
        }
