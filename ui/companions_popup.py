#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CompanionsPopup — всплывающее окно управления спутниками слева экрана.

Показывает информацию о спутнике и кнопки действий.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle

from ui.ui_styles import COLORS
from data.items import Potion, Weapon, Armor


class _SectionRow(Label):
    """Строка информации о спутнике."""

    def __init__(self, text="", color=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = dp(12)
        self.size_hint_y = None
        self.height = dp(20)
        self.halign = 'left'
        self.valign = 'middle'
        self.color = color or COLORS['text_light']
        self.bold = False


class CompanionsPopup(BoxLayout):
    """Полупрозрачное окно управления спутниками (левая сторона экрана)."""

    def __init__(self, player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
        self.padding = dp(8)
        self.player = player
        self.on_done = on_done

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

        # ── Заголовок ──
        title = Label(
            text='СПУТНИКИ',
            font_size=dp(20),
            size_hint_y=None,
            height=dp(34),
            color=COLORS['gold_light'],
            bold=True,
        )
        self.add_widget(title)

        # ── Информация о спутнике ──
        self._info_labels = []
        info_box = BoxLayout(
            orientation='vertical', size_hint_y=None,
            padding=(dp(4), dp(2)), spacing=dp(1),
        )
        info_box.bind(minimum_height=info_box.setter('height'))
        # Заголовок секции
        section_title = Label(
            text='ИНФОРМАЦИЯ',
            font_size=dp(13),
            size_hint_y=None,
            height=dp(20),
            halign='left',
            valign='middle',
            color=COLORS['gold'],
            bold=True,
        )
        info_box.add_widget(section_title)
        for _ in range(6):
            lbl = _SectionRow()
            self._info_labels.append(lbl)
            info_box.add_widget(lbl)
        self.add_widget(info_box)

        # ── Кнопки действий ──
        actions_box = BoxLayout(
            orientation='vertical', size_hint_y=None,
            padding=(dp(4), dp(2)), spacing=dp(3),
        )
        actions_box.bind(minimum_height=actions_box.setter('height'))

        action_title = Label(
            text='[Действие] ДЕЙСТВИЯ',
            font_size=dp(13),
            size_hint_y=None,
            height=dp(20),
            halign='left',
            valign='middle',
            color=COLORS['gold'],
            bold=True,
        )
        actions_box.add_widget(action_title)

        btn_style = {
            'size_hint_y': None,
            'height': dp(34),
            'font_size': dp(13),
            'background_normal': '',
            'bold': True,
        }

        self.btn_heal = Button(
            text='Лечить зельем',
            background_color=(0.35, 0.55, 0.30, 0.9),
            color=(1, 1, 1, 1),
            **btn_style,
        )
        self.btn_heal.bind(on_press=self.on_heal)
        actions_box.add_widget(self.btn_heal)

        self.btn_equip_weapon = Button(
            text='Экипировать оружие',
            background_color=(0.25, 0.30, 0.40, 0.9),
            color=(1, 1, 1, 1),
            **btn_style,
        )
        self.btn_equip_weapon.bind(on_press=self.on_equip_weapon)
        actions_box.add_widget(self.btn_equip_weapon)

        self.btn_equip_armor = Button(
            text='Экипировать броню',
            background_color=(0.25, 0.30, 0.40, 0.9),
            color=(1, 1, 1, 1),
            **btn_style,
        )
        self.btn_equip_armor.bind(on_press=self.on_equip_armor)
        actions_box.add_widget(self.btn_equip_armor)

        self.btn_unequip_weapon = Button(
            text='Снять оружие',
            background_color=(0.30, 0.25, 0.25, 0.9),
            color=(1, 1, 1, 1),
            **btn_style,
        )
        self.btn_unequip_weapon.bind(on_press=self.on_unequip_weapon)
        actions_box.add_widget(self.btn_unequip_weapon)

        self.btn_unequip_armor = Button(
            text='Снять броню',
            background_color=(0.30, 0.25, 0.25, 0.9),
            color=(1, 1, 1, 1),
            **btn_style,
        )
        self.btn_unequip_armor.bind(on_press=self.on_unequip_armor)
        actions_box.add_widget(self.btn_unequip_armor)

        self.btn_dismiss = Button(
            text='Отпустить',
            background_color=(0.55, 0.25, 0.20, 0.9),
            color=(1, 1, 1, 1),
            **btn_style,
        )
        self.btn_dismiss.bind(on_press=self.on_dismiss)
        actions_box.add_widget(self.btn_dismiss)

        self.add_widget(actions_box)

        # ── Растягивающийся spacer ──
        spacer = BoxLayout(size_hint_y=1)
        self.add_widget(spacer)

        # ── Кнопка закрытия ──
        btn_close = Button(
            text='✕ Закрыть',
            size_hint_y=None,
            height=dp(42),
            font_size=dp(15),
            background_color=(0.2, 0.22, 0.28, 0.95),
            color=(0.9, 0.9, 0.9, 1),
        )
        btn_close.bind(on_press=lambda _: self._close())
        self.add_widget(btn_close)

        self._refresh()

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _refresh(self):
        """Обновить информацию о спутнике."""
        if not self.player or not self.player.companions:
            texts = [
                "Нет спутника",
                "Нанмите кого-нибудь",
                "в таверне города!",
                "", "", "",
            ]
            for lbl, text in zip(self._info_labels, texts):
                lbl.text = text
            for btn in (self.btn_heal, self.btn_equip_weapon, self.btn_equip_armor,
                        self.btn_unequip_weapon, self.btn_unequip_armor, self.btn_dismiss):
                btn.disabled = True
            return

        companion = self.player.companions[0]
        weapon_name = companion.weapon.name if companion.weapon else 'Нет'
        armor_name = companion.armor.name if companion.armor else 'Нет'

        texts = [
            f"{companion.name} ({companion.role})",
            f"HP: {companion.health}/{companion.max_health}",
            f"Урон: {companion.damage}",
            f"Защита: {companion.defense}",
            f"Оружие: {weapon_name}",
            f"Броня: {armor_name}",
        ]
        for lbl, text in zip(self._info_labels, texts):
            lbl.text = text

        self.btn_heal.disabled = companion.health >= companion.max_health
        self.btn_equip_weapon.disabled = False
        self.btn_equip_armor.disabled = False
        self.btn_unequip_weapon.disabled = companion.weapon is None
        self.btn_unequip_armor.disabled = companion.armor is None
        self.btn_dismiss.disabled = False

    # ─── Обработчики действий (адаптированы из companion_management.py) ───

    def on_heal(self, instance):
        app = App.get_running_app()
        if not app.game or not self.player or not self.player.companions:
            return
        companion = self.player.companions[0]

        potions = []
        for item, qty in self.player.inventory.list_items():
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

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(15))
        content.add_widget(Label(text=f"Выберите зелье для {companion.name}:", font_size=dp(16)))

        for potion, qty in potions:
            btn = Button(
                text=f"{potion.display_name()} x{qty} (+{potion.heal_amount} HP)",
                size_hint_y=None, height=dp(44),
            )
            btn.bind(on_press=lambda x, p=potion: self._heal_with_potion(p))
            content.add_widget(btn)

        btn_cancel = Button(text='Отмена', size_hint_y=None, height=dp(44))
        btn_cancel.bind(on_press=lambda x: heal_popup.dismiss())
        content.add_widget(btn_cancel)

        heal_popup = Popup(
            title='🎁 Выбор зелья',
            content=content,
            size_hint=(0.7, 0.5),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        heal_popup.open()

    def _heal_with_potion(self, potion):
        app = App.get_running_app()
        if not app.game or not self.player or not self.player.companions:
            return
        companion = self.player.companions[0]
        healed = companion.heal(potion.heal_amount)
        self.player.inventory.remove(potion.id, 1)

        for widget in list(App.get_running_app()._app_window.children):
            if hasattr(widget, 'dismiss'):
                widget.dismiss()
                break

        result = Popup(
            title='Лечение',
            content=Label(
                text=f"{companion.name} восстановил {healed} HP!\n({companion.health}/{companion.max_health} HP)",
            ),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        result.open()
        self._refresh()

    def on_equip_weapon(self, instance):
        self._show_equip_dialog('weapon')

    def on_equip_armor(self, instance):
        self._show_equip_dialog('armor')

    def _show_equip_dialog(self, item_type):
        app = App.get_running_app()
        if not app.game or not self.player or not self.player.companions:
            return
        companion = self.player.companions[0]

        items = []
        for item, qty in self.player.inventory.list_items():
            if qty > 0:
                if item_type == 'weapon' and isinstance(item, Weapon):
                    items.append((item, qty))
                elif item_type == 'armor' and isinstance(item, Armor):
                    items.append((item, qty))

        type_names = {'weapon': 'оружия', 'armor': 'брони'}
        type_name = type_names.get(item_type, item_type)

        if not items:
            popup = Popup(
                title='Ошибка',
                content=Label(text=f'У вас нет {type_name}!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(15))
        content.add_widget(Label(text=f"Выберите {type_name} для {companion.name}:", font_size=dp(16)))

        for item, qty in items:
            btn = Button(
                text=f"{item.display_name()} x{qty}",
                size_hint_y=None, height=dp(44),
            )
            btn.bind(on_press=lambda x, i=item: self._equip_item(i, item_type))
            content.add_widget(btn)

        btn_cancel = Button(text='Отмена', size_hint_y=None, height=dp(44))
        btn_cancel.bind(on_press=lambda x: equip_popup.dismiss())
        content.add_widget(btn_cancel)

        equip_popup = Popup(
            title=f'Выбор {type_name}',
            content=content,
            size_hint=(0.7, 0.5),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        equip_popup.open()

    def _equip_item(self, item, item_type):
        if not self.player or not self.player.companions:
            return
        companion = self.player.companions[0]

        old_item = None
        if item_type == 'weapon':
            old_item = companion.weapon
            self.player.inventory.remove(item.id, 1)
            companion.equip_weapon(item)
        elif item_type == 'armor':
            old_item = companion.armor
            self.player.inventory.remove(item.id, 1)
            companion.equip_armor(item)

        if old_item:
            self.player.inventory.add(old_item, 1)

        for widget in list(App.get_running_app()._app_window.children):
            if hasattr(widget, 'dismiss'):
                widget.dismiss()
                break

        result = Popup(
            title='Экипировка',
            content=Label(text=f"{companion.name} экипирован {item.display_name()}!"),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        result.open()
        self._refresh()

    def on_unequip_weapon(self, instance):
        self._unequip_item('weapon')

    def on_unequip_armor(self, instance):
        self._unequip_item('armor')

    def _unequip_item(self, item_type):
        if not self.player or not self.player.companions:
            return
        companion = self.player.companions[0]

        item = None
        if item_type == 'weapon':
            item = companion.weapon
            if item:
                companion.unequip_weapon()
        elif item_type == 'armor':
            item = companion.armor
            if item:
                companion.unequip_armor()

        if item:
            self.player.inventory.add(item, 1)
            result = Popup(
                title='Снято',
                content=Label(text=f"{item.display_name()} возвращено в инвентарь!"),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            result.open()

        self._refresh()

    def on_dismiss(self, instance):
        if not self.player or not self.player.companions:
            return
        companion = self.player.companions[0]

        if companion.weapon:
            self.player.inventory.add(companion.weapon, 1)
        if companion.armor:
            self.player.inventory.add(companion.armor, 1)

        self.player.companions.remove(companion)

        result = Popup(
            title='👋 Спутник отпущен',
            content=Label(text=f"{companion.name} покинул вашу партию.\nЭкипировка возвращена в инвентарь."),
            size_hint=(0.7, 0.4),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        result.open()
        self._refresh()

    def _close(self):
        if self.on_done:
            self.on_done()