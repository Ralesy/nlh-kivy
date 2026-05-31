#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Overlay HUD с HP, статами, монетами и XP игрока."""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp

from ui.ui_styles import COLORS
from ui.bindings.player_observer import PlayerViewModel
from ui.widgets.level_up_popup import LevelUpPopup


class GameHUD(BoxLayout):
    """Overlay HUD показывающий HP, DMG, DEF, монеты, XP и уровень игрока."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width = dp(600)
        self.height = dp(85)
        self.pos_hint = {'x': 0, 'top': 0.98}
        self.orientation = 'vertical'
        self.padding = dp(6)
        self.spacing = dp(3)
        self.opacity = 0

        with self.canvas.before:
            Color(0.14, 0.14, 0.14, 0.92)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda i, v: setattr(self._bg_rect, 'pos', i.pos),
            size=lambda i, v: setattr(self._bg_rect, 'size', i.size),
        )

        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20), spacing=dp(6))
        self.level_label = Label(
            text='Lvl: -', font_size=dp(13), size_hint_x=None, width=dp(70), halign='left',
        )
        top.add_widget(self.level_label)
        self.add_widget(top)

        hp_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22), spacing=dp(8))
        self.hp_label = Label(
            text='HP: -/-', font_size=dp(11), size_hint_x=None, width=dp(90), halign='left',
        )
        hp_row.add_widget(self.hp_label)
        self._hp_bar_container = Widget(size_hint_x=1, size_hint_y=None, height=dp(18))
        with self._hp_bar_container.canvas:
            Color(0.12, 0.12, 0.12, 1)
            self._hp_bar_bg = Rectangle(
                pos=self._hp_bar_container.pos, size=self._hp_bar_container.size,
            )
            Color(*COLORS['hp_red'])
            self._hp_bar_fg = Rectangle(
                pos=self._hp_bar_container.pos, size=(0, self._hp_bar_container.height),
            )
        self._hp_bar_container.bind(pos=lambda i, v: setattr(self._hp_bar_bg, 'pos', i.pos))
        self._hp_bar_container.bind(size=lambda i, v: setattr(self._hp_bar_bg, 'size', i.size))
        self._hp_bar_container.bind(pos=lambda i, v: setattr(self._hp_bar_fg, 'pos', (i.x, i.y)))
        hp_row.add_widget(self._hp_bar_container)
        self.add_widget(hp_row)

        xp_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22), spacing=dp(8))
        self.xp_label = Label(
            text='XP: -/-', font_size=dp(11), size_hint_x=None, width=dp(90), halign='left',
        )
        xp_row.add_widget(self.xp_label)
        self._xp_bar_container = Widget(size_hint_x=1, size_hint_y=None, height=dp(18))
        with self._xp_bar_container.canvas:
            Color(0.12, 0.12, 0.12, 1)
            self._xp_bar_bg = Rectangle(
                pos=self._xp_bar_container.pos, size=self._xp_bar_container.size,
            )
            Color(*COLORS['xp_purple'])
            self._xp_bar_fg = Rectangle(
                pos=self._xp_bar_container.pos, size=(0, self._xp_bar_container.height),
            )
        self._xp_bar_container.bind(pos=lambda i, v: setattr(self._xp_bar_bg, 'pos', i.pos))
        self._xp_bar_container.bind(size=lambda i, v: setattr(self._xp_bar_bg, 'size', i.size))
        self._xp_bar_container.bind(pos=lambda i, v: setattr(self._xp_bar_fg, 'pos', (i.x, i.y)))
        xp_row.add_widget(self._xp_bar_container)
        self.add_widget(xp_row)

        stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20), spacing=dp(8))
        self.dmg_label = Label(
            text='DMG: -', font_size=dp(11), size_hint_x=None, width=dp(70), halign='left',
        )
        self.def_label = Label(
            text='DEF: -', font_size=dp(11), size_hint_x=None, width=dp(70), halign='left',
        )
        self.coins_label_small = Label(text='COINS: -', font_size=dp(11), halign='left')
        stats.add_widget(self.dmg_label)
        stats.add_widget(self.def_label)
        stats.add_widget(self.coins_label_small)
        self.add_widget(stats)

        self._view_model = None
        self._bound_player = None
        self._last_level = 0
        self._vm_bound = False

    def bind_to_view_model(self, view_model: PlayerViewModel) -> None:
        """Привязать HUD к PlayerViewModel (реактивное обновление)."""
        try:
            self._unbind_view_model()
            self._view_model = view_model
            if view_model:
                view_model.bind(
                    level=self._on_vm_level,
                    health=self._on_vm_health,
                    max_health=self._on_vm_max_health,
                    damage=self._on_vm_damage,
                    defense=self._on_vm_defense,
                    coins=self._on_vm_coins,
                    experience=self._on_vm_experience,
                    xp_required=self._on_vm_xp_required,
                )
                self._vm_bound = True
                self._last_level = view_model.level
                self._refresh_all_from_vm()
                self.opacity = 1
        except Exception:
            pass

    def bind_to_player(self, player) -> None:
        """Привязать HUD к Player через PlayerViewModel (обратная совместимость)."""
        try:
            self._bound_player = player
            app = App.get_running_app()
            vm = getattr(app, 'player_view', None) if app else None
            if vm is None:
                if self._view_model is None:
                    self._view_model = PlayerViewModel()
                vm = self._view_model
            vm.bind_player(player)
            self.bind_to_view_model(vm)
        except Exception:
            pass

    def unbind_player(self) -> None:
        """Отвязать HUD от текущей модели (не трогает app.player_view)."""
        try:
            self._unbind_view_model()
            self._bound_player = None
            self.opacity = 0
        except Exception:
            pass

    def _unbind_view_model(self) -> None:
        if self._view_model and self._vm_bound:
            try:
                self._view_model.unbind(
                    level=self._on_vm_level,
                    health=self._on_vm_health,
                    max_health=self._on_vm_max_health,
                    damage=self._on_vm_damage,
                    defense=self._on_vm_defense,
                    coins=self._on_vm_coins,
                    experience=self._on_vm_experience,
                    xp_required=self._on_vm_xp_required,
                )
            except Exception:
                pass
        self._vm_bound = False

    def update(self) -> None:
        """Принудительно обновить отображение (fallback / смена экрана)."""
        if self._view_model:
            self._refresh_all_from_vm()
            return
        app = App.get_running_app()
        if not app or not getattr(app, 'game', None) or not getattr(app.game, 'player', None):
            return
        p = app.game.player
        self._apply_stats(
            p.level, p.health, p.max_health, p.damage, p.defense,
            p.coins, p.experience, p.level * 100 if p.level else 0,
        )

    def _refresh_all_from_vm(self) -> None:
        vm = self._view_model
        if not vm:
            return
        self._apply_stats(
            vm.level, vm.health, vm.max_health, vm.damage, vm.defense,
            vm.coins, vm.experience, vm.xp_required,
        )

    def _apply_stats(
        self, level, health, max_health, damage, defense, coins, experience, xp_required,
    ) -> None:
        try:
            self.level_label.text = f"Lvl: {level}"
            self.hp_label.text = f"HP: {health}/{max_health}"
            self._update_bar(self._hp_bar_container, self._hp_bar_fg, health, max_health)
            self.xp_label.text = f"XP: {experience}/{xp_required}"
            self._update_bar(self._xp_bar_container, self._xp_bar_fg, experience, xp_required)
            self.dmg_label.text = f"DMG: {damage}"
            self.def_label.text = f"DEF: {defense}"
            self.coins_label_small.text = f"COINS: {coins}"
        except Exception:
            pass

    def _update_bar(self, container, fg_rect, current, maximum) -> None:
        try:
            pct = float(current) / float(maximum) if maximum else 0.0
            full_w = max(1, container.width)
            fg_w = max(0, int(full_w * pct))
            fg_rect.size = (fg_w, container.height)
        except Exception:
            pass

    def _on_vm_level(self, instance, value) -> None:
        self.level_label.text = f"Lvl: {value}"
        player = self._bound_player or getattr(self._view_model, '_player', None)
        if value > self._last_level and player and getattr(player, 'skill_points_available', 0) > 0:
            Clock.schedule_once(lambda dt: LevelUpPopup(player).open(), 0.05)
        self._last_level = value

    def _on_vm_health(self, instance, value) -> None:
        max_hp = self._view_model.max_health if self._view_model else 0
        self.hp_label.text = f"HP: {value}/{max_hp}"
        self._update_bar(self._hp_bar_container, self._hp_bar_fg, value, max_hp)

    def _on_vm_max_health(self, instance, value) -> None:
        health = self._view_model.health if self._view_model else 0
        self.hp_label.text = f"HP: {health}/{value}"
        self._update_bar(self._hp_bar_container, self._hp_bar_fg, health, value)

    def _on_vm_damage(self, instance, value) -> None:
        self.dmg_label.text = f"DMG: {value}"

    def _on_vm_defense(self, instance, value) -> None:
        self.def_label.text = f"DEF: {value}"

    def _on_vm_coins(self, instance, value) -> None:
        self.coins_label_small.text = f"COINS: {value}"

    def _on_vm_experience(self, instance, value) -> None:
        req = self._view_model.xp_required if self._view_model else 0
        self.xp_label.text = f"XP: {value}/{req}"
        self._update_bar(self._xp_bar_container, self._xp_bar_fg, value, req)

    def _on_vm_xp_required(self, instance, value) -> None:
        exp = self._view_model.experience if self._view_model else 0
        self.xp_label.text = f"XP: {exp}/{value}"
        self._update_bar(self._xp_bar_container, self._xp_bar_fg, exp, value)
