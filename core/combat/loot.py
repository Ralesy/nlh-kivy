#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модели результата боя и дропа.
"""

from typing import List

from data.items import ItemDatabase


class LootDrop:
    """Предмет, выпавший после боя."""

    def __init__(self, item_id: str, quantity: int = 1):
        """Создать запись о дропе."""
        self.item_id = item_id
        self.quantity = max(1, int(quantity))
        self.item = ItemDatabase.get(item_id)

    def display(self) -> str:
        """Текстовое представление для UI."""
        if self.item is None:
            return f"{self.item_id} x{self.quantity}"
        return f"{self.item.display_name()} x{self.quantity}"


class BattleResult:
    """Итог победы: лут, золото и опыт."""

    def __init__(
        self,
        victory: bool,
        loot: List[LootDrop],
        gold_earned: int,
        xp_earned: int,
    ):
        """Зафиксировать результат боя."""
        self.victory = victory
        self.loot = loot
        self.gold_earned = max(0, int(gold_earned))
        self.xp_earned = max(0, int(xp_earned))
