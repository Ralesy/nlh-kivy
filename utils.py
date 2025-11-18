#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities: вспомогательные функции и константы.
"""

import time
import random
from typing import List, Tuple, Any

# ---- Константы ----

RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
RARITY_ICONS = {
    "Common": "⚪",
    "Uncommon": "🟢",
    "Rare": "🔵",
    "Epic": "🟣",
    "Legendary": "🟡"
}

# ---- Функции ----


def clamp(v: float, a: float, b: float) -> float:
    """Зажимает значение между a и b."""
    return max(a, min(b, v))


def pause(seconds: float = 0.4) -> None:
    """Пауза в секундах."""
    time.sleep(seconds)


def rnd_choice_weighted(items_with_weight: List[Tuple[Any, float]]) -> Any:
    """Выбирает элемент на основе весов."""
    total = sum(w for _, w in items_with_weight)
    r = random.random() * total
    upto = 0.0
    for item, weight in items_with_weight:
        if upto + weight >= r:
            return item
        upto += weight
    return items_with_weight[-1][0]


def rarity_weighted_choice() -> str:
    """Выбирает редкость на основе весов (Common > Legendary)."""
    weights = [0.5, 0.25, 0.12, 0.08, 0.05]
    return rnd_choice_weighted(list(zip(RARITIES, weights)))


def clear_screen() -> None:
    """Очищает экран консоли."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text: str) -> None:
    """Выводит заголовок с разделителями."""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)


def print_section(text: str) -> None:
    """Выводит подзаголовок."""
    print(f"\n--- {text} ---")
