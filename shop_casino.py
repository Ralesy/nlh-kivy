#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shop & Casino: магазин и казино.
"""

import random
from typing import Dict, Optional, Tuple
from creatures import Player
from items import ItemDatabase, Weapon, Armor


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

    def buy(self, player: Player, item_id: str, qty: int = 1) -> str:
        """Покупка."""
        item = ItemDatabase.get(item_id)
        if not item:
            return "Товар не найден."

        stock_qty = self.stock.get(item_id)
        if stock_qty is not None and stock_qty < qty:
            return "В магазине нет такого количества."

        cost = item.price * qty
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

        price = (item.price * qty) // 2
        player.inventory.remove(item_id, qty)
        player.coins += price
        self.stock[item_id] = self.stock.get(item_id, 0) + qty

        return f"Продано {item.name} x{qty} за {price} монет."

    def refresh(self) -> None:
        """Обновление стока после боя."""
        for iid in list(self.stock.keys()):
            if random.random() < 0.5:
                self.stock[iid] = max(
                    0, self.stock.get(iid, 0) + random.randint(-2, 3)
                )
            if self.stock[iid] is not None:
                self.stock[iid] = max(0, self.stock[iid])


class Casino:
    """Казино."""

    @staticmethod
    def coinflip(bet: int, choice: str) -> Tuple[bool, int, str]:
        """Орёл-решка."""
        if bet <= 0:
            return False, 0, "Ставка должна быть положительной."
        if choice not in ('h', 't'):
            return False, 0, "Выберите 'h' (орёл) или 't' (решка)."

        flip = random.choice(('h', 't'))
        flip_name = "орёл" if flip == 'h' else "решка"

        if flip == choice:
            return True, bet, (
                f"Выпало {flip_name}. Вы выиграли {bet} монет! 🎉"
            )
        else:
            return False, -bet, (
                f"Выпало {flip_name}. Вы проиграли {bet} монет. 😞"
            )

    @staticmethod
    def slots(bet: int) -> Tuple[str, int]:
        """Слот-машина."""
        if bet <= 0:
            return "Неверная ставка.", 0

        symbols = ['🍒', '🍋', '🔔', '⭐', '7']
        weights = [0.35, 0.25, 0.2, 0.15, 0.05]
        res = [random.choices(symbols, weights)[0] for _ in range(3)]

        if res[0] == res[1] == res[2]:
            mult = {
                '🍒': 2, '🍋': 3, '🔔': 4,
                '⭐': 6, '7': 10
            }[res[0]]
            return (f"Слоты: {' '.join(res)} - Джекпот! "
                    f"Выигрыш: {bet * mult} монет! 🎊"), bet * mult

        if (res[0] == res[1] or res[1] == res[2] or
                res[0] == res[2]):
            return (f"Слоты: {' '.join(res)} - Два совпадения! "
                    f"Выигрыш: {bet // 2} монет."), bet // 2

        return f"Слоты: {' '.join(res)} - Ничего. Проигрыш.", -bet

    @staticmethod
    def wheel(bet: int) -> Tuple[str, int]:
        """Колесо фортуны."""
        if bet <= 0:
            return "Неверная ставка.", 0

        sectors = [
            ('big', 0.05),
            ('medium', 0.15),
            ('small', 0.3),
            ('lose', 0.5)
        ]

        def rnd_weighted(items):
            total = sum(w for _, w in items)
            r = random.random() * total
            upto = 0.0
            for item, weight in items:
                if upto + weight >= r:
                    return item
                upto += weight
            return items[-1][0]

        s = rnd_weighted(sectors)

        if s == 'big':
            return f'Колесо: БИЙ-КУСК! Выигрыш {bet * 8}!', bet * 8
        if s == 'medium':
            return f'Колесо: СРЕДНЕЕ. Выигрыш {bet * 3}', bet * 3
        if s == 'small':
            return f'Колесо: МАЛЕНЬКОЕ. Выигрыш {bet}', bet
        return 'Колесо: ПРОИГРЫШ!', -bet
