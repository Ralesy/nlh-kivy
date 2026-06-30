#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран боя."""

import os

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp

from ui.ui_styles import COLORS, BUTTONS_DIR
from core.combat.battle_service import BattleService

class BattleScreen(Screen):
    """Экран боя."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.battlefield = None
        self.service = None
        self.event_message = None
        self.is_processing_turn = False  # Флаг блокировки действий во время обработки хода
        self.from_local_location = False
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Устанавливаем темный фон для боевого экрана
        with layout.canvas.before:
            Color(0.15, 0.15, 0.2, 1)  # Темно-синий фон
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )
        
        # Сообщение о событии
        self.event_label = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(50),
            text_size=(None, None),
            color=COLORS['gold']  # Желтый цвет для событий
        )
        layout.add_widget(self.event_label)
        
        # Информация о бое с улучшенным дизайном
        self.battle_info = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(120),
            text_size=(None, None),
            halign='left',
            valign='top',
            color=COLORS['text_light']  # Светлый цвет текста
        )
        layout.add_widget(self.battle_info)
        
        # Список врагов
        scroll = ScrollView()
        self.enemies_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        self.enemies_layout.bind(minimum_height=self.enemies_layout.setter('height'))
        scroll.add_widget(self.enemies_layout)
        layout.add_widget(scroll)
        
        # Лог боя с улучшенным дизайном
        log_header = Label(
            text="📜 ЛОГ БОЯ:",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30),
            color=COLORS['stone']
        )
        layout.add_widget(log_header)
        
        scroll_log = ScrollView()
        self.log_label = Label(
            text='',
            font_size=dp(15),
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            color=COLORS['text_light']
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll_log.add_widget(self.log_label)
        layout.add_widget(scroll_log)
        
        # Кнопки действий
        actions_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(180))
        
        self.btn_inventory = Button(
            text='🎒 Инвентарь',
            font_size=dp(18),
            background_normal=os.path.join(BUTTONS_DIR, 'inventory.png'),
            background_down=os.path.join(BUTTONS_DIR, 'inventory.png'),
            background_color=(1, 1, 1, 1)
        )
        self.btn_inventory.bind(on_press=self.on_open_inventory)
        actions_layout.add_widget(self.btn_inventory)
        
        self.btn_ability = Button(
            text='⚔️ Способность',
            font_size=dp(18),
            background_color=COLORS['hp_red']
        )
        self.btn_ability.bind(on_press=self.on_ability_use)
        actions_layout.add_widget(self.btn_ability)
        
        self.btn_escape = Button(
            text='🏃 Убежать',
            font_size=dp(18),
            background_color=COLORS['gold']
        )
        self.btn_escape.bind(on_press=self.on_escape)
        actions_layout.add_widget(self.btn_escape)
        
        self.btn_surrender = Button(
            text='🏳️ Сдаться',
            font_size=dp(18),
            background_color=COLORS['hp_red']
        )
        self.btn_surrender.bind(on_press=self.on_surrender)
        actions_layout.add_widget(self.btn_surrender)
        
        layout.add_widget(actions_layout)
        
        self.add_widget(layout)
    
    def start_battle(self, battlefield, event_message=None):
        """Начало боя."""
        self.battlefield = battlefield
        self.service = BattleService(battlefield)
        self.event_message = event_message
        self.log_label.text = ''
        self.is_processing_turn = False
        self.update_battle_display()
        
        if event_message:
            self.event_label.text = f"⚡ {event_message}"
        else:
            self.event_label.text = ''
        
        self.add_log(f"Битва началась! Враги: {', '.join(e.name for e in battlefield.enemies)}")
        Clock.schedule_once(lambda dt: self.enemy_turn(), 0.5)
    
    def update_battle_display(self):
        """Обновление отображения боя."""
        if not self.battlefield:
            return
        
        p = self.battlefield.player
        
        # Улучшенное отображение информации о бое
        companions_info = ""
        if p.companions:
            alive_companions = [c for c in p.companions if c.is_alive]
            if alive_companions:
                comp_text = ", ".join(
                    [f"{c.name}({c.health}/{c.max_health})"
                     for c in alive_companions]
                )
                companions_info = f"\n🤝 Спутники: {comp_text}"
            else:
                companions_info = "\n🤝 Спутники: Все выбыли"
        
        self.battle_info.text = (
            f"⚔️ Раунд {self.battlefield.round + 1}\n"
            f"💚 Ваш HP: {p.health}/{p.max_health} | ⚔️ DMG: {p.damage} | 🛡️ DEF: {p.defense}"
            f"{companions_info}"
        )
        
        # Обновление списка врагов с улучшенным дизайном
        self.enemies_layout.clear_widgets()
        enemies = self.battlefield.alive_enemies()
        
        # Заголовок
        header = Label(
            text="👹 ВРАГИ (нажмите для атаки):",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.enemies_layout.add_widget(header)
        
        for i, enemy in enumerate(enemies):
            # Цвет кнопки зависит от здоровья врага
            hp_percent = enemy.health / enemy.max_health if enemy.max_health > 0 else 0
            if hp_percent > 0.6:
                bg_color = (0.7, 0.3, 0.3, 1)  # Красный для здоровых
            elif hp_percent > 0.3:
                bg_color = (0.8, 0.6, 0.2, 1)  # Оранжевый для раненых
            else:
                bg_color = (0.5, 0.5, 0.5, 1)  # Серый для почти мертвых
            
            btn = Button(
                text=(
                    f"⚔️ {enemy.name}\n"
                    f"💚 HP: {enemy.health}/{enemy.max_health} | ⚔️ DMG: {enemy.damage}"
                    f" | 🛡️ DEF: {enemy.defense}"
                ),
                size_hint_y=None,
                height=dp(60),
                font_size=dp(16),
                disabled=self.is_processing_turn,
                background_color=bg_color,
            )
            btn.bind(on_press=lambda x, idx=i: self.attack_enemy(idx))
            self.enemies_layout.add_widget(btn)
        
        # Отключаем/включаем кнопки действий
        self.btn_inventory.disabled = self.is_processing_turn
        self.btn_escape.disabled = self.is_processing_turn
        self.btn_surrender.disabled = self.is_processing_turn
        
        # Кнопка способности: отключена если способность уже использована или нет оружия
        ability_disabled = (
            self.is_processing_turn or 
            not self.battlefield.player.weapon or
            not hasattr(self.battlefield.player.weapon, 'ability') or
            not self.battlefield.player.weapon.ability or
            self.battlefield.player.weapon.ability.ability_type != "active" or
            self.battlefield.ability_used_this_battle
        )
        self.btn_ability.disabled = ability_disabled
        
        # Обновляем текст кнопки способности с названием
        if (not ability_disabled and 
            self.battlefield.player.weapon and 
            hasattr(self.battlefield.player.weapon, 'ability') and
            self.battlefield.player.weapon.ability):
            ability_name = self.battlefield.player.weapon.ability.name
            self.btn_ability.text = f"⚔️ {ability_name}"
        elif self.battlefield.ability_used_this_battle:
            self.btn_ability.text = "⚔️ Способность (использована)"
        else:
            self.btn_ability.text = "⚔️ Способность"
    
    def add_log(self, message):
        """Добавление сообщения в лог."""
        self.log_label.text += message + '\n'
        self.log_label.texture_update()
    
    def attack_enemy(self, enemy_index):
        """Атака врага."""
        # Блокируем повторные клики
        if self.is_processing_turn:
            return
        
        if not self.battlefield or self.battlefield.is_over():
            return
        
        # Устанавливаем флаг обработки
        self.is_processing_turn = True
        self.update_battle_display()

        result, killed = self.service.player_attack_enemy(enemy_index)
        self.add_log(result)
        self.update_battle_display()
        
        if self.battlefield.is_over():
            self.is_processing_turn = False
            self.end_battle()
        else:
            Clock.schedule_once(lambda dt: self.enemy_turn(), 1.0)
    
    def on_open_inventory(self, instance):
        """Открытие инвентаря в бою."""
        if self.is_processing_turn:
            return
        
        if not self.battlefield:
            return
        
        app = App.get_running_app()
        app.battle_inventory_screen.update_inventory(self.battlefield)
        self.manager.current = 'battle_inventory'
    
    def on_escape(self, instance):
        """Попытка побега."""
        if self.is_processing_turn:
            return

        if not self.battlefield:
            return

        # Устанавливаем флаг обработки
        self.is_processing_turn = True
        self.update_battle_display()

        success, logs = self.service.attempt_escape()
        for log in logs:
            self.add_log(f"→ {log}")

        if success:
            self.add_log("\nВы успешно сбежали!")
            self.is_processing_turn = False
            Clock.schedule_once(lambda dt: self.return_to_game(), 1.5)
        else:
            # Проверяем, закончился ли бой после урона от неудачного побега
            if self.battlefield.is_over():
                if not self.battlefield.player.is_alive:
                    self.add_log("\n💀 Вы были повержены!")
                    self.is_processing_turn = False
                    Clock.schedule_once(lambda dt: self.return_to_game(False), 2.0)
                else:
                    # Все враги мертвы (редкий случай)
                    self.is_processing_turn = False
                    self.end_battle()
            else:
                # Бой продолжается, враги атакуют
                Clock.schedule_once(lambda dt: self.enemy_turn(), 1.0)
    
    def on_surrender(self, instance):
        """Сдача."""
        if self.is_processing_turn:
            return
        
        self.is_processing_turn = True
        self.update_battle_display()
        message, _ = self.service.surrender()
        self.add_log(f"\n{message}")
        Clock.schedule_once(lambda dt: self.return_to_game(False), 1.5)
    
    def on_ability_use(self, instance):
        """Использование способности оружия."""
        # Блокируем повторные клики
        if self.is_processing_turn:
            return
        
        if not self.battlefield or self.battlefield.is_over():
            return
        
        # Проверяем наличие способности
        weapon = self.battlefield.player.weapon
        if (not weapon or not hasattr(weapon, 'ability') or
                not weapon.ability or
                weapon.ability.ability_type != "active"):
            self.add_log("❌ Нет активной способности для использования!")
            return
        
        if self.battlefield.ability_used_this_battle:
            self.add_log("❌ Способность уже использована в этой битве!")
            return
        
        # Устанавливаем флаг обработки
        self.is_processing_turn = True
        self.update_battle_display()
        
        # Используем способность через сервис
        success, logs = self.service.use_ability()
        if success:
            for log in logs:
                self.add_log(f"✨ {log}")
            self.add_log("")
            self.update_battle_display()
        else:
            self.add_log("❌ " + logs[0])
            self.is_processing_turn = False
            self.update_battle_display()
            return
        
        if self.battlefield.is_over():
            self.is_processing_turn = False
            self.end_battle()
        else:
            Clock.schedule_once(lambda dt: self.enemy_turn(), 1.0)
    
    def enemy_turn(self):
        """Ход врагов."""
        if not self.battlefield or not self.service or self.battlefield.is_over():
            self.is_processing_turn = False
            self.update_battle_display()
            return

        for log in self.service.run_enemy_phase():
            self.add_log(f"→ {log}")

        self.update_battle_display()
        
        if not self.battlefield.player.is_alive:
            self.add_log("\n💀 Вы были повержены!")
            self.is_processing_turn = False
            Clock.schedule_once(lambda dt: self.return_to_game(False), 2.0)
        elif self.battlefield.is_over():
            self.is_processing_turn = False
            self.end_battle()
        else:
            # Сбрасываем флаг после завершения хода врагов, чтобы игрок мог действовать
            self.is_processing_turn = False
            self.update_battle_display()
    
    def end_battle(self):
        """Завершение боя."""
        # Сбрасываем флаг обработки
        self.is_processing_turn = False
        self.update_battle_display()
        
        app = App.get_running_app()
        if self.battlefield.player.is_alive:
            self.add_log("\n🎉 Вы победили!")
            
            # Восстанавливаем здоровье компаньонов (только павших)
            for companion in self.battlefield.player.companions:
                if not companion.is_alive:
                    companion.health = 1  # Восстанавливаем до 1 HP
                    self.add_log(
                        f"💚 {companion.name} "
                        f"восстановлен после боя (1 HP)!"
                    )
            
            # Генерируем результат боя с добычей
            from systems.battle import BattleResult, LootDrop
            
            # Подсчитываем добычу
            total_gold = 0
            total_xp = 0
            loot_drops = []
            
            for enemy in self.battlefield.enemies:
                if not enemy.is_alive:
                    total_gold += enemy.base_coins
                    total_xp += enemy.base_xp
                    
                    loot = enemy.generate_loot()
                    if loot:
                        for item_id, quantity in loot:
                            loot_drops.append(LootDrop(item_id, quantity))

                    if getattr(enemy, "weapon", None):
                        weapon_id = getattr(enemy.weapon, "id", None)
                        if weapon_id:
                            loot_drops.append(LootDrop(weapon_id, 1))

                    if getattr(enemy, "armor", None):
                        armor_id = getattr(enemy.armor, "id", None)
                        if armor_id:
                            loot_drops.append(LootDrop(armor_id, 1))
                    # Если убит босс — отмечаем его как побежденного
                    try:
                        if hasattr(enemy, '_template') and enemy._template:
                            tpl = enemy._template
                            if getattr(tpl, 'is_boss', False):
                                boss_enemy_id = getattr(tpl, 'id', '')
                                boss_id = None
                                if 'berserker' in boss_enemy_id or 'mad_raider' in boss_enemy_id or 'boss_1' in boss_enemy_id:
                                    boss_id = 1
                                elif 'bog_master' in boss_enemy_id or 'boss_2' in boss_enemy_id:
                                    boss_id = 2
                                elif 'mine_king' in boss_enemy_id or 'boss_3' in boss_enemy_id:
                                    boss_id = 3
                                elif 'dragon_lord' in boss_enemy_id or 'boss_4' in boss_enemy_id:
                                    boss_id = 4

                                if boss_id and app and getattr(app, 'game', None):
                                    lm = app.game.location_manager
                                    if lm:
                                        lm.mark_boss_defeated(boss_id)
                    except Exception:
                        pass

            # After marking bosses defeated, immediately check for location unlocks
            try:
                app2 = App.get_running_app()
                if app2 and getattr(app2, 'game', None):
                    lm2 = app2.game.location_manager
                    if lm2:
                        unlocked = lm2.check_and_unlock_locations()
                        if unlocked:
                            names = [lm2.get_location(l).name for l in unlocked]
                            popup = Popup(
                                title='🔓 Новые локации!',
                                content=Label(text='\n'.join(names)),
                                size_hint=(0.6, 0.3)
                            )
                            popup.open()
                        # Refresh shop and UI screens so changes appear immediately
                        try:
                            app2.game.refresh_shop()
                        except Exception:
                            pass
                        if getattr(app2, 'shop_screen', None):
                            try:
                                app2.shop_screen.update_shop()
                            except Exception:
                                pass
                        if getattr(app2, 'location_select_screen', None):
                            try:
                                app2.location_select_screen.update_locations()
                            except Exception:
                                pass
            except Exception:
                pass
            
            battle_result = BattleResult(
                victory=True,
                loot=loot_drops,
                gold_earned=total_gold,
                xp_earned=total_xp
            )
            # Обновляем ассортимент магазина согласно разблокированным локациям
            app = App.get_running_app()
            if app and getattr(app, 'game', None):
                try:
                    app.game.refresh_shop()
                except Exception:
                    # на случай ошибок оставим поведение без падений
                    pass

            # Показываем окно добычи
            Clock.schedule_once(
                lambda dt: self._show_loot_window(
                    battle_result
                ),
                2.0
            )
        else:
            self.add_log("\n💀 Вы были повержены...")
            if app.game:
                Clock.schedule_once(
                    lambda dt: self.show_death_screen(),
                    2.0
                )
    
    def _show_loot_window(self, battle_result):
        """Показать окно добычи."""
        app = App.get_running_app()
        if app.loot_window_screen:
            app.loot_window_screen.show_loot(
                battle_result
            )
            self.manager.current = 'loot_window'
    
    def show_death_screen(self):
        """Обработка поражения в бою."""
        app = App.get_running_app()
        if not app.game:
            return
        result = app.game.apply_death_penalty()

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(
            text=result.message,
            text_size=(dp(300), None),
            halign='center',
            valign='middle',
        ))

        def return_to_main_menu(instance):
            popup.dismiss()
            if getattr(app, '_battle_from_local_location', False):
                try:
                    if getattr(app, 'local_location_screen', None):
                        app.local_location_screen.resume_game()
                except Exception:
                    pass
                self.manager.current = 'local_location'
                app._battle_from_local_location = False
            else:
                self.manager.current = 'location_select'

        btn_continue = Button(text='Продолжить', size_hint_y=None, height=dp(50))
        btn_continue.bind(on_press=return_to_main_menu)
        content.add_widget(btn_continue)

        popup = Popup(
            title='🤕 Вы были оглушены',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False,
        )
        popup.open()

    def return_to_game(self, victory=True):
        """Возврат на главный экран после боя."""
        app = App.get_running_app()
        if app.game and not victory:
            result = app.game.apply_death_penalty()

            content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
            content.add_widget(Label(
                text=result.message,
                text_size=(dp(300), None),
                halign='center',
                valign='middle',
                font_size=dp(18),
            ))

            def close_and_return(instance):
                popup.dismiss()
                if getattr(app, '_battle_from_local_location', False):
                    try:
                        if getattr(app, 'local_location_screen', None):
                            app.local_location_screen.resume_game()
                    except Exception:
                        pass
                    self.manager.current = 'local_location'
                    app._battle_from_local_location = False
                else:
                    self.manager.current = 'location_select'

            btn_continue = Button(
                text='Продолжить',
                size_hint_y=None,
                height=dp(50),
            )
            btn_continue.bind(on_press=close_and_return)
            content.add_widget(btn_continue)

            popup = Popup(
                title='🤕 Вы были оглушены',
                content=content,
                size_hint=(0.8, 0.6),
                auto_dismiss=False,
            )
            popup.open()
            return

        if getattr(app, '_battle_from_local_location', False):
            try:
                if getattr(app, 'local_location_screen', None):
                    app.local_location_screen.on_return_from_battle()
            except Exception as e:
                print(f"[DEBUG] Failed to call on_return_from_battle: {e}")
            self.manager.current = 'local_location'
            app._battle_from_local_location = False
        else:
            self.manager.current = 'location_select'
