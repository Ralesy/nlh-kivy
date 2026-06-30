#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NpcDialoguePopup — всплывающее окно диалога с NPC (квесты).

Открывается поверх локации/карты, не затемняет фон.
При отходе от NPC диалог автоматически закрывается.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle

from ui.ui_styles import COLORS
from systems.npcs import QuestState, QuestType


class _DialogueButton(Button):
    """Стилизованная кнопка для диалога."""

    def __init__(self, text="", bg_color=None, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.text = text
        self.font_size = dp(13)
        self.size_hint_y = None
        self.height = dp(38)
        self.background_normal = ''
        self.background_down = ''
        self.bold = True
        self.color = (1, 1, 1, 1)
        self._bg_color = bg_color or (0.25, 0.30, 0.40, 0.9)
        self._update_canvas()
        self.bind(pos=lambda i, v: self._update_canvas(), size=lambda i, v: self._update_canvas())

    def _update_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(0.4, 0.35, 0.25, 0.5)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(4)), width=dp(1))


class NpcDialoguePopup(BoxLayout):
    """Всплывающее окно диалога с NPC (левая сторона)."""

    def __init__(self, npc, npc_entity=None, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
        self.padding = dp(8)
        self.npc = npc
        self.npc_entity = npc_entity  # для отслеживания расстояния
        self.on_done = on_done
        self.current_quest = None

        # Фон со скруглёнными углами
        with self.canvas.before:
            Color(0.08, 0.1, 0.15, 0.94)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLORS['border_gold'])
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)),
                width=dp(1.2),
            )
        self.bind(
            pos=lambda i, v: self._update_bg(),
            size=lambda i, v: self._update_bg(),
        )

        # Название NPC
        self.npc_name = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(32),
            color=COLORS['gold_light'],
            bold=True,
            halign='left',
            valign='middle',
        )
        self.add_widget(self.npc_name)

        # Текст диалога (скролл)
        scroll = ScrollView(size_hint_y=1, bar_width=dp(4))
        self.dialogue_text = Label(
            text='',
            font_size=dp(12),
            size_hint_y=None,
            text_size=(dp(300), None),
            halign='left',
            valign='top',
            color=COLORS['text_light'],
        )
        self.dialogue_text.bind(texture_size=self.dialogue_text.setter('size'))
        scroll.add_widget(self.dialogue_text)
        self.add_widget(scroll)

        # Кнопки
        self.btn_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(4),
            padding=(dp(2), dp(4)),
        )
        self.btn_layout.bind(minimum_height=self.btn_layout.setter('height'))

        self.btn_accept = _DialogueButton(
            text='[Принять квест]',
            bg_color=(0.25, 0.45, 0.25, 0.9),
        )
        self.btn_accept.bind(on_press=self._on_accept_quest)
        self.btn_layout.add_widget(self.btn_accept)

        self.btn_claim = _DialogueButton(
            text='[Получить награду]',
            bg_color=(0.45, 0.40, 0.20, 0.9),
        )
        self.btn_claim.bind(on_press=self._on_claim_reward)
        self.btn_layout.add_widget(self.btn_claim)

        self.btn_reject = _DialogueButton(
            text='[Отклонить]',
            bg_color=(0.45, 0.20, 0.15, 0.9),
        )
        self.btn_reject.bind(on_press=self._on_reject_quest)
        self.btn_layout.add_widget(self.btn_reject)

        self.btn_back = _DialogueButton(
            text='[Вернуться]',
            bg_color=(0.30, 0.28, 0.26, 0.9),
        )
        self.btn_back.bind(on_press=self._close)
        self.btn_layout.add_widget(self.btn_back)

        self.add_widget(self.btn_layout)

        self._show_dialogue()

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _show_dialogue(self):
        self.current_quest = None
        dialogue = self.npc.get_introduction()

        app = App.get_running_app()
        player = app.game.player if app.game else None

        has_active_quest_from_npc = False
        if player:
            for quest in player.accepted_quests:
                if quest.npc_id == self.npc.id:
                    has_active_quest_from_npc = True
                    break

        self.btn_accept.disabled = True
        self.btn_claim.disabled = True
        self.btn_reject.disabled = True

        if self.npc.is_quest_active():
            quest = self.npc.current_quest
            if quest.state == QuestState.ACTIVE:
                if quest.is_complete():
                    dialogue += '\n\n[КВЕСТ ВЫПОЛНЕН!]\n'
                    dialogue += f'Награда: {quest.reward_gold} монет, {quest.reward_xp} XP\n'
                    self.current_quest = quest
                    self.btn_claim.disabled = False
                else:
                    dialogue += '\n\n[АКТИВНЫЙ КВЕСТ]\n'
                    dialogue += f'{quest.progress_display()}\n'
                    dialogue += f'Награда: {quest.reward_gold} монет, {quest.reward_xp} XP\n'
                    self.current_quest = None
            elif quest.state == QuestState.NOT_TAKEN:
                dialogue += '\n\n[ПРЕДЛОЖЕНИЕ]\n'
                if quest.quest_type == QuestType.KILL_ENEMIES:
                    dialogue += f'Задание: Убить {quest.required_count} {quest.target}\n'
                elif quest.quest_type == QuestType.COLLECT_ITEM:
                    dialogue += f'Задание: Найти {quest.required_count} {quest.target}\n'
                dialogue += f'Награда: {quest.reward_gold} монет, {quest.reward_xp} XP\n'
                self.current_quest = quest
                self.btn_accept.disabled = False
                self.btn_reject.disabled = False
        else:
            if has_active_quest_from_npc:
                dialogue += '\n\nУ вас уже есть активный квест от этого NPC.\n'
                dialogue += 'Завершите его, чтобы взять новый!\n'
                self.current_quest = None
            else:
                quest = self.npc.generate_quest()
                self.npc.offer_quest(quest)
                dialogue += '\n\n[ПРЕДЛОЖЕНИЕ]\n'
                if quest.quest_type == QuestType.KILL_ENEMIES:
                    dialogue += f'Задание: Убить {quest.required_count} {quest.target}\n'
                elif quest.quest_type == QuestType.COLLECT_ITEM:
                    dialogue += f'Задание: Найти {quest.required_count} {quest.target}\n'
                dialogue += f'Награда: {quest.reward_gold} монет, {quest.reward_xp} XP\n'
                self.current_quest = quest
                self.btn_accept.disabled = False
                self.btn_reject.disabled = False

        self.dialogue_text.text = dialogue

    def _on_accept_quest(self, *_args):
        app = App.get_running_app()
        if not app.game or not app.game.player or not self.current_quest:
            return
        self.npc.accept_quest()
        app.game.player.accepted_quests.append(self.current_quest)

        popup = Popup(
            title='Квест принят!',
            content=Label(text='Вы приняли квест.', font_size=dp(16)),
            size_hint=(0.6, 0.25),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)
        self._close()

    def _on_reject_quest(self, *_args):
        if self.current_quest:
            self.npc.reject_quest()
        self._close()

    def _on_claim_reward(self, *_args):
        if not self.current_quest or not self.current_quest.is_complete():
            return
        app = App.get_running_app()
        if not app.game or not app.game.player:
            return
        player = app.game.player
        player.coins += self.current_quest.reward_gold
        player.add_experience(self.current_quest.reward_xp)

        # --- Global Danger: снизить опасность за сдачу квеста ---
        danger_msg = ""
        if hasattr(app.game, 'danger_manager'):
            reduction = app.game.danger_manager.on_quest_completed()
            if reduction > 0:
                danger_msg = (
                    f"\n\nОпасность снижена на "
                    f"{reduction:.0f}% "
                    f"(теперь "
                    f"{app.game.danger_manager.danger_level:.0f}%)"
                )

        if self.current_quest in player.accepted_quests:
            player.accepted_quests.remove(self.current_quest)
        self.npc.current_quest = None
        self.current_quest = None

        popup = Popup(
            title='Награда получена!',
            content=Label(
                text='Квест выполнен! Вы получили награду.' + danger_msg,
                font_size=dp(16),
            ),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.5)
        self._close()

    def _close(self, *_args):
        if self.on_done:
            self.on_done()