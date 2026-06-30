#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран таверны."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp

from ui.ui_styles import COLORS
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import add_back_to_map_button, add_back_to_city_button
from systems.npcs import NPCManager

class TavernScreen(Screen, KeyboardHandler):
    """Экран таверны."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        title = Label(
            text='🏰 ТАВЕРНА',
            font_size=dp(40),
            size_hint_y=None,
            height=dp(70),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        # Вкладки с улучшенным дизайном
        tab_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(55),
            spacing=dp(5)
        )
        
        btn_npcs = Button(
            text='🧙 NPC',
            size_hint_x=0.33,
            background_color=COLORS['stone_light'],
            font_size=dp(16)
        )
        btn_npcs.bind(on_press=lambda x: self.show_npcs())
        tab_layout.add_widget(btn_npcs)
        
        btn_companions = Button(
            text='🤝 Спутники',
            size_hint_x=0.33,
            background_color=COLORS['stone_light'],
            font_size=dp(16)
        )
        btn_companions.bind(
            on_press=lambda x: self.show_companions()
        )
        tab_layout.add_widget(btn_companions)
        
        btn_games = Button(
            text='🎲 Игры',
            size_hint_x=0.34,
            background_color=COLORS['stone_light'],
            font_size=dp(16)
        )
        btn_games.bind(on_press=lambda x: self.show_games())
        tab_layout.add_widget(btn_games)
        
        layout.add_widget(tab_layout)
        
        scroll = ScrollView()
        self.content_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None
        )
        self.content_layout.bind(
            minimum_height=self.content_layout.setter('height')
        )
        scroll.add_widget(self.content_layout)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        # add map and city return buttons in top-left
        self._btn_back_map = add_back_to_map_button(self, self.manager)
        add_back_to_city_button(self, self.manager)
        self.current_tab = 'npcs'
        self.npc_manager = None
        self.game_result_label = None
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
    
    def update_tavern(self):
        if not self.npc_manager:
            app = App.get_running_app()
            self.npc_manager = app.npc_manager
        self.show_npcs()
    
    def show_games(self):
        """Показать игры в таверне (Орёл/Решка)."""
        self.current_tab = 'games'
        self.content_layout.clear_widgets()
        
        app = App.get_running_app()
        if not app.game:
            return
        
        # Заголовок
        games_title = Label(
            text='🎲 ИГРЫ В ТАВЕРНЕ',
            font_size=dp(24),
            size_hint_y=None,
            height=dp(50),
            color=(0.9, 0.7, 0.3, 1)
        )
        self.content_layout.add_widget(games_title)
        
        # Показываем монеты (сохраняем как атрибут, чтобы можно было обновлять)
        self.coins_label = Label(
            text=f'Ваши монеты: {app.game.player.coins} 💰',
            font_size=dp(20),
            size_hint_y=None,
            height=dp(40),
            color=(0.9, 0.9, 0.3, 1)
        )
        self.content_layout.add_widget(self.coins_label)
        
        # Результат последней игры
        self.game_result_label = Label(
            text='',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(80),
            text_size=(None, None),
            halign='center',
            valign='middle',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.content_layout.add_widget(self.game_result_label)
        
        # Кнопка для игры Орёл/Решка
        btn_coinflip = Button(
            text='🪙 Орёл/Решка (1:1)',
            size_hint_y=None,
            height=dp(70),
            font_size=dp(18),
            background_color=COLORS['stone_light']
        )
        btn_coinflip.bind(on_press=self.on_tavern_coinflip)
        self.content_layout.add_widget(btn_coinflip)
    
    def on_tavern_coinflip(self, instance):
        """Запустить игру Орёл/Решка в таверне."""
        self.show_bet_dialog('coinflip')
    
    def show_bet_dialog(self, game_type):
        """Показать диалог ставки для игры."""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        bet_input = TextInput(text='10', multiline=False, input_filter='int')
        content.add_widget(Label(text='Ставка:', font_size=dp(16)))
        content.add_widget(bet_input)
        
        choice_layout = None
        if game_type == 'coinflip':
            choice_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
            btn_h = Button(text='🦅 Орёл', font_size=dp(14))
            btn_t = Button(text='🪙 Решка', font_size=dp(14))
            choice_layout.add_widget(btn_h)
            choice_layout.add_widget(btn_t)
            content.add_widget(choice_layout)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        
        def play(choice=None):
            try:
                bet = int(bet_input.text)
                app = App.get_running_app()
                if not app.game:
                    return
                
                from systems.shop_casino import Casino
                
                if game_type == 'coinflip':
                    if choice is None:
                        popup.dismiss()
                        return
                    ok, payout, msg = Casino.coinflip(bet, choice)
                    app.game.player.coins += payout
                    # обновляем результат и отображение монет
                    if self.game_result_label:
                        self.game_result_label.text = msg
                    try:
                        self.coins_label.text = f'Ваши монеты: {app.game.player.coins} 💰'
                    except Exception:
                        pass
                
                popup.dismiss()
            except ValueError:
                pass
        
        if game_type == 'coinflip':
            btn_h.bind(on_press=lambda x: play('h'))
            btn_t.bind(on_press=lambda x: play('t'))
        
        btn_cancel = Button(text='Отмена', font_size=dp(14))
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(btn_cancel)
        
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='🎲 Ставка',
            content=content,
            size_hint=(0.7, 0.5),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
    
    def show_npcs(self):
        """Показать список NPC в таверне."""
        self.current_tab = 'npcs'
        self.content_layout.clear_widgets()

        app = App.get_running_app()
        if not app.game:
            return

        npcs = list(self.npc_manager.npcs.values())
        
        for npc in npcs:
            npc_box = BoxLayout(
                orientation='vertical',
                spacing=dp(5),
                size_hint_y=None,
                height=dp(120),
                padding=dp(10)
            )

            # Имя и роль NPC
            npc_title = Label(
                text=f"🧙 {npc.__class__.__name__}",
                font_size=dp(18),
                size_hint_y=None,
                height=dp(35),
                text_size=(None, None),
                halign='center',
                valign='middle',
                color=(0.9, 0.7, 0.3, 1),
                bold=True
            )
            npc_box.add_widget(npc_title)

            # Описание
            desc_label = Label(
                text="📋 Нажмите для диалога",
                font_size=dp(14),
                size_hint_y=None,
                height=dp(30),
                text_size=(None, None),
                halign='center',
                valign='middle',
                color=(0.8, 0.8, 0.8, 1)
            )
            npc_box.add_widget(desc_label)

            # Кнопка диалога
            btn_talk = Button(
                text='💬 Разговор',
                size_hint_y=None,
                height=dp(45),
                background_color=COLORS['stone_light'],
                font_size=dp(16)
            )
            btn_talk.bind(
                on_press=lambda b, n=npc.id: self.talk_to_npc(n)
            )
            npc_box.add_widget(btn_talk)
            
            self.content_layout.add_widget(npc_box)
    
    def talk_to_npc(self, npc_id):
        """Открыть диалог с NPC."""
        npc = self.npc_manager.get_npc(npc_id)
        app = App.get_running_app()
        if app.npc_dialogue_screen:
            app.npc_dialogue_screen.show_npc_dialogue(npc)
            self.manager.current = 'npc_dialogue'
    
    def show_companions(self):
        """Показать спутников (старая система)."""
        self.current_tab = 'companions'
        self.content_layout.clear_widgets()
        
        app = App.get_running_app()
        if not app.game:
            return
        
        try:
            companions = app.game.tavern.COMPANIONS
        except (AttributeError, TypeError):
            empty_label = Label(
                text="Система спутников недоступна",
                font_size=dp(18),
                text_size=(None, None),
                halign='center',
                valign='center',
                color=(0.8, 0.8, 0.8, 1)
            )
            self.content_layout.add_widget(empty_label)
            return
        
        for i, (name, role) in enumerate(companions, 1):
            roles_desc = {
                "tank": "Танк (высокая защита)",
                "archer": "Лучник (высокий урон)",
                "healer": "Целитель (восстанавливает HP)"
            }
            
            # Получаем цену из ROLES
            from core.creatures import Companion
            role_data = Companion.ROLES.get(
                role, {"coins": 30}
            )
            price = role_data["coins"]
            
            comp_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(60)
            )
            comp_label = Label(
                text=(
                    f"{i}) {name} — "
                    f"{roles_desc.get(role, role)} "
                    f"(цена: {price} монет)"
                ),
                font_size=dp(18),
                size_hint_x=0.7
            )
            comp_layout.add_widget(comp_label)
            
            btn_hire = Button(
                text='Нанять',
                size_hint_x=0.3,
                background_color=COLORS['hp_green']
            )
            btn_hire.bind(on_press=lambda x, n=name, r=role: self.hire_companion(n, r))
            comp_layout.add_widget(btn_hire)
            
            self.content_layout.add_widget(comp_layout)
    
    def _refresh_after_quest_claim(self):
        """Обновить вкладку таверны и экран активных квестов после награды."""
        app = App.get_running_app()
        quests_screen = getattr(app, 'active_quests_screen', None)
        if quests_screen:
            quests_screen.update_quests()
        if self.current_tab == 'companions':
            self.show_companions()
        elif self.current_tab == 'games':
            self.show_games()
        else:
            self.show_npcs()

    def claim_quest(self, quest):
        """Выдать награду за квест и обновить UI (legacy-хук)."""
        app = App.get_running_app()
        if not app.game:
            return

        result = quest.claim(app.game.player)

        # --- Global Danger: снизить опасность за сдачу квеста ---
        danger_msg = ""
        if hasattr(app.game, 'danger_manager'):
            reduction = app.game.danger_manager.on_quest_completed()
            if reduction > 0:
                danger_msg = (
                    f"\n\n🛡️ Опасность снижена на "
                    f"{reduction:.0f}% "
                    f"(теперь "
                    f"{app.game.danger_manager.danger_level:.0f}%)"
                )

        # Уведомляем NPC о завершении квеста
        if hasattr(quest, 'npc_id') and quest.npc_id:
            npc_manager = getattr(app, 'npc_manager', None) or NPCManager()
            npc = npc_manager.get_npc(quest.npc_id)
            if npc and npc.current_quest == quest:
                npc.current_quest = None
                npc.completed_quests_count += 1

        popup = Popup(
            title='🎁 Награда получена!',
            content=Label(
                text=result + danger_msg,
                text_size=(None, None),
                halign='center',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
        self._refresh_after_quest_claim()
    
    def hire_companion(self, name, role):
        app = App.get_running_app()
        if not app.game:
            return
        
        from core.creatures import Companion
        role_data = Companion.ROLES.get(role, {"coins": 30})
        price = role_data["coins"]

        # Проверяем, есть ли уже активный спутник
        if app.game.player.companions:
            active_companion = app.game.player.companions[0]
            popup = Popup(
                title='⚠️ Уже есть активный спутник',
                content=Label(
                    text=f'У вас уже есть спутник: {active_companion.name}.\n'
                         f'Отпустите его в меню "Спутники", '
                         f'чтобы нанять нового.',
                    text_size=(None, None),
                    halign='center',
                    font_size=dp(18)
                ),
                size_hint=(0.75, 0.4),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        if app.game.player.coins < price:
            popup = Popup(
                title='Ошибка',
                content=Label(text=f'Недостаточно монет (нужно {price}).'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        app.game.player.coins -= price
        comp = Companion(name, role, level=max(1, app.game.player.level - 1))
        app.game.player.companions.append(comp)
        
        popup = Popup(
            title='✅ Успех',
            content=Label(
                text=f'{name} присоединился к вашей партии!\n\n'
                     f'Роль: {comp.role}\n'
                     f'HP: {comp.health}/{comp.max_health}\n'
                     f'Урон: {comp.damage}',
                text_size=(None, None),
                halign='center',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
        self.show_companions()
