#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран диалога с NPC."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp

from ui.ui_styles import COLORS
from systems.npcs import QuestState, QuestType


def _tavern_return_screen():
    """Экран возврата из диалога NPC."""
    app = App.get_running_app()
    if getattr(app, "return_to_local_location", False):
        return "local_location"
    return "tavern"


class NPCDialogueScreen(Screen):
    """Экран диалога с NPC."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_npc = None
        self.current_quest = None
        
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
        self.npc_name = Label(
            text='',
            font_size=dp(24),
            size_hint_y=None,
            height=dp(50),
            color=(0.9, 0.7, 0.1, 1),
            bold=True
        )
        main_layout.add_widget(self.npc_name)
        
        # Текст диалога
        scroll = ScrollView()
        self.dialogue_text = Label(
            text='',
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            font_size=dp(16),
            color=(0.9, 0.9, 0.9, 1)
        )
        self.dialogue_text.bind(
            texture_size=self.dialogue_text.setter('size')
        )
        scroll.add_widget(self.dialogue_text)
        main_layout.add_widget(scroll)
        
        # Кнопки
        btn_layout = BoxLayout(
            spacing=dp(10),
            size_hint_y=None
        )
        btn_layout.height = dp(150)

        self.btn_accept_quest = Button(
            text='[Да] Принять квест',
            size_hint_y=None,
            height=dp(50),
            background_color=COLORS['hp_green']
        )
        self.btn_accept_quest.bind(
            on_press=self.on_accept_quest
        )
        btn_layout.add_widget(self.btn_accept_quest)

        self.btn_claim_reward = Button(
            text='🎁 Получить награду',
            size_hint_y=None,
            height=dp(50),
            background_color=COLORS['gold']
        )
        self.btn_claim_reward.bind(
            on_press=self.on_claim_reward
        )
        btn_layout.add_widget(self.btn_claim_reward)

        self.btn_reject_quest = Button(
            text='[Нет] Отклонить',
            size_hint_y=None,
            height=dp(50),
            background_color=COLORS['hp_red']
        )
        self.btn_reject_quest.bind(
            on_press=self.on_reject_quest
        )
        btn_layout.add_widget(self.btn_reject_quest)

        btn_back = Button(
            text='← Вернуться',
            size_hint_y=None,
            height=dp(50),
            background_color=COLORS['stone_light']
        )
        btn_back.bind(on_press=self.on_back)
        btn_layout.add_widget(btn_back)

        # Initially disable buttons
        self.btn_accept_quest.disabled = True
        self.btn_claim_reward.disabled = True
        self.btn_reject_quest.disabled = True

        main_layout.add_widget(btn_layout)
        self.add_widget(main_layout)
    
    def show_npc_dialogue(self, npc):
        """Показать диалог NPC."""
        self.current_npc = npc
        self.npc_name.text = f"🧙 {npc.__class__.__name__}"

        # Получаем текст диалога
        dialogue = npc.get_introduction()

        app = App.get_running_app()
        player = app.game.player if app.game else None
        
        # Проверяем, есть ли активный квест у этого NPC у игрока
        has_active_quest_from_npc = False
        if player:
            for quest in player.accepted_quests:
                if quest.npc_id == npc.id:
                    has_active_quest_from_npc = True
                    break

        # Проверяем, есть ли квест у NPC
        if npc.is_quest_active():
            quest = npc.current_quest
            if quest.state == QuestState.ACTIVE:
                if quest.is_complete():
                    dialogue += (
                        f"\n\n[Победа] КВЕСТ ВЫПОЛНЕН!\n"
                        f"Награда: {quest.reward_gold} монет, "
                        f"{quest.reward_xp} XP\n"
                    )
                    self.current_quest = quest
                    self.btn_claim_reward.disabled = False
                    self.btn_accept_quest.disabled = True
                    self.btn_reject_quest.disabled = True
                else:
                    dialogue += (
                        f"\n\n[Свиток] АКТИВНЫЙ КВЕСТ:\n"
                        f"Тип: {quest.quest_type.value}\n"
                        f"{quest.progress_display()}\n"
                        f"Награда: {quest.reward_gold} монет, "
                        f"{quest.reward_xp} XP\n"
                    )
                    self.current_quest = None
                    self.btn_claim_reward.disabled = True
                    self.btn_accept_quest.disabled = True
                    self.btn_reject_quest.disabled = True
            elif quest.state == QuestState.NOT_TAKEN:
                dialogue += (
                    f"\n\n[Свиток] ПРЕДЛОЖЕНИЕ:\n"
                    f"Тип: {quest.quest_type.value}\n"
                )

                if quest.quest_type == QuestType.KILL_ENEMIES:
                    dialogue += f"Задание: Убить {quest.required_count} {quest.target}\n"
                elif quest.quest_type == QuestType.COLLECT_ITEM:
                    dialogue += f"Задание: Найти {quest.required_count} {quest.target}\n"

                dialogue += (
                    f"Награда: {quest.reward_gold} монет, "
                    f"{quest.reward_xp} XP\n"
                )

                self.current_quest = quest
                self.btn_claim_reward.disabled = True
                self.btn_accept_quest.disabled = False
                self.btn_reject_quest.disabled = False
        else:
            # Проверяем есть ли активный квест от этого NPC
            if has_active_quest_from_npc:
                dialogue += (
                    f"\n\n[Квесты] У вас уже есть активный квест "
                    f"от этого NPC.\n"
                    f"Завершите его, чтобы взять новый!\n"
                )
                self.current_quest = None
                self.btn_claim_reward.disabled = True
                self.btn_accept_quest.disabled = True
                self.btn_reject_quest.disabled = True
            else:
                # Генерируем новый квест и предлагаем его NPC
                quest = npc.generate_quest()
                npc.offer_quest(quest)  # Устанавливаем квест у NPC

                dialogue += (
                    f"\n\n[Свиток] ПРЕДЛОЖЕНИЕ:\n"
                    f"Тип: {quest.quest_type.value}\n"
                )

                if quest.quest_type == QuestType.KILL_ENEMIES:
                    dialogue += f"Задание: Убить {quest.required_count} {quest.target}\n"
                elif quest.quest_type == QuestType.COLLECT_ITEM:
                    dialogue += f"Задание: Найти {quest.required_count} {quest.target}\n"

                dialogue += (
                    f"Награда: {quest.reward_gold} монет, "
                    f"{quest.reward_xp} XP\n"
                )

                self.current_quest = quest
                self.btn_claim_reward.disabled = True
                self.btn_accept_quest.disabled = False
                self.btn_reject_quest.disabled = False

        self.dialogue_text.text = dialogue
    
    def on_accept_quest(self, instance):
        """Принять квест."""
        app = App.get_running_app()
        if not app.game or not app.game.player or not self.current_quest:
            return

        # Принимаем квест у NPC
        self.current_npc.accept_quest()
        app.game.player.accepted_quests.append(self.current_quest)

        npc_class_name = self.current_npc.__class__.__name__

        # Подсказка о снижении опасности
        danger_hint = ""
        if hasattr(app.game, 'danger_manager'):
            dm = app.game.danger_manager
            from systems.danger_manager import QUEST_DANGER_REDUCTION
            danger_hint = (
                f"\n\n[Защита] Сдача квеста снизит опасность "
                f"на {QUEST_DANGER_REDUCTION:.0f}% "
                f"(сейчас: {dm.danger_level:.0f}%)"
            )

        popup = Popup(
            title='[Да] Квест принят!',
            content=Label(
                text=f"Вы приняли квест от {npc_class_name}" + danger_hint,
                text_size=(None, None),
                halign='center',
                valign='middle',
                font_size=dp(16),
            ),
            size_hint=(0.65, 0.35),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        self.on_back(instance)

    def on_reject_quest(self, instance):
        """Отклонить квест."""
        if self.current_quest:
            # Отклоняем квест у NPC
            self.current_npc.reject_quest()

        popup = Popup(
            title='[Нет] Квест отклонен',
            content=Label(
                text='Может быть в другой раз.',
                font_size=dp(18)
            ),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        Clock.schedule_once(
            lambda dt: (
                popup.dismiss(),
                setattr(self.manager, "current", _tavern_return_screen()),
            ),
            1.5,
        )

    def on_claim_reward(self, instance):
        """Получить награду за квест."""
        if not self.current_quest or not self.current_quest.is_complete():
            return

        app = App.get_running_app()
        if not app.game or not app.game.player:
            return
        # Дать награду
        player = app.game.player
        player.coins += self.current_quest.reward_gold
        level_up_msgs = player.add_experience(
            self.current_quest.reward_xp
        )

        # --- Global Danger: снизить опасность за сдачу квеста ---
        danger_msg = ""
        if hasattr(app.game, 'danger_manager'):
            reduction = app.game.danger_manager.on_quest_completed()
            if reduction > 0:
                danger_msg = (
                    f"\n\n[Защита] Опасность снижена на "
                    f"{reduction:.0f}% "
                    f"(теперь "
                    f"{app.game.danger_manager.danger_level:.0f}%)"
                )

        # Удалить квест из списка принятых
        if self.current_quest in player.accepted_quests:
            player.accepted_quests.remove(self.current_quest)

        # Очистить квест у NPC
        self.current_npc.current_quest = None
        self.current_quest = None

        popup = Popup(
            title='🎁 Награда получена!',
            content=Label(
                text=(
                    'Квест выполнен! '
                    'Вы получили награду.'
                    + danger_msg
                ),
                font_size=dp(18)
            ),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        Clock.schedule_once(
            lambda dt: (
                popup.dismiss(),
                setattr(self.manager, "current", _tavern_return_screen()),
            ),
            1.5,
        )

    def on_back(self, instance):
        """Вернуться в таверну (проходимую или экран списка)."""
        self.manager.current = _tavern_return_screen()
