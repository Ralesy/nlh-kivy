#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Игровой персонаж: прогрессия, инвентарь, навыки и уведомления для UI.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.models.companion import Companion
from core.models.creature import Creature
from core.models.inventory import Inventory
from core.utils import clamp
from data.items import Armor, ItemDatabase, Weapon


class Player(Creature):
    """Игровой персонаж с инвентарём, навыками и системой событий."""

    BACKGROUNDS = {
        "noble": {
            "name": "Обедневший дворянин",
            "coins": 500,
            "weapon_id": "w_iron_dagger",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 3)],
        },
        "squire": {
            "name": "Оруженосец",
            "coins": 50,
            "weapon_id": "w_iron_sword",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 2)],
        },
        "hunter": {
            "name": "Охотник",
            "coins": 200,
            "weapon_id": "w_iron_bow",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 2)],
        },
    }

    BASE_STATS = {
        "health": 100,
        "damage": 10,
        "critical_chance": 0.05,
        "luck": 1.0,
        "selling_multiplier": 1.0,
    }

    STAT_COEFFICIENTS = {
        "endurance": {"health": 15},
        "strength": {"damage": 2, "inventory_capacity": 5},
        "agility": {"critical_chance": 0.05},
        "luck": {"luck": 0.15},
        "trade": {"selling_multiplier": 0.1},
        "speed": {"move_speed": 15},
    }

    BASE_MOVE_SPEED = 200

    STARTING_SKILL_POINTS = 5

    def __init__(self, name: str, background: str = "squire"):
        """Создать нового игрока с выбранным фоном."""
        if background not in self.BACKGROUNDS:
            background = "squire"

        bg = self.BACKGROUNDS[background]
        super().__init__(
            name,
            self.BASE_STATS["health"],
            self.BASE_STATS["damage"],
            bg["coins"],
            level=1,
        )

        self.background = background
        self.inventory = Inventory(capacity=20)

        self.skill_points_available = self.STARTING_SKILL_POINTS
        self.skill_points_allocated = {
            "endurance": 0,
            "strength": 0,
            "agility": 0,
            "luck": 0,
            "trade": 0,
            "speed": 0,
        }

        self._move_speed = self.BASE_MOVE_SPEED

        self._critical_chance = self.BASE_STATS["critical_chance"]
        self._luck = self.BASE_STATS["luck"]
        self._selling_multiplier = self.BASE_STATS["selling_multiplier"]
        self._listeners: List = []

        self.last_global_pos: Optional[Tuple[float, float]] = None

        ItemDatabase.initialize()
        if bg["weapon_id"]:
            starter_weapon = ItemDatabase.get(bg["weapon_id"])
            if starter_weapon:
                self.equip_weapon(starter_weapon)

        if bg["armor_id"]:
            starter_armor = ItemDatabase.get(bg["armor_id"])
            if starter_armor:
                self.equip_armor(starter_armor)

        if bg["starting_items"]:
            for item_id, qty in bg["starting_items"]:
                item = ItemDatabase.get(item_id)
                if item:
                    self.inventory.add(item, qty)

        self.experience = 0
        self.companions: List[Companion] = []
        self.accepted_quests: List = []
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.enemies_defeated = 0
        self.battles_fought = 0
        self.last_location_pos: Dict[str, Tuple[float, float]] = {}
        # Позиции и экземпляры врагов на боевых картах (сохраняются между визитами)
        self.last_enemy_positions: Dict[str, List[Tuple[float, float]]] = {}
        self.last_enemy_creatures: Dict[str, List[Optional[Creature]]] = {}
        self.defeated_bosses = set()

    def allocate_skill_point(self, skill: str) -> bool:
        """Распределить одно очко навыка. Возвращает True при успехе."""
        if skill not in self.skill_points_allocated:
            return False
        if self.skill_points_available <= 0:
            return False

        self.skill_points_allocated[skill] += 1
        self.skill_points_available -= 1
        self._recalculate_derived_stats()
        self.notify_listeners("stats_changed")
        return True

    def deallocate_skill_point(self, skill: str) -> bool:
        """Вернуть одно очко навыка. Возвращает True при успехе."""
        if skill not in self.skill_points_allocated:
            return False
        if self.skill_points_allocated[skill] <= 0:
            return False

        self.skill_points_allocated[skill] -= 1
        self.skill_points_available += 1
        self._recalculate_derived_stats()
        self.notify_listeners("stats_changed")
        return True

    def _recalculate_derived_stats(self) -> None:
        """Пересчитать производные характеристики после изменения навыков."""
        new_health = (
            self.BASE_STATS["health"]
            + self.skill_points_allocated["endurance"]
            * self.STAT_COEFFICIENTS["endurance"]["health"]
        )
        self.base_health = new_health
        self.max_health = self._scale_stat(self.base_health)
        if self.health > self.max_health:
            self.health = self.max_health

        new_damage = (
            self.BASE_STATS["damage"]
            + self.skill_points_allocated["strength"]
            * self.STAT_COEFFICIENTS["strength"]["damage"]
        )
        self.base_damage = new_damage

        new_capacity = (
            20
            + self.skill_points_allocated["strength"]
            * self.STAT_COEFFICIENTS["strength"]["inventory_capacity"]
        )
        self.inventory.capacity = max(1, int(new_capacity))

        self._critical_chance = (
            self.BASE_STATS["critical_chance"]
            + self.skill_points_allocated["agility"]
            * self.STAT_COEFFICIENTS["agility"]["critical_chance"]
        )
        self._luck = (
            self.BASE_STATS["luck"]
            + self.skill_points_allocated["luck"]
            * self.STAT_COEFFICIENTS["luck"]["luck"]
        )
        self._selling_multiplier = (
            self.BASE_STATS["selling_multiplier"]
            + self.skill_points_allocated["trade"]
            * self.STAT_COEFFICIENTS["trade"]["selling_multiplier"]
        )

        self._move_speed = (
            self.BASE_MOVE_SPEED
            + self.skill_points_allocated["speed"]
            * self.STAT_COEFFICIENTS["speed"]["move_speed"]
        )

    @property
    def critical_chance(self) -> float:
        """Шанс критического удара (0.0–1.0)."""
        return clamp(self._critical_chance, 0.0, 1.0)

    @property
    def luck(self) -> float:
        """Множитель качества лута."""
        return max(0.0, self._luck)

    @property
    def selling_multiplier(self) -> float:
        """Множитель цены при продаже."""
        return max(0.0, self._selling_multiplier)

    @property
    def move_speed(self) -> int:
        """Скорость передвижения персонажа по карте."""
        return max(self.BASE_MOVE_SPEED, int(self._move_speed))

    def add_listener(self, callback) -> None:
        """Подписать UI-колбэк на изменения состояния игрока."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        """Отписать колбэк."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self, event: str, **payload) -> None:
        """Оповестить подписчиков о событии (health, coins, level и т.д.)."""
        for callback in list(self._listeners):
            try:
                callback(event, **payload)
            except Exception:
                pass

    def equip_weapon(self, weapon: Weapon) -> bool:
        """
        Надеть оружие с учётом инвентаря.

        Returns:
            True, если экипировка прошла успешно.
        """
        if weapon is None:
            return False

        if self.weapon and self.weapon.id == weapon.id:
            return True

        if self.weapon and not self.inventory.has_space_for(1):
            return False

        in_inv_qty = self.inventory.qty(weapon.id)
        if in_inv_qty > 0:
            self.inventory.remove(weapon.id, 1)

        if self.weapon:
            prev = self.weapon
            prev.on_unequip(self)
            self.inventory.add(prev, 1)

        self.weapon = weapon
        weapon.on_equip(self)
        self.notify_listeners("stats_changed")
        return True

    def unequip_weapon(self) -> bool:
        """Снять оружие и вернуть в инвентарь, если есть место."""
        if not self.weapon:
            return True
        prev = self.weapon
        if self.inventory.has_space_for(1):
            prev.on_unequip(self)
            self.inventory.add(prev, 1)
            self.weapon = None
            self.notify_listeners("stats_changed")
            return True
        return False

    def equip_armor(self, armor: Armor) -> bool:
        """Надеть броню с учётом инвентаря."""
        if armor is None:
            return False

        if self.armor and self.armor.id == armor.id:
            return True

        if self.armor and not self.inventory.has_space_for(1):
            return False

        if self.inventory.qty(armor.id) > 0:
            self.inventory.remove(armor.id, 1)

        if self.armor:
            prev = self.armor
            prev.on_unequip(self)
            self.inventory.add(prev, 1)

        self.armor = armor
        armor.on_equip(self)
        self.notify_listeners("stats_changed")
        return True

    def unequip_armor(self) -> bool:
        """Снять броню и вернуть в инвентарь, если есть место."""
        if not self.armor:
            return True
        prev = self.armor
        if self.inventory.has_space_for(1):
            prev.on_unequip(self)
            self.inventory.add(prev, 1)
            self.armor = None
            self.notify_listeners("stats_changed")
            return True
        return False

    def add_experience(self, exp: int) -> List[str]:
        """Начислить опыт и обработать повышения уровня."""
        msgs: List[str] = []
        if exp <= 0:
            return msgs

        old_level = self.level
        old_exp = self.experience
        self.experience += exp
        msgs.append(f"+{exp} XP")

        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            self.max_health = self._scale_stat(self.base_health)
            self.base_damage = int(
                self.base_damage + (self.level - 1) * (self.base_damage * 0.05)
            )
            self.health = self.max_health
            self.skill_points_available += 1
            msgs.append(f"🎉 Уровень! {self.name} Lv {self.level}")
            msgs.append("📊 +1 очко для распределения")

        if old_exp != self.experience:
            self.notify_listeners("experience", old=old_exp, new=self.experience)
        if old_level != self.level:
            self.notify_listeners("level", old=old_level, new=self.level)

        return msgs

    def spend_coins(self, amount: int) -> bool:
        """
        Потратить монеты, если хватает баланса.

        Returns:
            True при успешной трате.
        """
        amount = int(amount)
        if amount <= 0 or self.coins < amount:
            return False
        self.coins -= amount
        return True

    def attack(self, target: Creature) -> Tuple[int, int]:
        """Атаковать цель. Возвращает (фактический урон, сырой урон)."""
        raw = self.damage
        dealt = target.take_damage(raw)
        self.total_damage_dealt += dealt
        return dealt, raw

    def use_item(self, item_id: str, battlefield=None) -> str:
        """Использовать предмет из инвентаря."""
        item = self.inventory.get(item_id)
        if not item:
            return "У тебя нет такого предмета."
        msg = item.use(self, battlefield)
        if item.is_consumable():
            self.inventory.remove(item_id, 1)
        return msg

    def buy(self, shop, item_id: str, qty: int = 1) -> str:
        """Купить предмет в магазине."""
        return shop.buy(self, item_id, qty)

    def sell(self, shop, item_id: str, qty: int = 1) -> str:
        """Продать предмет в магазине."""
        return shop.sell(self, item_id, qty)

    def get_session_stats(self) -> dict:
        """Собрать статистику текущей сессии."""
        return {
            "name": self.name,
            "class": self.background,
            "level": self.level,
            "experience": self.experience,
            "coins": self.coins,
            "total_damage_dealt": self.total_damage_dealt,
            "total_damage_taken": self.total_damage_taken,
            "enemies_defeated": self.enemies_defeated,
            "battles_fought": self.battles_fought,
            "inventory_items": sum(q for _, q in self.inventory.list_items()),
        }

    def add_loot(self, enemy_loot: str, enemy_loot_quantity: int) -> bool:
        """
        Добавить лут в инвентарь.

        Raises:
            ValueError: при некорректном ID или количестве.
        """
        if not isinstance(enemy_loot, str) or not enemy_loot.strip():
            raise ValueError("enemy_loot должен быть непустым ID предмета.")
        if not isinstance(enemy_loot_quantity, int) or enemy_loot_quantity <= 0:
            raise ValueError("enemy_loot_quantity должен быть положительным целым.")

        if not self.inventory.has_space_for(enemy_loot_quantity):
            return False

        item = ItemDatabase.get(enemy_loot)
        if item is None:
            return False
        return self.inventory.add(item, enemy_loot_quantity)

    @property
    def coins(self) -> int:
        """Текущий баланс монет."""
        return super().coins

    @coins.setter
    def coins(self, value: int) -> None:
        """Установить монеты с clamp >= 0 и уведомлением UI."""
        old = super().coins
        clamped = max(0, int(value))
        self._coins = clamped
        if old != clamped:
            self.notify_listeners("coins", old=old, new=clamped)

    @property
    def health(self) -> int:
        """Текущее здоровье."""
        return super().health

    @health.setter
    def health(self, value: int) -> None:
        """Установить здоровье с clamp и уведомлением UI."""
        old = super().health
        clamped = int(clamp(value, 0, self.max_health))
        self._health = clamped
        if old != clamped:
            self.notify_listeners("health", old=old, new=clamped)

    def update_quest_progress(self, enemy_name: str) -> None:
        """Обновить прогресс активных квестов на убийство."""
        for quest in self.accepted_quests:
            quest.update_progress(enemy_name)

    def to_dict(self) -> dict:
        """Сериализация для сохранения."""
        data = super().to_dict()
        data["type"] = "player"
        data["background"] = self.background
        data["inventory"] = self.inventory.to_dict()
        data["experience"] = self.experience
        data["skill_points_available"] = self.skill_points_available
        data["skill_points_allocated"] = self.skill_points_allocated
        data["companions"] = [c.to_dict() for c in self.companions]
        data["accepted_quests"] = [quest.to_dict() for quest in self.accepted_quests]
        data["session_stats"] = self.get_session_stats()
        data["last_location_pos"] = self.last_location_pos
        data["last_global_pos"] = (
            list(self.last_global_pos) if self.last_global_pos else None
        )
        data["last_enemy_positions"] = {
            scene_id: [list(pos) for pos in positions]
            for scene_id, positions in self.last_enemy_positions.items()
        }
        data["last_enemy_creatures"] = {
            scene_id: [creature.to_dict() if creature else None for creature in creatures]
            for scene_id, creatures in self.last_enemy_creatures.items()
        }
        data["defeated_bosses"] = list(self.defeated_bosses)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Player:
        """Восстановить игрока из сохранения."""
        background = data.get("background", "squire")
        player = cls(data["name"], background)

        player.level = data["level"]
        player.base_health = data["base_health"]
        player.base_damage = data["base_damage"]
        player.base_coins = data["base_coins"]
        player.health = data["health"]
        player.coins = data["coins"]
        player.experience = data.get("experience", 0)

        if "skill_points_allocated" in data:
            player.skill_points_allocated = data["skill_points_allocated"]
            player.skill_points_available = data.get("skill_points_available", 0)
            player._recalculate_derived_stats()

        player.max_health = player._scale_stat(player.base_health)
        player.base_damage = int(
            player.base_damage
            + (player.level - 1) * (player.base_damage * 0.05)
        )

        if "inventory" in data:
            ItemDatabase.initialize()
            player.inventory = Inventory.from_dict(data["inventory"])

        if data.get("weapon_id"):
            weapon = ItemDatabase.get(data["weapon_id"])
            if weapon:
                player.equip_weapon(weapon)

        if data.get("armor_id"):
            armor = ItemDatabase.get(data["armor_id"])
            if armor:
                player.equip_armor(armor)

        if "companions" in data:
            player.companions = [
                Companion.from_dict(c) for c in data["companions"]
            ]

        if "accepted_quests" in data:
            player.accepted_quests = []

        player.last_location_pos = {
            scene_id: tuple(pos)
            for scene_id, pos in data.get("last_location_pos", {}).items()
        }
        gp = data.get("last_global_pos")
        player.last_global_pos = tuple(gp) if gp else None
        player.last_enemy_positions = {
            scene_id: [tuple(pos) for pos in positions]
            for scene_id, positions in data.get("last_enemy_positions", {}).items()
        }
        player.last_enemy_creatures = {}
        for scene_id, creatures in data.get("last_enemy_creatures", {}).items():
            restored: List[Optional[Creature]] = []
            for creature_data in creatures:
                if creature_data is None:
                    restored.append(None)
                else:
                    restored.append(Creature.from_dict(creature_data))
            player.last_enemy_creatures[scene_id] = restored
        player.defeated_bosses = set(data.get("defeated_bosses", []))

        return player


class TestPlayer(Player):
    """Тестовый игрок с усиленными характеристиками для QA и отладки."""

    def __init__(self, name: str):
        """Создать персонажа с максимальным снаряжением для тестов."""
        ItemDatabase.initialize()
        super().__init__(name, "squire")

        self.base_health = 1000
        self.base_damage = 1000
        self.max_health = self._scale_stat(self.base_health)
        self.health = self.max_health
        self.coins = 10000

        self.inventory = Inventory(capacity=20)

        test_weapon = ItemDatabase.get("w_dragon_sword")
        if test_weapon:
            self.equip_weapon(test_weapon)

        test_armor = ItemDatabase.get("a_dragon_lord_plate")
        if test_armor:
            self.equip_armor(test_armor)

        test_potion = ItemDatabase.get("p_mega")
        if test_potion:
            self.inventory.add(test_potion, 19)
