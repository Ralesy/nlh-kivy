#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creatures: система существ, персонажа и спутников.
"""

from typing import List, Optional, Tuple
from data.items import Weapon, Armor, Inventory, ItemDatabase
from core.utils import clamp


class Creature:
    """Базовый класс существа (враг, спутник, игрок)."""

    def __init__(
        self,
        name: str,
        base_health: int,
        base_damage: int,
        base_coins: int,
        level: int = 1
    ):
        self.name = name
        self.level = level
        self.base_health = base_health
        self.base_damage = base_damage
        self.base_coins = base_coins

        self.max_health = self._scale_stat(self.base_health)
        self._health = self.max_health
        self._coins = self.base_coins + (self.level - 1) * (
            self.base_coins // 2)
        self.temp_damage = 0
        self.temp_defense = 0
        self.weapon: Optional[Weapon] = None
        self.armor: Optional[Armor] = None
        self.cause_of_death: Optional[str] = None
        self._template = None  # For enemies: reference to Enemy template

    def _scale_stat(self, base: int) -> int:
        """Масштабирование характеристики по уровню."""
        return int(base + (self.level - 1) * (base * 0.12))

    @property
    def damage(self) -> int:
        """Итоговый урон."""
        return max(0, self.base_damage + self.temp_damage)

    @property
    def defense(self) -> int:
        """Итоговая защита."""
        return max(0, self.temp_defense)

    @property
    def is_alive(self) -> bool:
        """Жив ли персонаж."""
        return self.health > 0

    @property
    def health(self) -> int:
        return getattr(self, '_health', 0)

    @health.setter
    def health(self, value: int) -> None:
        self._health = value

    @property
    def base_xp(self) -> int:
        """XP за убийство (из шаблона врага или стандартный)."""
        if self._template:
            return self._template.xp_reward
        # Стандартный XP = (base_health * 0.5) + (base_damage * 0.8)
        return int(self.base_health * 0.5 + self.base_damage * 0.8)

    def generate_loot(self) -> Optional[List[Tuple[str, int]]]:
        """Генерировать лут при убийстве (если есть шаблон)."""
        if self._template:
            return self._template.generate_loot()
        return None

    def take_damage(self, dmg: int) -> int:
        """Получение урона."""
        if not self.is_alive:
            return 0
        effective = max(0, dmg - int(self.defense))
        self.health = max(0, self.health - effective)
        if self.health == 0:
            self.die("combat")
        return effective

    def heal(self, amount: int) -> int:
        """Восстановление здоровья."""
        if not self.is_alive:
            return 0
        old = self.health
        self.health = clamp(
            self.health + amount, 0, self.max_health
        )
        return self.health - old

    def die(self, cause: str = "combat") -> None:
        """Смерть персонажа."""
        self.cause_of_death = cause
        self.health = 0

    def equip_weapon(self, weapon: Weapon) -> None:
        """Надевание оружия."""
        if self.weapon:
            self.weapon.on_unequip(self)
        self.weapon = weapon
        weapon.on_equip(self)

    def unequip_weapon(self) -> None:
        """Снятие оружия."""
        if self.weapon:
            self.weapon.on_unequip(self)
            self.weapon = None

    def equip_armor(self, armor: Armor) -> None:
        """Надевание брони."""
        if self.armor:
            self.armor.on_unequip(self)
        self.armor = armor
        armor.on_equip(self)

    def unequip_armor(self) -> None:
        """Снятие брони."""
        if self.armor:
            self.armor.on_unequip(self)
            self.armor = None

    def description(self) -> str:
        """Описание статуса персонажа."""
        eq = []
        if self.weapon:
            dmg_bonus = (self.weapon.damage_bonus
                         if hasattr(self.weapon, 'damage_bonus')
                         else self.weapon.base_damage)
            eq.append(
                f"Weapon:{self.weapon.name}(+{dmg_bonus})"
            )
        if self.armor:
            def_bonus = (self.armor.defense
                         if hasattr(self.armor, 'defense')
                         else self.armor.base_defense)
            eq.append(f"Armor:{self.armor.name}(+{def_bonus})")
        eqs = "; ".join(eq) if eq else "No gear"
        return (f"{self.name} (Lv{self.level}) HP:{self.health}/"
                f"{self.max_health} DMG:{self.damage} DEF:{self.defense} "
                f"| {eqs}")

    @property
    def coins(self) -> int:
        return getattr(self, '_coins', 0)

    @coins.setter
    def coins(self, value: int) -> None:
        self._coins = value

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "name": self.name,
            "level": self.level,
            "base_health": self.base_health,
            "base_damage": self.base_damage,
            "base_coins": self.base_coins,
            "health": self.health,
            "coins": self.coins,
            "weapon_id": self.weapon.id if self.weapon else None,
            "armor_id": self.armor.id if self.armor else None
        }


class Companion(Creature):
    """Нанятый спутник."""

    ROLES = {
        "tank": {"hp": 50, "dmg": 3, "coins": 30,
                 "name": "Танк"},  # Ослаблено в 3 раза
        "archer": {"hp": 37, "dmg": 4, "coins": 30,
                   "name": "Лучник"},  # Ослаблено в 3 раза
        "healer": {"hp": 33, "dmg": 2, "coins": 35,
                   "name": "Целитель"}  # Ослаблено в 3 раза
    }

    def __init__(
        self,
        name: str,
        role: str,
        level: int = 1
    ):
        if role not in self.ROLES:
            role = "archer"
        r = self.ROLES[role]
        super().__init__(name, r["hp"], r["dmg"], r["coins"], level)
        self.role = role

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["role"] = self.role
        data["type"] = "companion"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Companion':
        """Загрузка из словаря."""
        companion = cls(data["name"], data["role"], data["level"])
        companion.health = data["health"]
        companion.max_health = companion._scale_stat(companion.base_health)
        companion.coins = data["coins"]
        companion.temp_damage = 0
        companion.temp_defense = 0

        # Восстанавливаем экипировку
        if data.get("weapon_id"):
            from data.items import ItemDatabase
            ItemDatabase.initialize()
            weapon = ItemDatabase.get(data["weapon_id"])
            if weapon:
                companion.equip_weapon(weapon)

        if data.get("armor_id"):
            armor = ItemDatabase.get(data["armor_id"])
            if armor:
                companion.equip_armor(armor)

        return companion


class Player(Creature):
    """Игровой персонаж."""

    CLASS_STATS = {
        "warrior": {"hp": 140, "dmg": 12, "coins": 80,
                    "name": "Воин"},
        "mage": {"hp": 100, "dmg": 16, "coins": 60,
                 "name": "Маг"},
        "archer": {"hp": 120, "dmg": 11, "coins": 70,
                   "name": "Лучник"}
    }

    def __init__(self, name: str, cls: str):
        if cls not in self.CLASS_STATS:
            cls = "warrior"
        stats = self.CLASS_STATS[cls]
        super().__init__(
            name,
            stats["hp"],
            stats["dmg"],
            stats["coins"],
            level=1
        )
        self.cls = cls
        self.inventory = Inventory(capacity=20)

        # Стартовое оборудование
        starter_w = ItemDatabase.get("w_iron_sword")
        starter_a = ItemDatabase.get("a_leather_armor")
        if starter_w:
            self.equip_weapon(starter_w)
        if starter_a:
            self.equip_armor(starter_a)

        # Стартовые зелья
        self.inventory.add(ItemDatabase.get("p_small"), 2)

        self.experience = 0
        self.companions: List[Companion] = []
        self.accepted_quests: List = []  # List of accepted quests
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.enemies_defeated = 0
        self.battles_fought = 0
        # --- Observer/listener support for event-driven UI updates ---
        # Listeners receive calls like: callback(event_name: str, **kwargs)
        self._listeners = []

    # Listener management
    def add_listener(self, callback):
        try:
            if callback not in self._listeners:
                self._listeners.append(callback)
        except Exception:
            pass

    def remove_listener(self, callback):
        try:
            if callback in self._listeners:
                self._listeners.remove(callback)
        except Exception:
            pass

    def notify_listeners(self, event: str, **payload):
        for cb in list(getattr(self, '_listeners', [])):
            try:
                cb(event, **payload)
            except Exception:
                pass

    # ===== Equipment management with inventory integration =====
    def equip_weapon(self, weapon: Weapon) -> bool:
        """Equip weapon and update inventory.

        If the weapon is present in the player's inventory, remove one copy
        from inventory when equipping. The previously equipped weapon is
        returned to the inventory (if there is space). If there isn't room
        to store the previous weapon, the equip is cancelled.
        Returns True when equip succeeded, False otherwise.
        """
        if weapon is None:
            return False

        # do nothing if same weapon
        if self.weapon and self.weapon.id == weapon.id:
            return True

        # Check if previous weapon can be stored (if any)
        if self.weapon:
            if not self.inventory.has_space_for(1):
                return False

        # Remove new weapon from inventory if it exists there
        try:
            in_inv_qty = self.inventory.qty(weapon.id)
        except Exception:
            in_inv_qty = 0

        if in_inv_qty > 0:
            self.inventory.remove(weapon.id, 1)

        # Move previous weapon to inventory
        if self.weapon:
            prev = self.weapon
            prev.on_unequip(self)
            # add previous back to inventory (we checked space)
            self.inventory.add(prev, 1)

        # Equip new
        self.weapon = weapon
        weapon.on_equip(self)
        try:
            self.notify_listeners('stats_changed')
        except Exception:
            pass
        return True

    def unequip_weapon(self) -> bool:
        """Unequip weapon and return it to inventory if possible.

        Returns True if unequipped and added to inventory, False if inventory
        is full and weapon remains equipped.
        """
        if not self.weapon:
            return True
        prev = self.weapon
        # try to add to inventory
        if self.inventory.has_space_for(1):
            prev.on_unequip(self)
            self.inventory.add(prev, 1)
            self.weapon = None
            try:
                self.notify_listeners('stats_changed')
            except Exception:
                pass
            return True
        # cannot unequip because no space
        return False

    def equip_armor(self, armor: Armor) -> bool:
        """Equip armor and update inventory similar to weapons."""
        if armor is None:
            return False

        if self.armor and self.armor.id == armor.id:
            return True

        if self.armor:
            if not self.inventory.has_space_for(1):
                return False

        try:
            in_inv_qty = self.inventory.qty(armor.id)
        except Exception:
            in_inv_qty = 0

        if in_inv_qty > 0:
            self.inventory.remove(armor.id, 1)

        if self.armor:
            prev = self.armor
            prev.on_unequip(self)
            self.inventory.add(prev, 1)

        self.armor = armor
        armor.on_equip(self)
        try:
            self.notify_listeners('stats_changed')
        except Exception:
            pass
        return True

    def unequip_armor(self) -> bool:
        """Unequip armor and return it to inventory if possible."""
        if not self.armor:
            return True
        prev = self.armor
        if self.inventory.has_space_for(1):
            prev.on_unequip(self)
            self.inventory.add(prev, 1)
            self.armor = None
            try:
                self.notify_listeners('stats_changed')
            except Exception:
                pass
            return True
        return False

    def add_experience(self, exp: int) -> List[str]:
        """Получение опыта и увеличение уровня."""
        msgs = []
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
                self.base_damage + (self.level - 1) *
                (self.base_damage * 0.05)
            )
            self.health = self.max_health
            msgs.append(f"🎉 Уровень! {self.name} Lv {self.level}")
        # Notify UI listeners about experience/level changes
        try:
            if old_exp != self.experience:
                self.notify_listeners('experience', old=old_exp, new=self.experience)
            if old_level != self.level:
                self.notify_listeners('level', old=old_level, new=self.level)
        except Exception:
            pass
        return msgs

    def attack(self, target: Creature) -> Tuple[int, int]:
        """Атака цели."""
        raw = self.damage
        dealt = target.take_damage(raw)
        self.total_damage_dealt += dealt
        return dealt, raw

    def use_item(self, item_id: str, battlefield=None) -> str:
        """Использование предмета из инвентаря."""
        item = self.inventory.get(item_id)
        if not item:
            return "У тебя нет такого предмета."
        msg = item.use(self, battlefield)
        if item.is_consumable():
            self.inventory.remove(item_id, 1)
        return msg

    def buy(self, shop, item_id: str, qty: int = 1) -> str:
        """Покупка в магазине."""
        return shop.buy(self, item_id, qty)

    def sell(self, shop, item_id: str, qty: int = 1) -> str:
        """Продажа в магазине."""
        return shop.sell(self, item_id, qty)

    def get_session_stats(self) -> dict:
        """Получить статистику сессии."""
        return {
            "name": self.name,
            "class": self.CLASS_STATS[self.cls]["name"],
            "level": self.level,
            "experience": self.experience,
            "coins": self.coins,
            "total_damage_dealt": self.total_damage_dealt,
            "total_damage_taken": self.total_damage_taken,
            "enemies_defeated": self.enemies_defeated,
            "battles_fought": self.battles_fought,
            "inventory_items": sum(q for _, q in
                                   self.inventory.list_items())
        }

    def add_loot(self, enemy_loot: str, enemy_loot_quantity: int) -> bool:
        """
        Add enemy loot to the player's inventory.

        Args:
            enemy_loot (str): The item ID or name of the loot.
            enemy_loot_quantity (int): The quantity of the loot to add.

        Returns:
            bool: True if the loot was successfully added, False otherwise.

        Raises:
            ValueError: If enemy_loot is invalid or enemy_loot_quantity is not positive.
        """
        if not isinstance(enemy_loot, str) or not enemy_loot.strip():
            raise ValueError("enemy_loot must be a non-empty string representing a valid item ID.")
        if not isinstance(enemy_loot_quantity, int) or enemy_loot_quantity <= 0:
            raise ValueError("enemy_loot_quantity must be a positive integer.")

        # Check if inventory has space for the loot
        if not self.inventory.has_space_for(enemy_loot_quantity):
            return False  # Inventory full, cannot add loot

        # Attempt to add the loot
        try:
            self.inventory.add(ItemDatabase.get(enemy_loot), enemy_loot_quantity)
            return True
        except Exception as e:
            # Log or handle unexpected errors (e.g., invalid item ID)
            print(f"Error adding loot {enemy_loot}: {e}")
            return False

    # Override coins and health to emit events when changed
    @property
    def coins(self) -> int:
        return super().coins

    @coins.setter
    def coins(self, value: int) -> None:
        old = super().coins
        # Set underlying value
        try:
            # assign to backing field directly
            self._coins = value
        except Exception:
            # Fallback to base setter if available
            try:
                Creature.coins.fset(self, value)  # type: ignore
            except Exception:
                pass
        try:
            if old != value:
                self.notify_listeners('coins', old=old, new=value)
        except Exception:
            pass

    @property
    def health(self) -> int:
        return super().health

    @health.setter
    def health(self, value: int) -> None:
        old = super().health
        try:
            self._health = value
        except Exception:
            try:
                Creature.health.fset(self, value)  # type: ignore
            except Exception:
                pass
        try:
            if old != value:
                self.notify_listeners('health', old=old, new=value)
        except Exception:
            pass

    def update_quest_progress(self, enemy_name: str):
        """Обновить прогресс квестов."""
        for quest in self.accepted_quests:
            quest.update_progress(enemy_name)

    def to_dict(self) -> dict:
        """Для сохранения."""
        data = super().to_dict()
        data["type"] = "player"
        data["cls"] = self.cls
        data["inventory"] = self.inventory.to_dict()
        data["experience"] = self.experience
        data["companions"] = [c.to_dict() for c in self.companions]
        data["accepted_quests"] = [quest.to_dict() for quest in self.accepted_quests]
        data["session_stats"] = self.get_session_stats()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """Загрузка из словаря."""
        # Создаём базового игрока
        player = cls(data["name"], data["cls"])

        # Восстанавливаем базовые атрибуты
        player.level = data["level"]
        player.base_health = data["base_health"]
        player.base_damage = data["base_damage"]
        player.base_coins = data["base_coins"]
        player.health = data["health"]
        player.coins = data["coins"]
        player.experience = data.get("experience", 0)

        # Масштабируем здоровье
        player.max_health = player._scale_stat(player.base_health)
        player.base_damage = int(
            player.base_damage + (player.level - 1) *
            (player.base_damage * 0.05)
        )

        # Восстанавливаем инвентарь
        if "inventory" in data:
            from data.items import ItemDatabase
            ItemDatabase.initialize()
            player.inventory = Inventory.from_dict(data["inventory"])

        # Восстанавливаем экипировку
        if data.get("weapon_id"):
            weapon = ItemDatabase.get(data["weapon_id"])
            if weapon:
                player.equip_weapon(weapon)

        if data.get("armor_id"):
            armor = ItemDatabase.get(data["armor_id"])
            if armor:
                player.equip_armor(armor)

        # Восстанавливаем спутников
        if "companions" in data:
            from core.creatures import Companion
            player.companions = [Companion.from_dict(c) for c in data["companions"]]

        # Восстанавливаем квесты (без сериализации квестов для теперь)
        if "accepted_quests" in data:
            player.accepted_quests = []  # Пусто для сейчас

        return player


class TestPlayer(Player):
    """Тестовый класс игрока с высокими характеристиками для тестирования."""

    def __init__(self, name: str):
        # Инициализируем базы данных перед вызовом parent конструктора
        from data.items import ItemDatabase
        ItemDatabase.initialize()
        
        # Создаём базового игрока с классом warrior
        super().__init__(name, "warrior")

        # Переопределяем характеристики для тестирования
        self.base_health = 1000
        self.base_damage = 1000
        self.max_health = self._scale_stat(self.base_health)
        self.health = self.max_health
        self.coins = 10000  # Много монет для тестирования

        # Очищаем инвентарь и добавляем тестовое снаряжение
        self.inventory = Inventory(capacity=20)

        # Добавляем мощное оружие и броню
        # Лучшее оружие
        test_weapon = ItemDatabase.get("w_dragon_sword")
        if test_weapon:
            self.equip_weapon(test_weapon)

        # Лучшая броня
        test_armor = ItemDatabase.get("a_dragon_lord_plate")
        if test_armor:
            self.equip_armor(test_armor)

        # Много зелий
        test_potion = ItemDatabase.get("p_mega")
        if test_potion:
            self.inventory.add(test_potion, 10)
