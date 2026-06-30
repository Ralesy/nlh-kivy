#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран активных квестов."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import add_back_to_map_button

class ActiveQuestsScreen(Screen, KeyboardHandler):
    """Экран активных квестов."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(12)
        )
        
        # Фон
        with main_layout.canvas.before:
            Color(0.15, 0.2, 0.25, 1)
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(
                    self.bg_rect, 'size', i.size
                ),
                pos=lambda i, v: setattr(
                    self.bg_rect, 'pos', i.pos
                )
            )
        
        # Заголовок
        title_label = Label(
            text='[Квесты] АКТИВНЫЕ КВЕСТЫ',
            font_size=dp(28),
            size_hint_y=None,
            height=dp(60),
            color=(0.9, 0.7, 0.1, 1),
            bold=True
        )
        main_layout.add_widget(title_label)
        
        # Список квестов
        scroll = ScrollView()
        self.quests_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        self.quests_layout.bind(
            minimum_height=self.quests_layout.setter('height')
        )
        scroll.add_widget(self.quests_layout)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        # Кнопка назад
        # replace old bottom back with edge 'Back to Map' button
        self._btn_back_map = add_back_to_map_button(self, self.manager)
        self.bind_keyboard()

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action in ("exit_location", "open_menu", "open_locations") and pressed:
            try:
                if getattr(self, "_btn_back_map", None):
                    self._btn_back_map.trigger_action(duration=0)
                    return True
            except Exception:
                pass
        return False
    
    def update_quests(self):
        """Обновить список активных квестов."""
        app = App.get_running_app()
        if not app.game or not app.game.player:
            return
        
        self.quests_layout.clear_widgets()
        
        player = app.game.player
        if not player.accepted_quests:
            empty_label = Label(
                text="Нет активных квестов.\n"
                     "Поговорите с NPC в таверне!",
                font_size=dp(18),
                text_size=(None, None),
                halign='center',
                valign='center',
                color=(0.8, 0.8, 0.8, 1)
            )
            self.quests_layout.add_widget(empty_label)
            return
        
        for quest in player.accepted_quests:
            quest_box = BoxLayout(
                orientation='vertical',
                spacing=dp(8),
                size_hint_y=None,
                height=dp(130),
                padding=dp(10)
            )
            
            # Фон квеста
            with quest_box.canvas.before:
                Color(0.3, 0.3, 0.35, 1)
                quest_bg = Rectangle()
                quest_box.bind(
                    pos=lambda i, v: setattr(
                        quest_bg, 'pos', i.pos
                    ),
                    size=lambda i, v: setattr(
                        quest_bg, 'size', i.size
                    )
                )
            
            # Заголовок квеста
            quest_title = Label(
                text=f"[Свиток] {quest.title.upper()}",
                font_size=dp(16),
                size_hint_y=None,
                height=dp(30),
                text_size=(None, None),
                halign='left',
                valign='top',
                color=(0.9, 0.9, 0.3, 1),
                bold=True
            )
            quest_box.add_widget(quest_title)
            
            # Описание
            quest_desc = Label(
                text=quest.description,
                font_size=dp(13),
                size_hint_y=None,
                height=dp(30),
                text_size=(None, None),
                halign='left',
                valign='top',
                color=(0.8, 0.8, 0.8, 1)
            )
            quest_box.add_widget(quest_desc)
            
            # Прогресс
            progress_label = Label(
                text=quest.progress_display(),
                font_size=dp(13),
                size_hint_y=None,
                height=dp(25),
                text_size=(None, None),
                halign='left',
                valign='center',
                color=(0.7, 0.9, 0.7, 1)
            )
            quest_box.add_widget(progress_label)
            
            # Награда
            reward_text = (
                f"[Монеты] {quest.reward_gold} монет | "
                f"[Опыт] {quest.reward_xp} XP"
            )
            reward_label = Label(
                text=reward_text,
                font_size=dp(12),
                size_hint_y=None,
                height=dp(20),
                text_size=(None, None),
                halign='left',
                valign='center',
                color=(0.9, 0.7, 0.3, 1)
            )
            quest_box.add_widget(reward_label)
            
            self.quests_layout.add_widget(quest_box)
