#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Случайные события при исследовании локаций.
"""

import random
from typing import Optional

from core.creatures import Player
from data.items import ItemDatabase


class EventSystem:
    """Взвешенные события для леса, болота и шахт."""

    FOREST_EVENTS = [
        ("found_potion", 0.15),
        ("ambush", 0.12),
        ("nothing", 0.73),
    ]

    SWAMP_EVENTS = [
        ("found_item", 0.10),
        ("poison_gas", 0.10),
        ("nothing", 0.80),
    ]

    MINES_EVENTS = [
        ("found_ore", 0.12),
        ("cave_in", 0.10),
        ("nothing", 0.78),
    ]

    @staticmethod
    def roll_event(location_id: str, player: Player) -> Optional[str]:
        """
        Выполнить случайное событие в локации.

        Returns:
            Текст сообщения для UI или None.
        """
        if location_id == "forest":
            events = EventSystem.FOREST_EVENTS
        elif location_id == "swamp":
            events = EventSystem.SWAMP_EVENTS
        elif location_id == "mines":
            events = EventSystem.MINES_EVENTS
        else:
            return None

        choice = random.choices(
            [event_id for event_id, _ in events],
            weights=[weight for _, weight in events],
            k=1,
        )[0]

        if choice == "found_potion":
            potion = ItemDatabase.get("p_small")
            if potion and player.inventory.has_space_for(1):
                player.inventory.add(potion, 1)
                return f"Вы нашли зелье! +{potion.display_name()}"
            return "Вы нашли зелье, но инвентарь полон."

        if choice == "poison_gas":
            damage = random.randint(10, 30)
            player.take_damage(damage)
            return f"Ядовитый газ! Вы получили {damage} урона."

        if choice == "cave_in":
            damage = random.randint(15, 40)
            player.take_damage(damage)
            return f"Обрушение! Вы получили {damage} урона."

        return None
