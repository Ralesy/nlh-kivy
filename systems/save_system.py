#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Save system: сохранение и загрузка игры.
"""

import json
from typing import Optional, List
from pathlib import Path
from core.creatures import Player
from data.items import ItemDatabase


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

        # Reconstruct and return the Player object
        if "player" in data:
            ItemDatabase.initialize()
            return Player.from_dict(data["player"])
        
        return None

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
