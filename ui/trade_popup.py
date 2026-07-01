#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TradePopup — двухпанельный интерфейс обмена предметами между членами отряда.

Адаптировано из LootWindow для передачи Item объектов между инвентарями.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle


class TradePopup(BoxLayout):
    """
    Двухпанельный интерфейс обмена вещами.

    Левая панель: инвентарь персонажа A (source).
    Правая панель: инвентарь персонажа B (target).
    Кнопки → передают предмет от A к B.
    Кнопки ← передают предмет от B к A.
    """

    def __init__(self, source_player, target_player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)
        self.source = source_player
        self.target = target_player
        self.on_done = on_done

        with self.canvas.before:
            Color(0.08, 0.1, 0.15, 0.88)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos),
            size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
        )

        # Заголовок
        title = Label(
            text=f"\u041e\u0411\u041c\u0415\u041d: {source_player.name} \u2194 {target_player.name}",
            font_size=dp(20),
            size_hint_y=None,
            height=dp(40),
            bold=True,
            color=(0.9, 0.8, 0.5, 1),
        )
        self.add_widget(title)

        # Две колонки
        columns = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=1)

        # ===== ЛЕВАЯ ПАНЕЛЬ: source (персонаж A) =====
        left_box = self._build_panel(
            source_player,
            side="source",
            title=source_player.name,
        )
        columns.add_widget(left_box)

        # ===== ПРАВАЯ ПАНЕЛЬ: target (персонаж B) =====
        right_box = self._build_panel(
            target_player,
            side="target",
            title=target_player.name,
        )
        columns.add_widget(right_box)

        self.add_widget(columns)

        # Кнопка Готово
        done_btn = Button(
            text='\u2713 \u0413\u041e\u0422\u041e\u0412\u041e',
            size_hint_y=None, height=dp(50),
            font_size=dp(18),
            bold=True,
            background_color=(0.25, 0.35, 0.25, 0.9),
            color=(1, 1, 1, 1),
            background_normal='',
        )
        done_btn.bind(on_press=self._finish)
        self.add_widget(done_btn)

    def _build_panel(self, player, side, title):
        """Собрать панель инвентаря одного персонажа."""
        container = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_x=0.5)

        # Фон панели
        with container.canvas.before:
            Color(0.12, 0.14, 0.18, 0.9)
            panel_bg = Rectangle(pos=container.pos, size=container.size)
            container.bind(
                pos=lambda i, v: setattr(panel_bg, 'pos', i.pos),
                size=lambda i, v: setattr(panel_bg, 'size', i.size),
            )

        lbl_title = Label(
            text=f"{title}  (слотов: {player.inventory.used_slots}/{player.inventory.capacity})",
            font_size=dp(14),
            size_hint_y=None, height=dp(30),
            bold=True,
            color=(0.8, 0.85, 0.9, 1),
        )
        container.add_widget(lbl_title)

        layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(4))
        layout.bind(minimum_height=layout.setter('height'))

        items = player.inventory.list_items() if player.inventory else []
        for item, qty in items:
            row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None, height=dp(38),
                spacing=dp(4),
            )
            row.add_widget(Label(
                text=f"{item.display_name()} x{qty}",
                font_size=dp(12),
                size_hint_x=0.7,
                color=(0.9, 0.9, 0.9, 1),
            ))
            arrow = '\u2192' if side == 'source' else '\u2190'
            btn = Button(
                text=arrow,
                size_hint_x=0.3,
                size_hint_y=1,
                font_size=dp(16),
                bold=True,
                background_color=(0.3, 0.4, 0.5, 0.8),
                color=(1, 1, 1, 1),
                background_normal='',
            )
            btn.bind(on_press=lambda _, it=item, q=qty, s=side: self._transfer(it, q, s))
            row.add_widget(btn)
            layout.add_widget(row)

        if not items:
            layout.add_widget(Label(
                text="(пусто)",
                font_size=dp(12),
                color=(0.5, 0.5, 0.5, 1),
            ))

        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(layout)
        container.add_widget(scroll)
        return container

    def _transfer(self, item, qty, side):
        """Переместить предмет между инвентарями."""
        if side == 'source':
            # source -> target
            if self.source.inventory.qty(item.id) >= qty:
                if self.target.inventory.free_slots >= qty:
                    self.source.inventory.remove(item.id, qty)
                    self.target.inventory.add(item, qty)
        else:
            # target -> source
            if self.target.inventory.qty(item.id) >= qty:
                if self.source.inventory.free_slots >= qty:
                    self.target.inventory.remove(item.id, qty)
                    self.source.inventory.add(item, qty)

        # Обновляем обе панели
        self._refresh_panels()

    def _refresh_panels(self):
        """Перестроить обе панели (простая реинициализация)."""
        # Сохраняем ссылки для перестроения
        old_source = self.source
        old_target = self.target
        old_done = self.on_done

        self.clear_widgets()

        # Заголовок
        title = Label(
            text=f"\u041e\u0411\u041c\u0415\u041d: {old_source.name} \u2194 {old_target.name}",
            font_size=dp(20),
            size_hint_y=None, height=dp(40),
            bold=True,
            color=(0.9, 0.8, 0.5, 1),
        )
        self.add_widget(title)

        columns = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=1)
        columns.add_widget(self._build_panel(old_source, side="source", title=old_source.name))
        columns.add_widget(self._build_panel(old_target, side="target", title=old_target.name))
        self.add_widget(columns)

        done_btn = Button(
            text='\u2713 \u0413\u041e\u0422\u041e\u0412\u041e',
            size_hint_y=None, height=dp(50),
            font_size=dp(18),
            bold=True,
            background_color=(0.25, 0.35, 0.25, 0.9),
            color=(1, 1, 1, 1),
            background_normal='',
        )
        done_btn.bind(on_press=self._finish)
        self.add_widget(done_btn)

    def _finish(self, *_args):
        """Закрыть окно обмена."""
        for child in list(App.get_running_app()._app_window.children):
            if hasattr(child, "dismiss"):
                child.dismiss()
                break
        if self.on_done:
            self.on_done()

    # --- Статический метод для выбора партнёра ---

    @staticmethod
    def select_exchange_partner(current_player, session, on_selected):
        """Показать попап выбора персонажа для обмена."""
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(15))
        content.add_widget(Label(
            text="Выберите персонажа для обмена:",
            font_size=dp(16), size_hint_y=None, height=dp(34),
        ))

        candidates = []
        if session.player and session.player is not current_player:
            candidates.append(session.player)
        for pm in session.party_members:
            if pm is not current_player:
                candidates.append(pm)

        scroll = ScrollView(size_hint_y=1)
        list_box = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None)
        list_box.bind(minimum_height=list_box.setter('height'))

        for c in candidates:
            btn = Button(
                text=f"{c.name} (LVL {c.level})",
                size_hint_y=None, height=dp(44),
                font_size=dp(14),
                background_color=(0.25, 0.3, 0.4, 0.9),
                color=(1, 1, 1, 1),
                bold=True,
                background_normal='',
            )
            # Используем замыкание для фиксации c
            btn.bind(on_press=lambda _, cc=c: TradePopup._partner_chosen(cc, content, on_selected))
            list_box.add_widget(btn)

        btn_cancel = Button(
            text="Отмена",
            size_hint_y=None, height=dp(40),
            background_color=(0.2, 0.22, 0.28, 0.95),
            color=(0.9, 0.9, 0.9, 1),
            background_normal='',
        )
        list_box.add_widget(btn_cancel)
        scroll.add_widget(list_box)
        content.add_widget(scroll)

        pop = Popup(
            title="",
            content=content,
            size_hint=(0.35, 0.5),
            background="",
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
            auto_dismiss=True,
        )
        for child in list_box.children:
            if isinstance(child, Button) and child.text == "Отмена":
                child.bind(on_press=pop.dismiss)
        pop.open()

    @staticmethod
    def _partner_chosen(partner, popup_content, on_selected):
        for child in App.get_running_app()._app_window.children:
            if hasattr(child, "dismiss"):
                child.dismiss()
                break
        on_selected(partner)