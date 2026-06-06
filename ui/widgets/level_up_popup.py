#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Popup распределения очков навыков при повышении уровня."""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp


class LevelUpPopup(Popup):
    """Popup для распределения доступных очков навыков."""

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Распределение очков'
        self.size_hint = (0.7, 0.7)
        self.auto_dismiss = False
        self.player = player
        self._paused_local = False

        root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        self.info_label = Label(text=self._info_text(), size_hint_y=None, height=dp(40))
        root.add_widget(self.info_label)

        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=1)

        self.skill_rows = {}
        for skill in ['endurance', 'strength', 'agility', 'luck', 'trade']:
            name = skill.capitalize()
            lbl = Label(
                text=f"{name}: {self.player.skill_points_allocated.get(skill, 0)}",
                halign='left',
            )
            btn_box = BoxLayout(orientation='horizontal', size_hint_x=None, width=dp(160), spacing=dp(6))
            minus = Button(text='−', size_hint_x=None, width=dp(50))
            plus = Button(text='+', size_hint_x=None, width=dp(50))
            minus.bind(on_press=lambda inst, s=skill: self._deallocate(s))
            plus.bind(on_press=lambda inst, s=skill: self._allocate(s))
            btn_box.add_widget(minus)
            btn_box.add_widget(plus)
            grid.add_widget(lbl)
            grid.add_widget(btn_box)
            self.skill_rows[skill] = lbl

        root.add_widget(grid)

        bottom = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btn_done = Button(text='Готово')
        btn_auto = Button(text='Распределить автоматически')
        btn_done.bind(on_press=lambda inst: self.dismiss())
        btn_auto.bind(on_press=lambda inst: self._auto_allocate())
        bottom.add_widget(btn_auto)
        bottom.add_widget(btn_done)
        root.add_widget(bottom)

        self.content = root

    def _info_text(self):
        pts = getattr(self.player, 'skill_points_available', 0)
        return f"Доступно очков для распределения: {pts}"

    def _refresh(self):
        self.info_label.text = self._info_text()
        for sk, lbl in self.skill_rows.items():
            lbl.text = f"{sk.capitalize()}: {self.player.skill_points_allocated.get(sk, 0)}"

    def _allocate(self, skill):
        if self.player.allocate_skill_point(skill):
            self._refresh()

    def _deallocate(self, skill):
        if self.player.deallocate_skill_point(skill):
            self._refresh()

    def _auto_allocate(self):
        order = ['strength', 'endurance', 'agility', 'luck', 'trade']
        while getattr(self.player, 'skill_points_available', 0) > 0:
            for s in order:
                if self.player.skill_points_available <= 0:
                    break
                self.player.allocate_skill_point(s)
        self._refresh()

    def on_open(self):
        local_screen = getattr(App.get_running_app(), 'local_location_screen', None)
        if local_screen and hasattr(local_screen, '_paused') and not local_screen._paused:
            local_screen.pause_game()
            self._paused_local = True

    def on_dismiss(self):
        if self._paused_local:
            local_screen = getattr(App.get_running_app(), 'local_location_screen', None)
            if local_screen:
                local_screen.resume_game()
            self._paused_local = False