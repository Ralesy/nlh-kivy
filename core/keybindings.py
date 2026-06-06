#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KeyBindingManager — управление привязками клавиш для игры.
"""

import json
import os
from typing import Optional


class KeyBindingManager:
    """
    Управляет привязками клавиш к действиям в игре.
    Поддерживает сохранение и загрузку настроек в JSON.
    """

    DEFAULT_BINDINGS = {
        # Движение на глобальной карте
        "move_up": "w",
        "move_down": "s",
        "move_left": "a",
        "move_right": "d",
        # Вход/выход
        "enter_location": "enter",
        "exit_location": "q",
        # Быстрые действия (игра без мыши)
        "open_inventory": "tab",
        "open_status": "p",
        "open_companions": "h",
        "open_quests": "u",
        "open_menu": "escape",
        "open_locations": "m",
        "open_save": "f5",
        # Боевая система
        "combat_attack": "j",
        "combat_defend": "k",
        "combat_skill": "l",
        "combat_item": "i",
        # Меню и инвентарь
        "menu_up": "up",
        "menu_down": "down",
        "menu_buy": "b",
        "menu_sell": "v",
        "menu_equip": "e",
        "menu_transfer": "t",
        # Мышиные кнопки
        "mouse_left": "mouse_left",
        "mouse_right": "mouse_right",
    }

    ACTION_NAMES_RU = {
        "move_up": "Движение вверх",
        "move_down": "Движение вниз",
        "move_left": "Движение влево",
        "move_right": "Движение вправо",
        "enter_location": "Войти в локацию",
        "exit_location": "Выйти / Назад",
        "open_inventory": "Открыть инвентарь",
        "open_status": "Открыть статус",
        "open_companions": "Открыть спутников",
        "open_quests": "Открыть квесты",
        "open_menu": "Открыть меню",
        "open_locations": "Открыть карту/локации",
        "open_save": "Сохранить игру",
        "combat_attack": "Бой: Атака",
        "combat_defend": "Бой: Защита",
        "combat_skill": "Бой: Способность",
        "combat_item": "Бой: Использовать предмет",
        "menu_up": "Меню: Вверх",
        "menu_down": "Меню: Вниз",
        "menu_buy": "Купить в магазине",
        "menu_sell": "Продать торговцу",
        "menu_equip": "Экипировать предмет",
        "menu_transfer": "Переложить предмет",
    }

    def __init__(self, filepath: str = "saves/keybindings.json"):
        self.filepath = filepath
        self.bindings = dict(self.DEFAULT_BINDINGS)
        self.load()

    def load(self) -> None:
        """Загрузить настройки привязок клавиш."""
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Обновляем только известные ключи
                    for key, val in data.items():
                        if key in self.DEFAULT_BINDINGS:
                            self.bindings[key] = str(val).lower()
        except Exception as e:
            print(f"[KeyBindingManager] Ошибка при загрузке клавиш: {e}")

    def save(self) -> None:
        """Сохранить настройки привязок клавиш."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.bindings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[KeyBindingManager] Ошибка при сохранении клавиш: {e}")

    def get_action_for_key(self, key_str: str) -> Optional[str]:
        """Получить действие по имени клавиши."""
        if not key_str:
            return None
        key_str = key_str.lower()
        for action, bound_key in self.bindings.items():
            if bound_key == key_str:
                return action
        return None

    def set_binding(self, action: str, key_str: str) -> bool:
        """
        Переназначить клавишу для действия.
        Предотвращает дубликаты.
        """
        if action not in self.bindings:
            return False

        key_str = key_str.lower()

        # Если эта клавиша уже назначена на другое действие, очистим его
        for act, k in list(self.bindings.items()):
            if k == key_str and act != action:
                self.bindings[act] = ""

        self.bindings[action] = key_str
        self.save()
        return True

    def reset_to_defaults(self) -> None:
        """Сбросить настройки на дефолтные."""
        self.bindings = dict(self.DEFAULT_BINDINGS)
        self.save()


# Глобальный инстанс для удобства
key_manager = KeyBindingManager()
