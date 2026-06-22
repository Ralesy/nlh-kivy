#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Overlay HUD с HP, статами, монетами и XP игрока."""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS
from ui.bindings.player_observer import PlayerViewModel


class GameHUD(BoxLayout):
    """Overlay HUD показывающий HP, DMG, DEF, монеты, XP и уровень игрока."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width = dp(620)  # Комфортная ширина под горизонтальный ряд
        self.height = dp(40)  # Компактная высота в один ряд
        self.orientation = 'horizontal'
        self.padding = [dp(12), dp(0), dp(12), dp(0)]
        self.spacing = dp(14)

        with self.canvas.before:
            Color(0.08, 0.08, 0.1, 0.7)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(*COLORS['border_gold'])
            self._border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(4)),
                width=dp(1.2)
            )
        self.bind(
            pos=lambda i, v: self._update_canvas(),
            size=lambda i, v: self._update_canvas()
        )

        # 1. Уровень
        self.level_label = Label(
            text='Lvl: -', font_size=dp(13), size_hint_x=None, width=dp(45), 
            halign='left', valign='middle', color=COLORS['text_light']
        )
        self.level_label.bind(size=self._trigger_label_render)
        self.add_widget(self.level_label)

        # 2. Полоса HP (RelativeLayout контейнер для удержания текста по центру)
        self._hp_bar_container = RelativeLayout(size_hint_x=None, width=dp(110), size_hint_y=None, height=dp(16))
        self._hp_bar_container.pos_hint = {'center_y': 0.5}
        with self._hp_bar_container.canvas.before:
            Color(0.2, 0.05, 0.05, 1)
            self._hp_bar_bg = RoundedRectangle(pos=(0, 0), size=self._hp_bar_container.size, radius=[dp(3)])
            Color(*COLORS['hp_red'])
            self._hp_bar_fg = RoundedRectangle(pos=(0, 0), size=(0, self._hp_bar_container.height), radius=[dp(3)])
        
        self.hp_label = Label(
            text='HP: -/-', font_size=dp(10), bold=True, color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self._hp_bar_container.add_widget(self.hp_label)
        self._hp_bar_container.bind(size=self._on_hp_container_size)
        self.add_widget(self._hp_bar_container)

        # 3. Полоса XP
        self._xp_bar_container = RelativeLayout(size_hint_x=None, width=dp(110), size_hint_y=None, height=dp(16))
        self._xp_bar_container.pos_hint = {'center_y': 0.5}
        with self._xp_bar_container.canvas.before:
            Color(0.05, 0.1, 0.2, 1)
            self._xp_bar_bg = RoundedRectangle(pos=(0, 0), size=self._xp_bar_container.size, radius=[dp(3)])
            Color(*COLORS['xp_purple'])
            self._xp_bar_fg = RoundedRectangle(pos=(0, 0), size=(0, self._xp_bar_container.height), radius=[dp(3)])
        
        self.xp_label = Label(
            text='XP: -/-', font_size=dp(10), bold=True, color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self._xp_bar_container.add_widget(self.xp_label)
        self._xp_bar_container.bind(size=self._on_xp_container_size)
        self.add_widget(self._xp_bar_container)

        # 4. Текстовые характеристики статов (DMG, DEF, COINS)
        label_kwargs = {
            'font_size': dp(13),
            'color': COLORS['text_light'],
            'size_hint_y': 1,
            'valign': 'middle',
            'halign': 'center'
        }
        self.dmg_label = Label(text='DMG: -', **label_kwargs)
        self.def_label = Label(text='DEF: -', **label_kwargs)
        self.coins_label = Label(text='COINS: -', **label_kwargs)

        for lbl in (self.dmg_label, self.def_label, self.coins_label):
            lbl.bind(size=self._trigger_label_render)

        self.add_widget(self.dmg_label)
        self.add_widget(self.def_label)
        self.add_widget(self.coins_label)

        # Внутреннее состояние (оригинальные переменные)
        self._view_model = None
        self._bound_player = None
        self._last_level = 0
        self._vm_bound = False

    def _trigger_label_render(self, instance, size):
        instance.text_size = instance.size

    def _update_canvas(self):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(4))

    def _on_hp_container_size(self, instance, size):
        self._hp_bar_bg.size = size
        if self._view_model:
            self._update_bar(self._hp_bar_container, self._hp_bar_fg, self._view_model.health, self._view_model.max_health)
        elif self._bound_player:
            self._update_bar(self._hp_bar_container, self._hp_bar_fg, self._bound_player.health, self._bound_player.max_health)

    def _on_xp_container_size(self, instance, size):
        self._xp_bar_bg.size = size
        if self._view_model:
            self._update_bar(self._xp_bar_container, self._xp_bar_fg, self._view_model.experience, self._view_model.xp_required)
        elif self._bound_player:
            self._update_bar(self._xp_bar_container, self._xp_bar_fg, self._bound_player.experience, self._bound_player.level * 100)

    # --- ОРИГИНАЛЬНОЕ API СВЯЗЫВАНИЯ ДАННЫХ ---
    
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
        """Отвязать HUD от текущей модели."""
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

    def _apply_stats(self, level, health, max_health, damage, defense, coins, experience, xp_required) -> None:
        try:
            self.level_label.text = f"Lvl: {level}"
            self.hp_label.text = f"HP: {health}/{max_health}"
            self._update_bar(self._hp_bar_container, self._hp_bar_fg, health, max_health)
            self.xp_label.text = f"XP: {experience}/{xp_required}"
            self._update_bar(self._xp_bar_container, self._xp_bar_fg, experience, xp_required)
            self.dmg_label.text = f"DMG: {damage}"
            self.def_label.text = f"DEF: {defense}"
            self.coins_label.text = f"COINS: {coins}"
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

    # --- ОРИГИНАЛЬНЫЕ СЛУШАТЕЛИ СОБЫТИЙ VIEWMODEL ---

    def _on_vm_level(self, instance, value) -> None:
        self.level_label.text = f"Lvl: {value}"
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
        self.coins_label.text = f"COINS: {value}"

    def _on_vm_experience(self, instance, value) -> None:
        req = self._view_model.xp_required if self._view_model else 0
        self.xp_label.text = f"XP: {value}/{req}"
        self._update_bar(self._xp_bar_container, self._xp_bar_fg, value, req)

    def _on_vm_xp_required(self, instance, value) -> None:
        exp = self._view_model.experience if self._view_model else 0
        self.xp_label.text = f"XP: {exp}/{value}"
        self._update_bar(self._xp_bar_container, self._xp_bar_fg, exp, value)