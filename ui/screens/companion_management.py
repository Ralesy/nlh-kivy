#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран управления спутниками."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import add_back_to_map_button
from data.items import Potion, Weapon, Armor

class CompanionManagementScreen(Screen, KeyboardHandler):
    """Экран управления спутниками."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))

        # Фон
        with layout.canvas.before:
            Color(0.15, 0.2, 0.25, 1)
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )

        title = Label(
            text='🤝 УПРАВЛЕНИЕ СПУТНИКАМИ',
            font_size=dp(32),
            size_hint_y=None,
            height=dp(60),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)

        # Информация о спутнике
        self.companion_info = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(100),
            text_size=(None, None),
            halign='center',
            valign='top',
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(self.companion_info)

        # Кнопки действий
        actions_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        actions_layout.height = dp(200)

        self.btn_heal = Button(
            text='💚 Лечить зельем',
            font_size=dp(18),
            background_color=COLORS['hp_green']
        )
        self.btn_heal.bind(on_press=self.on_heal)
        actions_layout.add_widget(self.btn_heal)

        self.btn_equip_weapon = Button(
            text='⚔️ Экипировать оружие',
            font_size=dp(18),
            background_color=COLORS['stone_light']
        )
        self.btn_equip_weapon.bind(on_press=self.on_equip_weapon)
        actions_layout.add_widget(self.btn_equip_weapon)

        self.btn_equip_armor = Button(
            text='🛡️ Экипировать броню',
            font_size=dp(18),
            background_color=COLORS['stone_light']
        )
        self.btn_equip_armor.bind(on_press=self.on_equip_armor)
        actions_layout.add_widget(self.btn_equip_armor)

        self.btn_unequip_weapon = Button(
            text='⚔️ Снять оружие',
            font_size=dp(18),
            background_color=COLORS['stone_light']
        )
        self.btn_unequip_weapon.bind(on_press=self.on_unequip_weapon)
        actions_layout.add_widget(self.btn_unequip_weapon)

        self.btn_unequip_armor = Button(
            text='🛡️ Снять броню',
            font_size=dp(18),
            background_color=COLORS['stone_light']
        )
        self.btn_unequip_armor.bind(on_press=self.on_unequip_armor)
        actions_layout.add_widget(self.btn_unequip_armor)

        self.btn_dismiss = Button(
            text='❌ Отпустить',
            font_size=dp(18),
            background_color=COLORS['hp_red']
        )
        self.btn_dismiss.bind(on_press=self.on_dismiss)
        actions_layout.add_widget(self.btn_dismiss)

        layout.add_widget(actions_layout)

        self.add_widget(layout)
        # remove old back button; add edge 'Back to Map' button
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

    def update_companion(self):
        """Обновить информацию о спутнике."""
        app = App.get_running_app()
        if not app.game or not app.game.player:
            self.companion_info.text = 'Нет спутника'
            self._disable_buttons()
            return

        player = app.game.player
        if not player.companions:
            self.companion_info.text = 'У вас нет спутника.\nНанмите кого-нибудь в таверне!'
            self._disable_buttons()
            return

        companion = player.companions[0]  # Только один спутник

        weapon_name = companion.weapon.name if companion.weapon else 'Нет'
        armor_name = companion.armor.name if companion.armor else 'Нет'

        self.companion_info.text = (
            f"🤝 {companion.name} ({companion.role})\n"
            f"💚 HP: {companion.health}/{companion.max_health}\n"
            f"⚔️ Урон: {companion.damage}\n"
            f"🛡️ Защита: {companion.defense}\n"
            f"⚔️ Оружие: {weapon_name}\n"
            f"🛡️ Броня: {armor_name}"
        )

        # Включить кнопки
        self.btn_heal.disabled = companion.health >= companion.max_health
        self.btn_equip_weapon.disabled = False
        self.btn_equip_armor.disabled = False
        self.btn_unequip_weapon.disabled = companion.weapon is None
        self.btn_unequip_armor.disabled = companion.armor is None
        self.btn_dismiss.disabled = False

    def _disable_buttons(self):
        """Отключить все кнопки."""
        self.btn_heal.disabled = True
        self.btn_equip_weapon.disabled = True
        self.btn_equip_armor.disabled = True
        self.btn_unequip_weapon.disabled = True
        self.btn_unequip_armor.disabled = True
        self.btn_dismiss.disabled = True

    def on_heal(self, instance):
        """Лечить спутника зельем."""
        app = App.get_running_app()
        if not app.game or not app.game.player or not app.game.player.companions:
            return

        player = app.game.player
        companion = player.companions[0]

        # Найти зелья в инвентаре
        potions = []
        for item, qty in player.inventory.list_items():
            if isinstance(item, Potion) and qty > 0:
                potions.append((item, qty))

        if not potions:
            popup = Popup(
                title='Ошибка',
                content=Label(text='У вас нет зелий!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        # Показать выбор зелья
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))

        content.add_widget(Label(text=f"Выберите зелье для {companion.name}:"))

        for potion, qty in potions:
            btn = Button(
                text=f"{potion.display_name()} x{qty} (+{potion.heal_amount} HP)",
                size_hint_y=None,
                height=dp(50)
            )
            btn.bind(on_press=lambda x, p=potion: self._heal_with_potion(p))
            content.add_widget(btn)

        btn_cancel = Button(text='Отмена', size_hint_y=None, height=dp(50))
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(btn_cancel)

        popup = Popup(
            title='🎁 Выбор зелья',
            content=content,
            size_hint=(0.7, 0.6),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

    def _heal_with_potion(self, potion):
        """Лечить выбранным зельем."""
        app = App.get_running_app()
        if not app.game or not app.game.player or not app.game.player.companions:
            return

        player = app.game.player
        companion = player.companions[0]

        # Использовать зелье
        healed = companion.heal(potion.heal_amount)
        player.inventory.remove(potion.id, 1)

        # Закрыть popup
        for widget in App.get_running_app()._app_window.children:
            if hasattr(widget, 'dismiss'):
                widget.dismiss()
                break

        # Показать результат
        popup = Popup(
            title='✅ Лечение',
            content=Label(
                text=f"{companion.name} восстановил {healed} HP!\n"
                     f"({companion.health}/{companion.max_health} HP)"
            ),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        self.update_companion()

    def on_equip_weapon(self, instance):
        """Экипировать оружие."""
        self._show_equip_dialog('weapon')

    def on_equip_armor(self, instance):
        """Экипировать броню."""
        self._show_equip_dialog('armor')

    def _show_equip_dialog(self, item_type):
        """Показать диалог выбора предмета для экипировки."""
        app = App.get_running_app()
        if not app.game or not app.game.player or not app.game.player.companions:
            return

        player = app.game.player
        companion = player.companions[0]

        # Найти подходящие предметы
        items = []
        for item, qty in player.inventory.list_items():
            if qty > 0:
                if item_type == 'weapon' and isinstance(item, Weapon):
                    items.append((item, qty))
                elif item_type == 'armor' and isinstance(item, Armor):
                    items.append((item, qty))

        item_type_names = {
            'weapon': 'оружия',
            'armor': 'брони'
        }
        item_type_name = item_type_names.get(item_type, item_type)

        if not items:
            popup = Popup(
                title='Ошибка',
                content=Label(text=f'У вас нет {item_type_name}!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        # Показать выбор предмета
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))

        content.add_widget(Label(text=f"Выберите {item_type} для {companion.name}:"))

        for item, qty in items:
            btn = Button(
                text=f"{item.display_name()} x{qty}",
                size_hint_y=None,
                height=dp(50)
            )
            btn.bind(on_press=lambda x, i=item: self._equip_item(i, item_type))
            content.add_widget(btn)

        btn_cancel = Button(text='Отмена', size_hint_y=None, height=dp(50))
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(btn_cancel)

        popup = Popup(
            title=f'⚔️ Выбор {item_type}',
            content=content,
            size_hint=(0.7, 0.6),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

    def _equip_item(self, item, item_type):
        """Экипировать выбранный предмет."""
        app = App.get_running_app()
        if not app.game or not app.game.player or not app.game.player.companions:
            return

        player = app.game.player
        companion = player.companions[0]

        # Снять старый предмет, если есть
        old_item = None
        if item_type == 'weapon':
            old_item = companion.weapon
            # Удалить из инвентаря игрока перед экипировкой
            player.inventory.remove(item.id, 1)
            # Использовать метод equip_weapon для корректного обновления урона
            companion.equip_weapon(item)
        elif item_type == 'armor':
            old_item = companion.armor
            # Удалить из инвентаря игрока перед экипировкой
            player.inventory.remove(item.id, 1)
            # Использовать метод equip_armor для корректного обновления защиты
            companion.equip_armor(item)

        # Вернуть старый предмет в инвентарь, если был
        if old_item:
            player.inventory.add(old_item, 1)

        # Закрыть popup
        for widget in App.get_running_app()._app_window.children:
            if hasattr(widget, 'dismiss'):
                widget.dismiss()
                break

        # Показать результат
        popup = Popup(
            title='✅ Экипировка',
            content=Label(text=f"{companion.name} экипирован {item.display_name()}!"),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        self.update_companion()

    def on_unequip_weapon(self, instance):
        """Снять оружие."""
        self._unequip_item('weapon')

    def on_unequip_armor(self, instance):
        """Снять броню."""
        self._unequip_item('armor')

    def _unequip_item(self, item_type):
        """Снять предмет."""
        app = App.get_running_app()
        if not app.game or not app.game.player:
            return
        if not app.game.player.companions:
            return

        player = app.game.player
        companion = player.companions[0]

        item = None
        if item_type == 'weapon':
            item = companion.weapon
            # Использовать метод unequip_weapon для корректного обновления урона
            if item:
                companion.unequip_weapon()
        elif item_type == 'armor':
            item = companion.armor
            # Использовать метод unequip_armor для корректного обновления защиты
            if item:
                companion.unequip_armor()

        if item:
            # Вернуть в инвентарь игрока
            player.inventory.add(item, 1)

            popup = Popup(
                title='✅ Снято',
                content=Label(text=f"{item.display_name()} возвращено в инвентарь!"),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()

        self.update_companion()

    def on_dismiss(self, instance):
        """Отпустить спутника."""
        app = App.get_running_app()
        if not app.game or not app.game.player or not app.game.player.companions:
            return

        player = app.game.player
        companion = player.companions[0]

        # Вернуть экипировку в инвентарь
        if companion.weapon:
            player.inventory.add(companion.weapon, 1)
        if companion.armor:
            player.inventory.add(companion.armor, 1)

        # Удалить спутника
        player.companions.remove(companion)

        popup = Popup(
            title='👋 Спутник отпущен',
            content=Label(text=f"{companion.name} покинул вашу партию.\nЭкипировка возвращена в инвентарь."),
            size_hint=(0.7, 0.4),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        self.update_companion()
