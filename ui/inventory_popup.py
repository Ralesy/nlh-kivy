#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InventoryPopup — всплывающее окно инвентаря слева экрана.

Стилизовано аналогично LootWindow: полупрозрачный фон, две колонки
(экипировка + список предметов), кнопки действий.
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

from data.items import Weapon, Armor, Potion, WEAPON_MATERIALS, ARMOR_MATERIALS


class InventoryPopup(BoxLayout):
    """Полупрозрачное окно инвентаря (левая сторона экрана)."""

    def __init__(self, player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(6)
        self.padding = dp(8)
        self.player = player
        self.on_done = on_done

        # Фон — тёмный полупрозрачный со скруглёнными углами
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
            text='ИНВЕНТАРЬ',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(38),
            color=(0.9, 0.8, 0.3, 1),
        )
        self.add_widget(title)

        # ── Экипировка ──
        self.equipment_label = Label(
            text='',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(50),
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.85, 0.85, 0.85, 1),
        )
        self.add_widget(self.equipment_label)

        # ── Скролл со списком предметов ──
        scroll = ScrollView(size_hint_y=1)
        self.items_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
        )
        self.items_layout.bind(minimum_height=self.items_layout.setter('height'))
        scroll.add_widget(self.items_layout)
        self.add_widget(scroll)

        # ── Кнопка закрытия ──
        btn_close = Button(
            text='✕ Закрыть',
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=(0.2, 0.22, 0.28, 0.95),
            color=(0.9, 0.9, 0.9, 1),
        )
        btn_close.bind(on_press=self._close)
        self.add_widget(btn_close)

        self._refresh()

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _refresh(self):
        """Обновить содержимое инвентаря."""
        p = self.player
        if not p:
            return

        weapon_name = p.weapon.display_name() if p.weapon else 'Нет'
        armor_name = p.armor.display_name() if p.armor else 'Нет'
        hp_str = f'{p.health}/{p.max_health}'
        self.equipment_label.text = (
            f'[Сердце] {hp_str} {weapon_name} {armor_name}'
        )

        self.items_layout.clear_widgets()
        items = p.inventory.list_items()
        if not items:
            empty = Label(
                text='(инвентарь пуст)',
                font_size=dp(14),
                size_hint_y=None,
                height=dp(30),
                color=(0.6, 0.6, 0.6, 1),
            )
            self.items_layout.add_widget(empty)
            return

        for item, qty in items:
            # Контейнер предмета
            card = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(72),
                spacing=dp(2),
            )
            with card.canvas.before:
                Color(0.12, 0.15, 0.2, 0.7)
                card_bg = Rectangle(pos=card.pos, size=card.size)
            card.bind(pos=lambda i, v: setattr(card_bg, 'pos', i.pos),
                      size=lambda i, v: setattr(card_bg, 'size', i.size))

            # Верхняя строка: название + кнопка инфо
            top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
            label = Label(
                text=f'{item.display_name()} x{qty}',
                font_size=dp(13),
                size_hint_x=0.8,
                halign='left',
                valign='middle',
                color=(0.9, 0.9, 0.9, 1),
            )
            label.bind(size=lambda lb, s: setattr(lb, 'text_size', s))
            top.add_widget(label)

            btn_info = Button(
                text='',
                size_hint_x=0.2,
                size_hint_y=None,
                height=dp(26),
                background_color=(0.2, 0.25, 0.35, 0.8),
            )
            btn_info.bind(on_press=lambda x, it=item: self._show_info(it))
            top.add_widget(btn_info)
            card.add_widget(top)

            # Нижняя строка: кнопки действий
            bottom = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(34), spacing=dp(4))

            is_equipped = (p.weapon and p.weapon.id == item.id) or (p.armor and p.armor.id == item.id)

            if isinstance(item, Weapon) or isinstance(item, Armor):
                if is_equipped:
                    btn = Button(
                        text='Снять',
                        size_hint_x=1.0,
                        font_size=dp(12),
                        background_color=(0.35, 0.2, 0.2, 0.8),
                    )
                    btn.bind(on_press=lambda x, it=item: self._unequip(it))
                    bottom.add_widget(btn)
                else:
                    btn = Button(
                        text='Экипировать',
                        size_hint_x=1.0,
                        font_size=dp(12),
                        background_color=(0.2, 0.35, 0.2, 0.8),
                    )
                    btn.bind(on_press=lambda x, it=item: self._equip(it))
                    bottom.add_widget(btn)

            if isinstance(item, Potion):
                btn = Button(
                    text='Использовать',
                    size_hint_x=1.0,
                    font_size=dp(12),
                    background_color=(0.25, 0.3, 0.4, 0.8),
                )
                btn.bind(on_press=lambda x, it=item: self._use_potion(it))
                bottom.add_widget(btn)

            card.add_widget(bottom)
            self.items_layout.add_widget(card)

    # ──────────────────────────────────────────────
    # Действия с предметами
    # ──────────────────────────────────────────────

    def _equip(self, item):
        p = self.player
        if not p:
            return
        if isinstance(item, Weapon):
            p.equip_weapon(item)
        elif isinstance(item, Armor):
            p.equip_armor(item)
        self._refresh()

    def _unequip(self, item):
        p = self.player
        if not p:
            return
        if isinstance(item, Weapon):
            p.unequip_weapon()
        elif isinstance(item, Armor):
            p.unequip_armor()
        self._refresh()

    def _use_potion(self, potion):
        """Использовать зелье: показать диалог выбора цели."""
        p = self.player
        if not p:
            return

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(15))
        content.add_widget(Label(
            text=f'Кому дать {potion.display_name()}?',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(35),
        ))

        targets = BoxLayout(orientation='vertical', spacing=dp(6))

        if p.is_alive and p.health < p.max_health:
            btn = Button(
                text=f'Игрок ({p.health}/{p.max_health} HP)',
                size_hint_y=None,
                height=dp(44),
            )
            btn.bind(on_press=lambda x: self._apply_potion(potion, p, target_popup))
            targets.add_widget(btn)

        for companion in p.companions:
            if companion.is_alive and companion.health < companion.max_health:
                btn = Button(
                    text=f'{companion.name} ({companion.health}/{companion.max_health} HP)',
                    size_hint_y=None,
                    height=dp(44),
                )
                btn.bind(on_press=lambda x, c=companion: self._apply_potion(potion, c, target_popup))
                targets.add_widget(btn)

        content.add_widget(targets)

        btn_cancel = Button(text='Отмена', size_hint_y=None, height=dp(44))
        content.add_widget(btn_cancel)

        target_popup = Popup(
            title='🎁 Использование зелья',
            content=content,
            size_hint=(0.6, 0.5),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        btn_cancel.bind(on_press=target_popup.dismiss)
        target_popup.open()

    def _apply_potion(self, potion, target, target_popup):
        healed = target.heal(potion.heal_amount)
        self.player.inventory.remove(potion.id, 1)
        target_popup.dismiss()

        result_popup = Popup(
            title='Зелье использовано',
            content=Label(
                text=f'{target.name} восстановил {healed} HP!\n'
                     f'({target.health}/{target.max_health} HP)',
                font_size=dp(16),
            ),
            size_hint=(0.5, 0.25),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        result_popup.open()
        self._refresh()

    # ──────────────────────────────────────────────
    # Информация о предмете
    # ──────────────────────────────────────────────

    def _show_info(self, item):
        lines = []
        lines.append(item.display_name())

        if isinstance(item, Weapon):
            lines.append(f'Урон: {item.damage_bonus}')
            mat = WEAPON_MATERIALS.get(item.material, 'неизвестный')
            lines.append(f'Материал: {mat}')
            lines.append(f'Состояние: {item.condition_display}')
        elif isinstance(item, Armor):
            lines.append(f'Защита: {item.defense}')
            mat = ARMOR_MATERIALS.get(item.material, 'неизвестная')
            lines.append(f'Материал: {mat}')
            lines.append(f'Состояние: {item.condition_display}')
        elif isinstance(item, Potion):
            lines.append(f'Восстанавливает: {item.heal_amount} HP')

        lines.append(f'Цена: {item.price} монет')
        if item.description:
            lines.append('')
            lines.append(f'📝 {item.description}')

        if hasattr(item, 'ability') and item.ability:
            ab = item.ability
            lines.append('')
            lines.append(f'Способность: {ab.name} ({ab.ability_type})')
            if hasattr(ab, 'damage_per_hit'):
                lines.append(f'+{ab.damage_per_hit} урона за удар')
            if hasattr(ab, 'armor_ignore'):
                pct = int(ab.armor_ignore * 100)
                lines.append(f'Игнорирует {pct}% брони')
            if hasattr(ab, 'crit_multiplier'):
                lines.append(f'Крит. множитель: x{ab.crit_multiplier}')

        popup_text = '\n'.join(lines)

        from kivy.uix.popup import Popup as InfoPopup
        from kivy.uix.scrollview import ScrollView as InfoScroll

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        scroll = InfoScroll()
        info_label = Label(
            text=popup_text,
            font_size=dp(15),
            size_hint_y=None,
            text_size=(dp(280), None),
            halign='left',
            valign='top',
        )
        info_label.bind(texture_size=info_label.setter('size'))
        scroll.add_widget(info_label)
        content.add_widget(scroll)

        btn_close = Button(
            text='Закрыть',
            size_hint_y=None,
            height=dp(44),
            background_color=(0.3, 0.3, 0.3, 1),
        )
        content.add_widget(btn_close)

        info_popup = InfoPopup(
            title='📖 Информация о предмете',
            content=content,
            size_hint=(0.7, 0.6),
        )
        btn_close.bind(on_press=info_popup.dismiss)
        info_popup.open()

    # ──────────────────────────────────────────────
    # Закрытие
    # ──────────────────────────────────────────────

    def _close(self, *_args):
        if self.on_done:
            self.on_done()