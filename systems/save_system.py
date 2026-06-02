#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Save system: сохранение и загрузка игры и сессии.
"""

import json
from typing import TYPE_CHECKING, Any, Dict, Optional, List
from pathlib import Path
from core.creatures import Player
from data.items import ItemDatabase

if TYPE_CHECKING:
    from core.session import GameSession

SAVES_DIR = Path("saves")
SESSION_VERSION = "2.0"


def ensure_saves_dir() -> None:
    """Создать папку saves/, если её ещё нет."""
    SAVES_DIR.mkdir(exist_ok=True)


def get_save_path(filename: str) -> Path:
    """Полный путь к файлу сохранения."""
    return SAVES_DIR / f"{filename}.json"


def read_save_data(filename: str) -> Optional[Dict[str, Any]]:
    """Прочитать JSON сохранения без восстановления объектов."""
    try:
        save_path = get_save_path(filename)
        if not save_path.exists():
            return None
        with open(save_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения сохранения: {e}")
        return None


def save_session(session: "GameSession", filename: str) -> bool:
    """
    Сохранить полную игровую сессию (игрок, день, NPC).

    Returns:
        True при успехе.
    """
    try:
        ensure_saves_dir()
        save_path = get_save_path(filename)
        data = session.to_save_dict()
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка сохранения сессии: {e}")
        return False


def load_session_into(session: "GameSession", filename: str) -> bool:
    """
    Загрузить сохранение в существующую сессию.

    Returns:
        True, если игрок восстановлен.
    """
    data = read_save_data(filename)
    if not data or "player" not in data:
        return False

    try:
        ItemDatabase.initialize()
        session.player = Player.from_dict(data["player"])
        session.day = int(
            data.get("day", getattr(session.player, "level", 1) * 5)
        )
        session.history = list(data.get("history", []))
        session.wins_in_row = int(data.get("wins_in_row", 0))
        session.restore_npc_state(data.get("npcs", {}))
        # Восстановить состояние DangerManager
        if "danger" in data:
            session.danger_manager.from_dict(data["danger"])
        return True
    except Exception as e:
        print(f"Ошибка загрузки сессии: {e}")
        return False


def save_game(player: Player, filename: str) -> bool:
    """
    Сохранить только игрока (legacy-формат v1.0).

    Для полного сохранения используйте save_session().
    """
    try:
        ensure_saves_dir()
        save_path = get_save_path(filename)
        data = {
            "player": player.to_dict(),
            "version": "1.0",
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False


def load_game(filename: str) -> Optional[Player]:
    """Загрузить только игрока из сохранения."""
    data = read_save_data(filename)
    if not data or "player" not in data:
        return None

    try:
        ItemDatabase.initialize()
        return Player.from_dict(data["player"])
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return None


def get_save_list() -> List[str]:
    """Получить список всех сохранений."""
    ensure_saves_dir()
    # Return saves sorted by modification time (newest first)
    saves = []
    for file in SAVES_DIR.glob("*.json"):
        try:
            mtime = file.stat().st_mtime
        except Exception:
            mtime = 0
        saves.append((file.stem, mtime))
    # sort by mtime descending
    saves.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in saves]


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
