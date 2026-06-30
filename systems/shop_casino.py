#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shop & Casino: магазин и казино.
"""

import random
from typing import Dict, Optional, Tuple
from core.creatures import Player
from data.items import ItemDatabase, Weapon, Armor


class Shop:
    """Магазин."""

    def __init__(self, stock: Dict[str, Optional[int]]):
        self.stock = stock.copy()

    def list_for_sale(self) -> str:
        """Список товаров."""
        lines = []
        for iid, qty in self.stock.items():
            item = ItemDatabase.get(iid)
            if not item:
                continue
            q = "∞" if qty is None else str(qty)
            lines.append(
                f"{item.display_name()} — {item.price} монет "
                f"(в наличии: {q})"
            )
        return "\n".join(lines)

    def buy(
        self,
        player: Player,
        item_id: str,
        qty: int = 1,
        price_modifier: float = 1.0,
    ) -> str:
        """Покупка.

        Args:
            player: игрок.
            item_id: ID предмета.
            qty: количество.
            price_modifier: множитель цены (от DangerManager).
        """
        item = ItemDatabase.get(item_id)
        if not item:
            return "Товар не найден."

        stock_qty = self.stock.get(item_id)
        if stock_qty is not None and stock_qty < qty:
            return "В магазине нет такого количества."

        base_cost = item.price * qty
        cost = int(base_cost * price_modifier)
        if player.coins < cost:
            return "Недостаточно монет."

        if not player.inventory.has_space_for(qty):
            return "Недостаточно места в инвентаре."

        player.coins -= cost
        player.inventory.add(item, qty)
        if stock_qty is not None:
            self.stock[item_id] -= qty

        return f"Куплено {item.name} x{qty} за {cost} монет."

    def sell(self, player: Player, item_id: str, qty: int = 1) -> str:
        """Продажа."""
        item = ItemDatabase.get(item_id)
        if not item:
            return "Невозможно продать."

        # Проверяем есть ли в инвентаре достаточное количество
        in_inventory = player.inventory.qty(item_id)
        if in_inventory < qty:
            return "У вас нет столько предметов."

        # Предотвращаем продажу последнего экземпляра, если он экипирован.
        # Учтём общее количество предметов у игрока (в инвентаре + экипировка).
        equip_count = 0
        if player.weapon and player.weapon.id == item_id:
            equip_count += 1
        if player.armor and player.armor.id == item_id:
            equip_count += 1

        total_owned = in_inventory + equip_count

        # Блокируем только если пытаются продать ВСЕ имеющиеся копии,
        # и при этом хоть одна копия сейчас экипирована.
        if qty >= total_owned and equip_count > 0:
            item_type = "оружие" if isinstance(item, Weapon) else "броня"
            return f"Нельзя продавать последнее экипированное {item_type}. Снимите сначала."

        price = (item.price * qty) // 5
        player.inventory.remove(item_id, qty)
        player.coins += price
        self.stock[item_id] = self.stock.get(item_id, 0) + qty

        return f"Продано {item.name} x{qty} за {price} монет."

    def refresh(self, location_manager=None) -> None:
        """Обновление стока после боя.

        Если передан менеджер локаций (location_manager), формируем
        новый ассортимент: 3 случайных оружия и 2 комплекта брони,
        доступных для уже разблокированных локаций. Если
        location_manager не передан, используется старая
        случайная корректировка стока.
        """
        # Поддержка обратной совместимости: без менеджера локаций
        # оставляем старое поведение (с небольшими изменениями).
        def _legacy_refresh():
            for iid in list(self.stock.keys()):
                if random.random() < 0.5:
                    self.stock[iid] = max(
                        0, self.stock.get(iid, 0) + random.randint(-2, 3)
                    )
                if self.stock[iid] is not None:
                    self.stock[iid] = max(0, self.stock[iid])

        # Если нет внешнего менеджера — делаем легкий рефреш
        # (вызывается из более старых мест).
        try:
            # Мы ожидаем объект менеджера локаций с атрибутом locations
            # Передавать его нужно из Game: self.shop.refresh(self.location_manager)
            location_manager  # type: ignore
        except NameError:
            _legacy_refresh()
            return

        # Если объект не передан явно — оставить старое поведение
        if location_manager is None:
            _legacy_refresh()
            return

        # Карта материалов/пулов предметов по локациям.
        LOCATION_MATERIAL_POOLS = {
            "forest": {
                "weapons": ["iron", "steel"],
                "armors": ["leather", "iron"]
            },
            "swamp": {
                "weapons": ["goblin", "iron", "steel"],
                "armors": ["leather", "iron", "orc"]
            },
            "mines": {
                "weapons": ["orc", "dwarf", "steel"],
                "armors": ["iron", "steel", "dwarf"]
            },
            "mountains": {
                "weapons": ["elf", "dwarf", "dragon", "steel"],
                "armors": ["elf", "dwarf", "dragon"]
            },
            "ancient_cave": {
                "weapons": ["dragon", "elf"],
                "armors": ["dragon", "elf"]
            }
        }

        # Собираем разрешённые материалы по разблокированным локациям
        allowed_weapon_materials = set()
        allowed_armor_materials = set()
        # Determine whether mines are unlocked; elven gear is gated by mines
        mines_unlocked = False
        try:
            mines_loc = getattr(location_manager, 'locations', {}).get('mines')
            if mines_loc and not getattr(mines_loc, 'is_locked', True):
                mines_unlocked = True
        except Exception:
            mines_unlocked = False
        for loc in getattr(location_manager, "locations", {}).values():
            if not getattr(loc, "is_locked", True):
                pool = LOCATION_MATERIAL_POOLS.get(loc.id)
                if pool:
                    # Only allow 'elf' material if mines are unlocked
                    for m in pool.get("weapons", []):
                        if m == 'elf' and not mines_unlocked:
                            continue
                        allowed_weapon_materials.add(m)
                    for m in pool.get("armors", []):
                        if m == 'elf' and not mines_unlocked:
                            continue
                        allowed_armor_materials.add(m)
        # Надёжный fallback — если ничего не собрали, используем железо
        if not allowed_weapon_materials:
            allowed_weapon_materials.add("iron")
        if not allowed_armor_materials:
            allowed_armor_materials.add("leather")

        # Формируем кандидатов из ItemDatabase
        weapons = [
            it for it in ItemDatabase.ITEMS.values()
            if isinstance(it, Weapon)
            and (not it.is_unique)
            and it.material in allowed_weapon_materials
        ]
        armors = [
            it for it in ItemDatabase.ITEMS.values()
            if isinstance(it, Armor)
            and (not it.is_unique)
            and it.material in allowed_armor_materials
        ]

        # Если кандидатов мало — расширяем до всех неуникальных предметов
        if len(weapons) < 3:
            weapons = [
                it for it in ItemDatabase.ITEMS.values()
                if isinstance(it, Weapon) and not it.is_unique
            ]
        if len(armors) < 2:
            armors = [
                it for it in ItemDatabase.ITEMS.values()
                if isinstance(it, Armor) and not it.is_unique
            ]

        # Выбираем случайный ассортимент
        sel_weapons = random.sample(weapons, min(3, len(weapons)))
        sel_armors = random.sample(armors, min(2, len(armors)))

        # Базовые аптечки оставляем в ассортименте
        new_stock: Dict[str, Optional[int]] = {}
        for pid, qty in [("p_small", 15), ("p_med", 8), ("p_large", 3)]:
            if ItemDatabase.get(pid):
                new_stock[pid] = qty

        # Добавляем выбранное оружие и броню
        for w in sel_weapons:
            new_stock[w.id] = random.randint(1, 3)
        for a in sel_armors:
            new_stock[a.id] = random.randint(1, 2)

        # Устанавливаем новый сток
        self.stock = new_stock


class Casino:
    """Небольшая реализация казино с играми: coinflip, slots, wheel."""

    @staticmethod
    def coinflip(bet: int, choice: str) -> Tuple[bool, int, str]:
        """Орёл-решка.

        Возвращает кортеж (won: bool, payout: int, message: str).
        payout положителен при выигрыше, отрицателен при проигрыше.
        """
        if bet <= 0:
            return False, 0, "Ставка должна быть положительной."
        if choice not in ("h", "t"):
            return False, 0, "Выберите 'h' (орёл) или 't' (решка)."

        flip = random.choice(("h", "t"))
        flip_name = "орёл" if flip == "h" else "решка"

        if flip == choice:
            return True, bet, f"Выпало {flip_name}. Вы выиграли {bet} монет! [Победа]"
        else:
            return False, -bet, f"Выпало {flip_name}. Вы проиграли {bet} монет. 😞"

    @staticmethod
    def slots(bet: int) -> Tuple[str, int]:
        """Простые слоты: возвращает (result_text, payout).

        Правила:
        - Три одинаковых символа: выплата 5x ставки
        - Два одинаковых символа: выплата 2x ставки
        - Иначе: проигрыш (-bet)
        """
        if bet <= 0:
            return "Ставка должна быть положительной.", 0

        symbols = ["🍒", "🔔", "[Уровень]", "7", "🍋"]
        reels = [random.choice(symbols) for _ in range(3)]
        res = " | ".join(reels)

        if reels[0] == reels[1] == reels[2]:
            payout = bet * 5
            return f"{res} — Три в ряд! Вы выиграли {payout} монет! [Победа]", payout
        # two of them equal
        elif reels[0] == reels[1] or reels[0] == reels[2] or reels[1] == reels[2]:
            payout = bet * 2
            return f"{res} — Две одинаковых! Вы выиграли {payout} монет.", payout
        else:
            return f"{res} — Увы, вы проиграли {bet} монет.", -bet

    @staticmethod
    def wheel(bet: int) -> Tuple[str, int]:
        """Колесо фортуны: возвращает (label, payout).

        Колесо имеет сектора с разными множителями.
        """
        if bet <= 0:
            return "Ставка должна быть положительной.", 0

        # sectors: (label, multiplier)
        sectors = [
            ("Малое везение", 0),  # потеря
            ("Малое везение", 0),
            ("Нечто", 1),
            ("Удача", 2),
            ("Большая удача", 3),
            ("Джекпот", 10),
        ]

        label, mult = random.choice(sectors)
        if mult == 0:
            return f"{label} — вы проиграли {bet} монет.", -bet
        payout = bet * mult
        return f"{label} — вы выиграли {payout} монет!", payout