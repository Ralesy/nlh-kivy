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

    # Фоновые истории персонажа
    BACKGROUNDS = {
        "noble": {
            "name": "Обедневший дворянин",
            "coins": 500,
            "weapon_id": "w_iron_dagger",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 3)]
        },
        "squire": {
            "name": "Оруженосец",
            "coins": 50,
            "weapon_id": "w_iron_sword",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 2)]
        },
        "hunter": {
            "name": "Охотник",
            "coins": 200,
            "weapon_id": "w_iron_bow",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 2)]
        }
    }

    # Базовые статы до распределения очков
    BASE_STATS = {
        "health": 100,
        "damage": 10,
        "critical_chance": 0.05,  # 5%
        "luck": 1.0,  # Множитель качества лута
        "selling_multiplier": 1.0  # Множитель цены при продаже
    }

    # Коэффициенты для очков характеристик
    STAT_COEFFICIENTS = {
        "endurance": {"health": 15},  # +15 HP за очко
        "strength": {"damage": 2, "inventory_capacity": 5},  # +2 урона и +5 мест в инвентаре
        "agility": {"critical_chance": 0.05},  # +5% крита за очко
        "luck": {"luck": 0.15},  # +15% качество лута за очко
        "trade": {"selling_multiplier": 0.1}  # +10% к цене продажи за очко
    }

    # Начальное количество очков для распределения (на уровне 1)
    STARTING_SKILL_POINTS = 5

    def __init__(self, name: str, background: str = "squire"):
        if background not in self.BACKGROUNDS:
            background = "squire"
        
        bg = self.BACKGROUNDS[background]
        
        # Инициализируем базовыми статами
        super().__init__(
            name,
            self.BASE_STATS["health"],
            self.BASE_STATS["damage"],
            bg["coins"],
            level=1
        )
        
        self.background = background
        self.inventory = Inventory(capacity=20)
        
        # Система распределения очков (для каждой характеристики текущее значение очков)
        self.skill_points_available = self.STARTING_SKILL_POINTS
        self.skill_points_allocated = {
            "endurance": 0,
            "strength": 0,
            "agility": 0,
            "luck": 0,
            "trade": 0
        }
        
        # Специальные характеристики (вычисляются из очков и базовых статов)
        self._critical_chance = self.BASE_STATS["critical_chance"]
        self._luck = self.BASE_STATS["luck"]
        self._selling_multiplier = self.BASE_STATS["selling_multiplier"]

        # Стартовое оборудование согласно фону
        if bg["weapon_id"]:
            starter_w = ItemDatabase.get(bg["weapon_id"])
            if starter_w:
                self.equip_weapon(starter_w)
        
        if bg["armor_id"]:
            starter_a = ItemDatabase.get(bg["armor_id"])
            if starter_a:
                self.equip_armor(starter_a)

        # Стартовые предметы (по желанию)
        if bg["starting_items"]:
            for item_id, qty in bg["starting_items"]:
                item = ItemDatabase.get(item_id)
                if item:
                    self.inventory.add(item, qty)

        self.experience = 0
        self.companions: List[Companion] = []
        self.accepted_quests: List = []  # List of accepted quests
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.enemies_defeated = 0
        self.battles_fought = 0
        self.last_location_pos = {}  # location_id -> (x_norm, y_norm)
        self.defeated_bosses = set()  # set of defeated boss ids
        # --- Observer/listener support for event-driven UI updates ---
        # Listeners receive calls like: callback(event_name: str, **kwargs)
        self._listeners = []
    
    # ===== Система распределения очков =====
    def allocate_skill_point(self, skill: str) -> bool:
        """Распределить один очко в характеристику. Возвращает True если успешно."""
        if skill not in self.skill_points_allocated:
            return False
        if self.skill_points_available <= 0:
            return False
        
        self.skill_points_allocated[skill] += 1
        self.skill_points_available -= 1
        self._recalculate_derived_stats()
        return True
    
    def deallocate_skill_point(self, skill: str) -> bool:
        """Вернуть один очко из характеристики."""
        if skill not in self.skill_points_allocated:
            return False
        if self.skill_points_allocated[skill] <= 0:
            return False
        
        self.skill_points_allocated[skill] -= 1
        self.skill_points_available += 1
        self._recalculate_derived_stats()
        return True
    
    def _recalculate_derived_stats(self):
        """Пересчитать производные характеристики на основе очков."""
        # Здоровье: базовое + (выносливость * коэфф)
        new_health = self.BASE_STATS["health"] + self.skill_points_allocated["endurance"] * self.STAT_COEFFICIENTS["endurance"]["health"]
        self.base_health = new_health
        self.max_health = self._scale_stat(self.base_health)
        
        # Урон: базовый + (сила * коэфф)
        new_damage = self.BASE_STATS["damage"] + self.skill_points_allocated["strength"] * self.STAT_COEFFICIENTS["strength"]["damage"]
        self.base_damage = new_damage
        
        # Вместимость инвентаря: базовая 20 + (сила * коэфф)
        new_capacity = 20 + self.skill_points_allocated["strength"] * self.STAT_COEFFICIENTS["strength"]["inventory_capacity"]
        self.inventory.capacity = int(new_capacity)
        
        # Крит: базовый + (ловкость * коэфф)
        self._critical_chance = self.BASE_STATS["critical_chance"] + self.skill_points_allocated["agility"] * self.STAT_COEFFICIENTS["agility"]["critical_chance"]
        
        # Удача: базовая + (удача * коэфф)
        self._luck = self.BASE_STATS["luck"] + self.skill_points_allocated["luck"] * self.STAT_COEFFICIENTS["luck"]["luck"]
        
        # Торговля: базовая + (торговля * коэфф)
        self._selling_multiplier = self.BASE_STATS["selling_multiplier"] + self.skill_points_allocated["trade"] * self.STAT_COEFFICIENTS["trade"]["selling_multiplier"]
    
    @property
    def critical_chance(self) -> float:
        """Шанс на критический удар (0.0-1.0)."""
        return clamp(self._critical_chance, 0.0, 1.0)
    
    @property
    def luck(self) -> float:
        """Удача (множитель качества лута)."""
        return max(0.0, self._luck)
    
    @property
    def selling_multiplier(self) -> float:
        """Множитель цены при продаже."""
        return max(0.0, self._selling_multiplier)

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
            # Даём +1 очко при повышении уровня
            self.skill_points_available += 1
            msgs.append(f"🎉 Уровень! {self.name} Lv {self.level}")
            msgs.append(f"📊 +1 очко для распределения")
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
            "class": self.background,
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
        data["background"] = self.background
        data["inventory"] = self.inventory.to_dict()
        data["experience"] = self.experience
        data["skill_points_available"] = self.skill_points_available
        data["skill_points_allocated"] = self.skill_points_allocated
        data["companions"] = [c.to_dict() for c in self.companions]
        data["accepted_quests"] = [quest.to_dict() for quest in self.accepted_quests]
        data["session_stats"] = self.get_session_stats()
        data["last_location_pos"] = self.last_location_pos
        data["defeated_bosses"] = list(self.defeated_bosses)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """Загрузка из словаря."""
        # Создаём базового игрока с сохранённым фоном
        background = data.get("background", "squire")
        player = cls(data["name"], background)

        # Восстанавливаем базовые атрибуты
        player.level = data["level"]
        player.base_health = data["base_health"]
        player.base_damage = data["base_damage"]
        player.base_coins = data["base_coins"]
        player.health = data["health"]
        player.coins = data["coins"]
        player.experience = data.get("experience", 0)

        # Восстанавливаем распределённые очки навыков
        if "skill_points_allocated" in data:
            player.skill_points_allocated = data["skill_points_allocated"]
            player.skill_points_available = data.get("skill_points_available", 0)
            player._recalculate_derived_stats()

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

        # Восстанавливаем позиции в локациях
        player.last_location_pos = data.get("last_location_pos", {})

        # Восстанавливаем поверженных боссов
        player.defeated_bosses = set(data.get("defeated_bosses", []))

        return player


class TestPlayer(Player):
    """Тестовый класс игрока с высокими характеристиками для тестирования."""

    def __init__(self, name: str):
        # Инициализируем базы данных перед вызовом parent конструктора
        from data.items import ItemDatabase
        ItemDatabase.initialize()
        
        # Создаём базового игрока с фоном squire
        super().__init__(name, "squire")

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
            self.inventory.add(test_potion, 19)
