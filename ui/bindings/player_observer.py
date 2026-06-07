#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Привязка Player к Kivy Properties для автоматического обновления UI.
"""

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, StringProperty


class PlayerViewModel(EventDispatcher):
    """
    ViewModel игрока: синхронизирует core Player с Kivy Properties.

    Виджеты HUD могут биндиться к свойствам вместо ручного ``update()``.
    """

    level = NumericProperty(0)
    health = NumericProperty(0)
    max_health = NumericProperty(0)
    damage = NumericProperty(0)
    defense = NumericProperty(0)
    coins = NumericProperty(0)
    experience = NumericProperty(0)
    xp_required = NumericProperty(0)
    move_speed = NumericProperty(200)
    name = StringProperty("")

    def __init__(self, **kwargs):
        """Создать пустую модель; привязка — через bind_player()."""
        super().__init__(**kwargs)
        self._player = None

    def bind_player(self, player) -> None:
        """Подписать модель на события Player."""
        self.unbind_player()
        self._player = player
        if player:
            player.add_listener(self._on_player_event)
            self.sync_from_player()

    def unbind_player(self) -> None:
        """Отписать модель от текущего игрока."""
        if self._player:
            try:
                self._player.remove_listener(self._on_player_event)
            except Exception:
                pass
        self._player = None

    def sync_from_player(self) -> None:
        """Принудительно скопировать все статы из Player."""
        player = self._player
        if not player:
            return
        self.name = player.name
        self.level = player.level
        self.health = player.health
        self.max_health = player.max_health
        self.damage = player.damage
        self.defense = player.defense
        self.move_speed = player.move_speed
        self.coins = player.coins
        self.experience = player.experience
        self.xp_required = player.level * 100 if player.level else 0

    def _on_player_event(self, event, **kwargs) -> None:
        """Обработчик событий Player → обновление Properties."""
        self.sync_from_player()
