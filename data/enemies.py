#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enemies: система врагов с новой системой дропа лута.
"""

from typing import List, Optional, Tuple
import random


class Enemy:
    """Описание врага для дропа."""

    def __init__(
        self,
        id_: str,
        name: str,
        enemy_type: str,
        base_health: int,
        base_damage: int,
        base_coins: int,
        xp_reward: int = 0,
        loot_table: Optional[List[Tuple[str, float]]] = None,
        is_boss: bool = False
    ):
        self.id = id_
        self.name = name
        self.enemy_type = enemy_type  # animal, humanoid, boss
        self.base_health = base_health
        self.base_damage = base_damage
        self.base_coins = base_coins
        self.xp_reward = xp_reward
        self.loot_table = loot_table or []
        self.is_boss = is_boss

    def generate_loot(self, luck: float = 1.0) -> List[Tuple[str, int]]:
        """Генерировать лут при убийстве.

        :param luck: multiplicative luck factor from the player (1.0 = neutral).
        Luck increases the probability of rare drops and biases weighted
        selections toward higher-weighted items.
        """
        loot = []

        # Животные/монстры: теперь тоже могут дропать из loot_table
        if self.enemy_type == "animal":
            if self.loot_table:
                items = [item_id for item_id, _ in self.loot_table]
                base_chances = [chance for _, chance in self.loot_table]
                adj_chances = [max(0.0, c * luck) for c in base_chances]
                if random.random() < 0.4 * luck:
                    chosen_item = random.choices(items, weights=adj_chances, k=1)[0]
                    loot.append((chosen_item, 1))
            return loot

        # Гуманоиды: из своего таблицы дропа
        if self.enemy_type == "humanoid":
            if self.loot_table:
                # Apply luck as a multiplier to the weights: higher luck biases selection
                items = [item_id for item_id, _ in self.loot_table]
                base_chances = [chance for _, chance in self.loot_table]
                # Multiply weights by luck to bias toward better outcomes when luck>1
                adj_chances = [max(0.0, c * luck) for c in base_chances]
                chosen_item = random.choices(items, weights=adj_chances, k=1)[0]
                loot.append((chosen_item, 1))

            # Rare drop chance scales with luck (base 10%)
            rare_chance = 0.10 * luck
            if random.random() < rare_chance:
                # Выбираем случайный редкий предмет из доступных
                rare_items = [
                    "w_steel_sword", "w_steel_axe",
                    "w_orc_maul", "w_orc_sword",
                    "a_steel_plate", "a_orc_mail"
                ]
                # include staffs among rare drops
                rare_items.append("w_steel_staff")
                # Slight extra roll to avoid always granting rare item when luck is high
                if random.random() < 0.5:
                    loot.append((random.choice(rare_items), 1))

        # Боссы: специальный лут
        if self.is_boss:
            if self.loot_table:
                items = [item_id for item_id, _ in self.loot_table]
                chances = [chance for _, chance in self.loot_table]
                chosen_item = random.choices(items, weights=chances, k=1)[0]
                loot.append((chosen_item, 1))

        return loot


class EnemyDatabase:
    """База данных врагов."""

    ENEMIES: dict = {}

    @classmethod
    def register(cls, enemy: Enemy) -> None:
        """Регистрация врага."""
        cls.ENEMIES[enemy.id] = enemy

    @classmethod
    def get(cls, enemy_id: str) -> Optional[Enemy]:
        """Получить врага по ID."""
        return cls.ENEMIES.get(enemy_id)

    @classmethod
    def get_by_location(cls, location_id: str) -> List[Enemy]:
        """Получить врагов локации."""
        location_enemies = []
        for enemy_id, enemy in cls.ENEMIES.items():
            if enemy_id.startswith(f"enemy_{location_id}_"):
                location_enemies.append(enemy)
        return location_enemies

    @classmethod
    def initialize(cls) -> None:
        """Инициализация врагов."""

        # === ЛЕС "КРИВОЛЕСЬЕ" ===

        # Волки (животные - только опыт+деньги)
        cls.register(Enemy(
            "enemy_forest_wolf", "Волк", "animal",
            base_health=30, base_damage=8, base_coins=8,
            xp_reward=50,
            loot_table=[
                ("p_small", 0.3),
            ],
        ))

        # Мародёры (гуманоиды - трепьё + железное оружие)
        cls.register(Enemy(
            "enemy_forest_raider", "Мародёр", "humanoid",
            base_health=50, base_damage=12, base_coins=16,
            xp_reward=75,
            loot_table=[
                ("a_rags_leather", 0.8),
                ("w_iron_sword", 0.35),
                ("w_iron_axe", 0.35),
                ("w_iron_spear", 0.25),
                ("w_iron_bow", 0.2),
                ("w_iron_staff", 0.15)
            ]
        ))

        # Бандиты (гуманоиды - кожаная броня + железное оружие)
        cls.register(Enemy(
            "enemy_forest_bandit", "Бандит", "humanoid",
            base_health=45, base_damage=11, base_coins=20,
            xp_reward=80,
            loot_table=[
                ("a_leather_armor", 0.7),
                ("w_iron_sword", 0.35),
                ("w_iron_axe", 0.35),
                ("w_iron_dagger", 0.25),
                ("w_iron_bow", 0.2),
                ("w_iron_staff", 0.15)
            ]
        ))

        # Дезертиры (гуманоиды - стальное оружие + броня)
        cls.register(Enemy(
            "enemy_forest_deserter", "Дезертир", "humanoid",
            base_health=60, base_damage=14, base_coins=28,
            xp_reward=100,
            loot_table=[
                ("a_steel_plate", 0.5),
                ("w_steel_sword", 0.35),
                ("w_steel_axe", 0.35),
                ("w_steel_spear", 0.25),
                ("w_steel_dagger", 0.2),
                ("w_steel_bow", 0.15),
                ("w_steel_staff", 0.12)
            ]
        ))

        # Лесной разведчик
        cls.register(Enemy(
            "enemy_forest_scout", "Лесной разведчик", "humanoid",
            base_health=35, base_damage=9, base_coins=12,
            xp_reward=60,
        ))

        # === БОЛОТА "ГНИЮЩИЕ ТОПИ" ===

        # Гоблины (гуманоиды - гоблинское оружие)
        cls.register(Enemy(
            "enemy_swamp_goblin", "Гоблин", "humanoid",
            base_health=40, base_damage=10, base_coins=18,
            xp_reward=70,
            loot_table=[
                ("w_goblin_dagger", 0.35),
                ("w_goblin_cleaver", 0.35),
                ("w_goblin_spear", 0.25),
                ("w_goblin_bow", 0.2),
                ("w_goblin_kris", 0.15),
                ("w_goblin_staff", 0.12)
            ]
        ))

        # Гигантские жабы (животные)
        cls.register(Enemy(
            "enemy_swamp_giant_toad", "Гигантская жаба", "animal",
            base_health=55, base_damage=13, base_coins=14,
            xp_reward=65,
            loot_table=[
                ("p_small", 0.4),
                ("p_med", 0.15),
            ],
        ))

        # Болотники (животные/гуманоиды - часто зелья и оружие)
        cls.register(Enemy(
            "enemy_swamp_bog_walker", "Болотник", "humanoid",
            base_health=48, base_damage=11, base_coins=20,
            xp_reward=75,
            loot_table=[
                ("p_small", 0.5),
                ("p_med", 0.2),
                ("w_goblin_spear", 0.25),
                ("w_goblin_bow", 0.15),
                ("w_goblin_staff", 0.12)
            ]
        ))

        # Гигантская жаба (синоним для глобальной карты)
        cls.register(Enemy(
            "enemy_swamp_toad", "Гигантская жаба", "animal",
            base_health=55, base_damage=13, base_coins=14,
            xp_reward=65,
            loot_table=[
                ("p_small", 0.4),
                ("p_med", 0.15),
            ],
        ))

        # Шаман болот
        cls.register(Enemy(
            "enemy_swamp_shamanic", "Шаман болот", "humanoid",
            base_health=50, base_damage=12, base_coins=22,
            xp_reward=80,
            loot_table=[
                ("w_goblin_staff", 0.5),
                ("p_small", 0.4),
                ("p_med", 0.2),
            ]
        ))

        # === ШАХТЫ "ПОДСКАЛЬНЫЕ ГРОТЫ" ===

        # Орки (гуманоиды - орчье оружие)
        cls.register(Enemy(
            "enemy_mines_orc", "Орк", "humanoid",
            base_health=70, base_damage=15, base_coins=32,
            xp_reward=120,
            loot_table=[
                ("w_orc_sword", 0.35),
                ("w_orc_maul", 0.35),
                ("w_orc_spear", 0.25),
                ("w_orc_bow", 0.2),
                ("w_orc_dagger", 0.15),
                ("w_orc_staff", 0.12)
            ]
        ))

        # Гномы-драугры (гуманоиды - гномье оружие)
        cls.register(Enemy(
            "enemy_mines_dwarven_draugr", "Гном-драугр", "humanoid",
            base_health=65, base_damage=16, base_coins=36,
            xp_reward=130,
            loot_table=[
                ("a_dwarf_plate", 0.3),
                ("w_dwarf_axe", 0.35),
                ("w_dwarf_sword", 0.35),
                ("w_dwarf_spear", 0.25),
                ("w_dwarf_dagger", 0.15),
                ("w_dwarf_staff", 0.12)
            ]
        ))

        # Скелеты (животные)
        cls.register(Enemy(
            "enemy_mines_skeleton", "Скелет", "animal",
            base_health=55, base_damage=12, base_coins=12,
            xp_reward=60,
            loot_table=[
                ("p_small", 0.3),
                ("w_iron_dagger", 0.15),
            ],
        ))

        # Крысиный Король (гуманоид)
        cls.register(Enemy(
            "enemy_mines_rat_king", "Крысиный Король", "humanoid",
            base_health=100, base_damage=18, base_coins=60,
            xp_reward=200,
            loot_table=[
                ("p_large", 0.4),
                ("w_orc_sword", 0.3),
                ("w_orc_maul", 0.25),
                ("w_orc_spear", 0.2),
                ("w_orc_dagger", 0.15)
            ]
        ))

        # Старый Камнежор (очень сильный)
        cls.register(Enemy(
            "enemy_mines_old_stonehammer",
            "Старый Камнежор", "humanoid",
            base_health=150, base_damage=22, base_coins=80,
            xp_reward=300,
            loot_table=[
                ("a_dwarf_plate", 0.5),
                ("p_large", 0.6),
                ("w_dwarf_sword", 0.35),
                ("w_dwarf_axe", 0.3),
                ("w_dwarf_spear", 0.25),
                ("w_dwarf_dagger", 0.15)
            ]
        ))

        # Драугр-шахтёр
        cls.register(Enemy(
            "enemy_mines_draugr", "Драугр-шахтёр", "humanoid",
            base_health=60, base_damage=14, base_coins=28,
            xp_reward=100,
            loot_table=[
                ("a_dwarf_plate", 0.2),
                ("w_dwarf_axe", 0.3),
                ("w_dwarf_sword", 0.3),
            ]
        ))

        # Каменный голем
        cls.register(Enemy(
            "enemy_mines_golem", "Каменный голем", "animal",
            base_health=80, base_damage=18, base_coins=20,
            xp_reward=110,
            loot_table=[
                ("p_small", 0.3),
                ("w_orc_maul", 0.2),
                ("a_iron_plate", 0.15),
            ],
        ))

        # Серый гремлин
        cls.register(Enemy(
            "enemy_mines_greyling", "Серый гремлин", "animal",
            base_health=40, base_damage=10, base_coins=10,
            xp_reward=50,
            loot_table=[
                ("p_small", 0.25),
                ("w_iron_dagger", 0.1),
            ],
        ))

        # === ГОРЫ "ХРЕБЕТ ДРАКОНОВ" ===

        # Безумные снеговики (животные)
        cls.register(Enemy(
            "enemy_mountains_mad_snowman", "Безумный снеговик",
            "animal",
            base_health=60, base_damage=13, base_coins=20,
            xp_reward=80,
            loot_table=[
                ("p_small", 0.35),
                ("p_med", 0.1),
            ],
        ))

        # Горные волки (животные)
        cls.register(Enemy(
            "enemy_mountains_mountain_wolf", "Горный волк", "animal",
            base_health=65, base_damage=15, base_coins=22,
            xp_reward=90,
            loot_table=[
                ("p_small", 0.35),
                ("w_iron_sword", 0.15),
            ],
        ))

        # Ледяные приведения (животные)
        cls.register(Enemy(
            "enemy_mountains_ice_specter", "Ледяное приведение",
            "animal",
            base_health=70, base_damage=16, base_coins=24,
            xp_reward=100,
            loot_table=[
                ("p_med", 0.25),
                ("w_steel_staff", 0.1),
            ],
        ))

        # Драконоборец-зомби (гуманоид)
        cls.register(Enemy(
            "enemy_mountains_dragonslayer_zombie",
            "Драконоборец-зомби", "humanoid",
            base_health=120, base_damage=20, base_coins=60,
            xp_reward=250,
            loot_table=[
                ("w_orc_maul", 0.5),
                ("a_steel_plate", 0.4),
                ("a_dwarf_plate", 0.3)
            ]
        ))

        # Драконы (животные)
        cls.register(Enemy(
            "enemy_mountains_dragon", "Дракон", "animal",
            base_health=200, base_damage=25, base_coins=120,
            xp_reward=400,
            loot_table=[
                ("p_large", 0.5),
                ("w_dragon_sword", 0.05),
                ("a_dwarf_plate", 0.2),
            ],
        ))

        # Горный тролль
        cls.register(Enemy(
            "enemy_mountains_troll", "Горный тролль", "humanoid",
            base_health=100, base_damage=18, base_coins=40,
            xp_reward=150,
            loot_table=[
                ("w_orc_maul", 0.4),
                ("a_dwarf_plate", 0.25),
            ]
        ))

        # Ледяной призрак
        cls.register(Enemy(
            "enemy_mountains_specter", "Ледяной призрак", "animal",
            base_health=65, base_damage=14, base_coins=22,
            xp_reward=90,
            loot_table=[
                ("p_med", 0.25),
                ("w_steel_staff", 0.1),
            ],
        ))

        # Горный великан
        cls.register(Enemy(
            "enemy_mountains_giant", "Горный великан", "humanoid",
            base_health=150, base_damage=22, base_coins=60,
            xp_reward=200,
            loot_table=[
                ("w_orc_maul", 0.5),
                ("a_steel_plate", 0.3),
                ("a_orc_mail", 0.25),
            ]
        ))

        # Ледяной дракон
        cls.register(Enemy(
            "enemy_mountains_drake", "Ледяной дракон", "animal",
            base_health=180, base_damage=24, base_coins=100,
            xp_reward=350,
            loot_table=[
                ("p_large", 0.4),
                ("w_dragon_sword", 0.03),
                ("a_dwarf_plate", 0.15),
            ],
        ))

        # === БОССЫ В ПЕЩЕРЕ ДРЕВНИХ ===

        # Босс 1: Безумный мародёр
        cls.register(Enemy(
            "boss_1_mad_raider", "Безумный мародёр", "boss",
            base_health=200, base_damage=20, base_coins=200,
            xp_reward=1000,
            loot_table=[
                ("w_mad_raider_sword", 1.0)  # Меч безумного мародёра
            ],
            is_boss=True
        ))

        # Босс 2: Хозяин Болота
        cls.register(Enemy(
            "boss_2_bog_master", "Хозяин Болота", "boss",
            base_health=220, base_damage=18, base_coins=240,
            xp_reward=1100,
            loot_table=[
                ("w_bog_master_staff", 1.0)  # Посох Хозяина Болота
            ],
            is_boss=True
        ))

        # Босс 3: Король Шахт
        cls.register(Enemy(
            "boss_3_mine_king", "Король Шахт", "boss",
            base_health=250, base_damage=24, base_coins=280,
            xp_reward=1200,
            loot_table=[
                ("w_dwarf_king_hammer", 1.0)  # Молот короля гномов
            ],
            is_boss=True
        ))

        # Босс 4: Повелитель Драконов
        cls.register(Enemy(
            "boss_4_dragon_lord", "Повелитель Драконов", "boss",
            base_health=300, base_damage=28, base_coins=400,
            xp_reward=1500,
            loot_table=[
                ("a_dragon_lord_plate", 1.0)  # Доспех Повелителя Драконов
            ],
            is_boss=True
        ))

        # === ПЕЩЕРА ДРЕВНИХ (враги локации) ===

        # Враги пещеры - ссылки на боссов
        cls.register(Enemy(
            "enemy_ancient_cave_berserker", "Безумный мародёр", "boss",
            base_health=200, base_damage=20, base_coins=200,
            xp_reward=1000,
            loot_table=[
                ("w_mad_raider_sword", 1.0)
            ],
            is_boss=True
        ))

        cls.register(Enemy(
            "enemy_ancient_cave_bog_master", "Хозяин Болота", "boss",
            base_health=220, base_damage=18, base_coins=240,
            xp_reward=1100,
            loot_table=[
                ("w_bog_master_staff", 1.0)
            ],
            is_boss=True
        ))

        cls.register(Enemy(
            "enemy_ancient_cave_mine_king", "Король Шахт", "boss",
            base_health=250, base_damage=24, base_coins=280,
            xp_reward=1200,
            loot_table=[
                ("w_dwarf_king_hammer", 1.0)
            ],
            is_boss=True
        ))

        cls.register(Enemy(
            "enemy_ancient_cave_dragon_lord", "Повелитель Драконов",
            "boss",
            base_health=300, base_damage=28, base_coins=400,
            xp_reward=1500,
            loot_table=[
                ("a_dragon_lord_plate", 1.0)
            ],
            is_boss=True
        ))
