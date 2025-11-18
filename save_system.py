#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Save system: сохранение и загрузка игры.
"""

import json
from typing import Optional, List
from pathlib import Path
from creatures import Player, Companion
from items import ItemDatabase, Weapon, Armor


SAVES_DIR = Path("saves")


def ensure_saves_dir() -> None:
    """Создаёт папку для сохранений если её нет."""
    SAVES_DIR.mkdir(exist_ok=True)


def get_save_path(filename: str) -> Path:
    """Получить полный путь для сохранения."""
    return SAVES_DIR / f"{filename}.json"


def save_game(player: Player, filename: str) -> bool:
    """Сохранить игру."""
    try:
        ensure_saves_dir()
        save_path = get_save_path(filename)
        data = {
            "player": player.to_dict(),
            "version": "1.0"
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False


def load_game(filename: str) -> Optional[Player]:
    """Загрузить игру."""
    try:
        save_path = get_save_path(filename)
        if not save_path.exists():
            return None

        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        player_data = data.get("player", {})

        # Создаём игрока
        player = Player(
            player_data.get("name", "Герой"),
            player_data.get("cls", "warrior")
        )

        # Восстанавливаем характеристики
        player.level = player_data.get("level", 1)
        player.health = player_data.get("health", player.max_health)
        player.coins = player_data.get("coins", 0)
        player.experience = player_data.get("experience", 0)

        # Восстанавливаем экипировку
        if player_data.get("weapon_id"):
            weapon = ItemDatabase.get(player_data["weapon_id"])
            if weapon and isinstance(weapon, Weapon):
                player.equip_weapon(weapon)

        if player_data.get("armor_id"):
            armor = ItemDatabase.get(player_data["armor_id"])
            if armor and isinstance(armor, Armor):
                player.equip_armor(armor)

        # Восстанавливаем инвентарь
        inv_data = player_data.get("inventory", {})
        player.inventory.items = {}
        for item_id, (item_dict, qty) in inv_data.get(
            "items", {}
        ).items():
            item = ItemDatabase.get(item_id)
            if item:
                player.inventory.add(item, qty)

        # Восстанавливаем спутников
        player.companions = []
        for comp_data in player_data.get("companions", []):
            comp = Companion(
                comp_data.get("name", "Спутник"),
                comp_data.get("role", "archer"),
                comp_data.get("level", 1)
            )
            comp.health = comp_data.get("health", comp.max_health)
            player.companions.append(comp)

        # Восстанавливаем статистику
        stats = player_data.get("session_stats", {})
        player.total_damage_dealt = stats.get(
            "total_damage_dealt", 0
        )
        player.total_damage_taken = stats.get(
            "total_damage_taken", 0
        )
        player.enemies_defeated = stats.get("enemies_defeated", 0)
        player.battles_fought = stats.get("battles_fought", 0)

        return player

    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return None


def get_save_list() -> List[str]:
    """Получить список всех сохранений."""
    ensure_saves_dir()
    saves = []
    for file in SAVES_DIR.glob("*.json"):
        saves.append(file.stem)
    return sorted(saves)


def delete_save(filename: str) -> bool:
    """Удалить сохранение."""
    try:
        save_path = get_save_path(filename)
        if save_path.exists():
            save_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Ошибка удаления: {e}")
        return False
