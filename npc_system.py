#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NPC System: система NPC с диалогами и генерацией квестов.
"""

import random
from typing import Dict, List, Optional
from items import ItemDatabase, Weapon, Armor
from quests import Quest


class NPC:
    """Базовый класс NPC."""

    def __init__(self, name: str, quest_type: str, description: str, backstory: str):
        self.name = name
        self.quest_type = quest_type
        self.description = description
        self.backstory = backstory
        self.dialogue_intro = ""
        self.dialogue_quest_explanation = ""
        self.dialogue_quest_complete = ""
        self.dialogue_new_quest = ""
        self.dialogue_no_quest = ""
        self.available_quests: List[Quest] = []
        self.completed_quests_count = 0

    def generate_quest(self, player_level: int = 1) -> Quest:
        """Генерация нового квеста."""
        raise NotImplementedError

    def get_greeting_dialogue(self) -> str:
        """Получение приветственного диалога."""
        return self.dialogue_intro

    def get_quest_dialogue(self, quest: Quest) -> Dict[str, str]:
        """Получение диалогов для квеста."""
        return {
            "backstory": self.backstory,
            "explanation": self.dialogue_quest_explanation,
            "quest_details": quest.description,
            "accept": f"Отлично! Принимай задание: {quest.description}",
            "decline": "Как хочешь. Если передумаешь - возвращайся.",
            "complete": self.dialogue_quest_complete,
            "new_quest": self.dialogue_new_quest,
            "no_quest": self.dialogue_no_quest
        }

    def has_available_quest(self) -> bool:
        """Проверка наличия доступного квеста."""
        return len(self.available_quests) > 0

    def get_current_quest(self) -> Optional[Quest]:
        """Получение текущего активного квеста."""
        for quest in self.available_quests:
            if quest.status == "active":
                return quest
        return None

    def offer_quest(self, player_level: int = 1) -> Optional[Quest]:
        """Предложение квеста игроку."""
        if not self.has_available_quest():
            # Генерируем новый квест
            new_quest = self.generate_quest(player_level)
            self.available_quests.append(new_quest)
            return new_quest
        return None

    def accept_quest(self, quest: Quest) -> bool:
        """Принятие квеста игроком."""
        if quest in self.available_quests and quest.status == "not_taken":
            quest.status = "active"
            return True
        return False

    def complete_quest(self, quest: Quest) -> bool:
        """Завершение квеста."""
        if quest in self.available_quests and quest.status == "completed":
            quest.status = "claimed"
            self.completed_quests_count += 1
            # Удаляем завершенный квест и генерируем новый
            self.available_quests.remove(quest)
            return True
        return False

    def check_quest_progress(self, quest: Quest) -> None:
        """Проверка прогресса квеста."""
        if quest.status == "active" and quest.complete and not quest.claimed:
            quest.status = "completed"


class CityGuardCaptain(NPC):
    """Капитан городской стражи - квесты на убийство лесных врагов."""

    def __init__(self):
        super().__init__(
            "Капитан Стражи Рорик",
            "kill_forest_enemies",
            "Опытный офицер в потрёпанной кольчуге, с лицом, изборождённым шрамами от множества битв",
            "Я служу этому городу уже 25 лет. Начинал простым стражником, а теперь командую всей городской охраной. "
            "Видел, как орки пытались штурмовать стены, как драконы сжигали кварталы, как банды мародёров грабили "
            "караваны. Но хуже всего - это бесконечная война с лесными бандитами и дикими зверями. Каждый год они "
            "становятся наглее, а мои люди - уставшими. Если не остановить их сейчас, город может пасть."
        )

        self.dialogue_intro = (
            "Хм, ещё один 'герой'? Ладно, слушай внимательно. Я - капитан Рорик, командую городской стражей уже "
            "четверть века. За это время я похоронил больше друзей, чем ты, наверное, повстречал. Лес вокруг города "
            "кишит бандитами, дезертирами и всякой нечистью. Они грабят караваны, нападают на фермеров, "
            "иногда даже осмеливаются подбираться к городским стенам."
        )

        self.dialogue_quest_explanation = (
            "Вот что я предлагаю: отправляйся в лес и разберись с этими мерзавцами. Не просто убей кого-нибудь, "
            "а нанеси им такой удар, чтобы они надолго запомнили. Я дам тебе точные указания и награжу за работу."
        )

        self.dialogue_quest_complete = (
            "Ха! Вернулся живым? Отлично! Город стал чуть безопаснее благодаря таким как ты. "
            "Вот твоя награда - честно заработанная. И помни: каждый убитый бандит - это спасённая жизнь."
        )

        self.dialogue_new_quest = (
            "Опять проблемы... Эти твари никогда не унимаются. Нужна твоя помощь, и на этот раз дело серьёзное!"
        )

        self.dialogue_no_quest = (
            "Сейчас у меня нет срочных заданий. Но это не значит, что ситуация спокойная. "
            "Возвращайся позже - работа всегда найдётся."
        )

    def generate_quest(self, player_level: int = 1) -> Quest:
        """Генерация квеста на убийство лесных врагов."""
        enemies = ["Волк", "Мародёр", "Бандит", "Дезертир", "Лесной разбойник"]
        enemy_type = random.choice(enemies)

        # Базовая сложность в зависимости от уровня игрока
        base_count = max(3, min(12, player_level * 2))
        count = random.randint(max(3, base_count - 2), min(12, base_count + 3))

        quest_id = f"guard_kill_{enemy_type.lower().replace(' ', '_')}_{random.randint(1000, 9999)}"

        # Награда в зависимости от типа врага
        enemy_rewards = {
            "Волк": (count * 8, count * 12),
            "Мародёр": (count * 12, count * 18),
            "Бандит": (count * 15, count * 22),
            "Дезертир": (count * 18, count * 25),
            "Лесной разбойник": (count * 20, count * 28)
        }

        reward_coins, reward_xp = enemy_rewards.get(enemy_type, (count * 10, count * 15))

        # Иногда добавляем предметы
        reward_items = []
        if random.random() < 0.3:  # 30% шанс на предмет
            possible_items = ["p_small", "p_med", "a_leather", "w_short"]
            reward_items = [random.choice(possible_items)]

        return Quest(
            id_=quest_id,
            description=f"Убить {count} {enemy_type}{'ов' if count > 1 else 'а'} в Криволесье",
            quest_type=self.quest_type,
            target_enemy_type=enemy_type,
            target_count=count,
            progress={enemy_type: 0},
            goal={enemy_type: count},
            reward_coins=reward_coins,
            reward_xp=reward_xp,
            reward_items=reward_items
        )


class VillageElder(NPC):
    """Староста деревни - квесты на сбор ресурсов и помощь жителям."""

    def __init__(self):
        super().__init__(
            "Староста Элдрин",
            "village_help",
            "Пожилой мужчина с седой бородой и мудрыми глазами, одетый в простую крестьянскую одежду",
            "Я родился в этой деревне 60 лет назад. Видел, как она росла от маленького поселения до цветущего места. "
            "Но жизнь здесь нелегка - дикие звери, разбойники, болезни... Мои дети выросли и разъехались кто куда, "
            "внуки редко навещают. А деревня нуждается в защите. Каждый год становится всё тяжелее собирать урожай, "
            "защищать стада от волков, лечить больных. Иногда я думаю, что без помощи извне мы просто не выживем."
        )

        self.dialogue_intro = (
            "Здравствуй, странник. Я - Элдрин, староста этой деревни вот уже 30 лет. "
            "За это время я похоронил больше друзей, чем ты можешь представить. "
            "Наша деревня - как маленький островок спокойствия посреди бурного моря опасностей. "
            "Но даже здесь проблемы находят нас."
        )

        self.dialogue_quest_explanation = (
            "У нас есть несколько проблем, с которыми ты мог бы помочь. Ничего героического - "
            "просто практическая помощь людям, которые кормят этот город своими трудами. "
            "За работу я заплачу честно, из наших скромных сбережений."
        )

        self.dialogue_quest_complete = (
            "Спасибо тебе, добрый человек. Деревня не забудет твоей помощи. "
            "Возьми эту скромную награду - она заработана честным трудом."
        )

        self.dialogue_new_quest = (
            "Опять беда... Не знаю, сколько ещё мы сможем выдержать. "
            "Твоя помощь сейчас очень нужна!"
        )

        self.dialogue_no_quest = (
            "Сейчас у нас всё относительно спокойно. Но жизнь в деревне непредсказуема - "
            "возвращайся через несколько дней, и работа обязательно найдётся."
        )

    def generate_quest(self, player_level: int = 1) -> Quest:
        """Генерация квеста на помощь деревне."""
        quest_types = [
            ("волков", "убить", "Волк"),
            ("медведей", "убить", "Бурый медведь"),
            ("разбойников", "прогнать", "Бандит"),
            ("привидений", "изгнать", "Привидение")
        ]

        target_name, action, enemy_type = random.choice(quest_types)
        count = random.randint(2, 5)

        quest_id = f"village_help_{action}_{target_name}_{random.randint(1000, 9999)}"

        reward_coins = count * 15
        reward_xp = count * 20

        # Чаще даём предметы за помощь деревне
        reward_items = []
        if random.random() < 0.5:  # 50% шанс
            possible_items = ["p_small", "p_med", "a_leather", "w_short"]
            reward_items = [random.choice(possible_items)]

        return Quest(
            id_=quest_id,
            description=f"{action.capitalize()} {count} {target_name} возле деревни",
            quest_type=self.quest_type,
            target_enemy_type=enemy_type,
            target_count=count,
            progress={enemy_type: 0},
            goal={enemy_type: count},
            reward_coins=reward_coins,
            reward_xp=reward_xp,
            reward_items=reward_items
        )


class TravelingMerchant(NPC):
    """Странствующий торговец - квесты на доставку и поиск редких предметов."""

    def __init__(self):
        super().__init__(
            "Торговец Заратустра",
            "merchant_delivery",
            "Ярко одетый мужчина средних лет с острыми глазами и множеством колец на пальцах",
            "Я родом из далёких восточных земель, где песок жёлтый, а золото течёт рекой. "
            "Много лет назад я покинул родину в поисках богатства и приключений. "
            "За эти годы я объехал весь известный мир - от ледяных гор на севере до жарких пустынь на юге. "
            "Видел дворцы королей и хижины нищих, торговал с эльфами и орками, перехитрял драконов и разбойников. "
            "Теперь я странствующий торговец, и моя жизнь - это постоянное движение, новые лица и сделки."
        )

        self.dialogue_intro = (
            "Ах, ещё один искатель фортуны! Я - Заратустра, странствующий торговец из далёких земель. "
            "Мои караваны ходят по всему миру, а мои товары - самые редкие и ценные. "
            "Но торговля - это не только продажа, но и связи, информация, сделки..."
        )

        self.dialogue_quest_explanation = (
            "У меня есть небольшое поручение. Ничего опасного, просто нужно доставить посылку "
            "или найти редкий предмет. За работу я заплачу щедро - у меня всегда есть золото для тех, "
            "кто оказывает услуги."
        )

        self.dialogue_quest_complete = (
            "Отлично! Ты справился с заданием. Вот твоя награда, и знай - "
            "если тебе понадобятся редкие товары, я всегда рад сделке."
        )

        self.dialogue_new_quest = (
            "У меня появилось новое дело! Если ты свободен, давай обсудим условия..."
        )

        self.dialogue_no_quest = (
            "Сейчас у меня нет срочных поручений. Но мир полон возможностей - "
            "может, скоро появится что-то интересное."
        )

    def generate_quest(self, player_level: int = 1) -> Quest:
        """Генерация торгового квеста."""
        quest_types = [
            ("волков", "убить", "Волк"),
            ("медведей", "убить", "Бурый медведь"),
            ("троллей", "убить", "Тролль"),
            ("призраков", "изгнать", "Призрачный рыцарь")
        ]

        target_name, action, enemy_type = random.choice(quest_types)
        count = random.randint(1, 3)  # Торговые квесты обычно легче

        quest_id = f"merchant_{action}_{target_name}_{random.randint(1000, 9999)}"

        reward_coins = count * 25  # Торговец платит лучше
        reward_xp = count * 15

        # Высокий шанс на ценные предметы
        reward_items = []
        if random.random() < 0.7:  # 70% шанс
            possible_items = ["p_med", "p_large", "a_chain", "w_sword", "w_staff"]
            reward_items = [random.choice(possible_items)]

        return Quest(
            id_=quest_id,
            description=f"{action.capitalize()} {count} {target_name} для торгового каравана",
            quest_type=self.quest_type,
            target_enemy_type=enemy_type,
            target_count=count,
            progress={enemy_type: 0},
            goal={enemy_type: count},
            reward_coins=reward_coins,
            reward_xp=reward_xp,
            reward_items=reward_items
        )


class DragonHunter(NPC):
    """Охотник на драконов - появляется после открытия гор."""

    def __init__(self):
        super().__init__(
            "Охотник на Драконов Геральт",
            "dragon_hunting",
            "Могучий воин в потрёпанной броне, с огромным мечом за спиной и множеством шрамов",
            "Меня называют Геральт, но это не моё настоящее имя. Я родился в маленькой деревне на окраине королевства, "
            "но с детства мечтал о славе и богатстве. В 16 лет я убил первого дракона - маленького лесного змея, "
            "и с тех пор охота на этих тварей стала моей жизнью. Я видел, как драконы сжигали города, как они "
            "накапливали сокровища в своих пещерах, как они уничтожали целые армии. Но я также знаю их слабости. "
            "За 20 лет охоты я убил 47 драконов разных видов и размеров. Каждый из них был битвой не на жизнь, "
            "а на смерть. И каждый раз я возвращался победителем."
        )

        self.dialogue_intro = (
            "Ха! Ещё один 'герой', который думает, что может убить дракона? Ладно, слушай внимательно. "
            "Я - Геральт, лучший охотник на драконов в этом королевстве. За моей спиной 47 убитых тварей, "
            "и каждая из них могла бы стереть тебя в порошок одним дыханием. Но я вижу в твоих глазах "
            "ту же жажду славы, что была у меня в юности."
        )

        self.dialogue_quest_explanation = (
            "Драконы - это не просто большие ящерицы с крыльями. Это древние существа, полные магии и злобы. "
            "Убить дракона - значит не только победить в бою, но и перехитрить его, использовать его слабости. "
            "Я научу тебя основам, дам точные указания. Но помни: один неверный шаг - и ты станешь пеплом."
        )

        self.dialogue_quest_complete = (
            "Невероятно! Ты действительно сделал это? Ха-ха-ха! Ты только что вошёл в легенды, "
            "мой друг. Вот твоя награда - самая щедрая из тех, что я когда-либо давал. "
            "И знай: теперь ты - настоящий охотник на драконов!"
        )

        self.dialogue_new_quest = (
            "Появилась новая цель! Настоящий монстр, достойный легенды. "
            "Если ты готов к самому опасному испытанию в своей жизни - слушай внимательно..."
        )

        self.dialogue_no_quest = (
            "Сейчас нет достойных целей. Драконы не появляются по заказу. "
            "Но если ты действительно хочешь стать легендой - тренируйся, набирайся опыта. "
            "Я буду следить за твоими успехами."
        )

    def generate_quest(self, player_level: int = 1) -> Quest:
        """Генерация квеста на охоту за драконами."""
        if player_level < 15:
            # Для низких уровней - более лёгкие драконы
            dragons = ["Молодой дракон", "Лесной змей", "Горный ящер"]
            enemy_type = random.choice(dragons)
            count = 1
            reward_coins = 100
            reward_xp = 100
        else:
            # Для высоких уровней - настоящие драконы
            dragons = ["Дракон", "Огненный дракон", "Ледяной дракон"]
            enemy_type = random.choice(dragons)
            count = 1
            reward_coins = 200
            reward_xp = 150

        quest_id = f"dragon_hunt_{enemy_type.lower().replace(' ', '_')}_{random.randint(1000, 9999)}"

        # Драконы всегда дают ценные награды
        reward_items = []
        epic_items = ["w_great_sword", "a_plate", "a_epic", "w_legend", "a_legend"]
        reward_items = [random.choice(epic_items)]

        return Quest(
            id_=quest_id,
            description=f"Убить {enemy_type}{'а' if 'дракон' in enemy_type.lower() else ''} в горах",
            quest_type=self.quest_type,
            target_enemy_type=enemy_type,
            target_count=count,
            progress={enemy_type: 0},
            goal={enemy_type: count},
            reward_coins=reward_coins,
            reward_xp=reward_xp,
            reward_items=reward_items
        )


class NPCSystem:
    """Система управления NPC."""

    def __init__(self):
        self.npcs: Dict[str, NPC] = {}
        self._initialize_npcs()

    def _initialize_npcs(self):
        """Инициализация всех NPC."""
        self.npcs["city_guard"] = CityGuardCaptain()
        self.npcs["village_elder"] = VillageElder()
        self.npcs["traveling_merchant"] = TravelingMerchant()
        self.npcs["dragon_hunter"] = DragonHunter()

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Получение NPC по ID."""
        return self.npcs.get(npc_id)

    def get_available_npcs(self) -> List[str]:
        """Получение списка доступных NPC."""
        return list(self.npcs.keys())

    def get_random_quest_giver(self) -> Optional[NPC]:
        """Получение случайного NPC, который может дать квест."""
        available = [npc for npc in self.npcs.values() if not npc.has_available_quest()]
        if available:
            return random.choice(available)
        return None
