#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CompanionsPopup — всплывающее окно управления отрядом.

Показывает список ВСЕХ персонажей отряда с их характеристиками.
Каждая карточка кликабельна — открывает меню действий (следовать / обмен).
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line

from ui.ui_styles import COLORS
from ui.trade_popup import TradePopup


class _PartyCard(BoxLayout):
    """Карточка одного члена отряда — кликабельная."""

    def __init__(self, player_obj, on_click, **kwargs):
        super().__init__(**kwargs)
        self.player = player_obj
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = dp(6)
        self.spacing = dp(6)

        # Рамка карточки
        with self.canvas.before:
            Color(0.12, 0.14, 0.18, 0.95)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*COLORS.get("border_gold", (0.6, 0.5, 0.3, 0.6)))
            self.border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(6)),
                width=dp(1),
            )
        self.bind(
            pos=lambda i, v: self._update_card_bg(),
            size=lambda i, v: self._update_card_bg(),
        )

        # Левая часть: имя + уровень
        left = BoxLayout(orientation="vertical", size_hint_x=0.35, spacing=dp(2))
        name_lbl = Label(
            text=player_obj.name,
            font_size=dp(14),
            bold=True,
            color=COLORS.get("gold_light", (0.9, 0.8, 0.5, 1)),
            halign="left", valign="middle",
            size_hint_y=0.5,
        )
        lvl_lbl = Label(
            text=f"LVL {player_obj.level}",
            font_size=dp(12),
            color=(0.7, 0.7, 0.7, 1),
            halign="left", valign="middle",
            size_hint_y=0.5,
        )
        left.add_widget(name_lbl)
        left.add_widget(lvl_lbl)

        # Правая часть: статы
        right = BoxLayout(orientation="vertical", size_hint_x=0.65, spacing=dp(1))
        stats = [
            f"HP: {player_obj.health}/{player_obj.max_health}",
            f"DMG: {player_obj.damage}  DEF: {player_obj.defense}",
            f"XP: {player_obj.experience}  COINS: {player_obj.coins}",
        ]
        for text in stats:
            lbl = Label(
                text=text,
                font_size=dp(11),
                color=(0.8, 0.85, 0.9, 1),
                halign="left", valign="middle",
                size_hint_y=None, height=dp(18),
            )
            right.add_widget(lbl)

        self.add_widget(left)
        self.add_widget(right)

        # Кнопка-имя для клика (прозрачная поверх всей карточки)
        btn = Button(
            text="",
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            background_normal="",
        )
        btn.bind(on_press=lambda _: on_click(self.player))
        self.add_widget(btn)

    def _update_card_bg(self):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(6))


class PartyActionMenu(BoxLayout):
    """Подменю действий для выбранного спутника (следовать / обмен)."""

    def __init__(self, target_player, all_players, on_close, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(6)
        self.padding = dp(10)
        self.target = target_player

        with self.canvas.before:
            Color(0.08, 0.1, 0.15, 0.96)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLORS.get("border_gold", (0.6, 0.5, 0.3, 0.6)))
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)),
                width=dp(1.2),
            )
        self.bind(
            pos=lambda i, v: self._update_bg(),
            size=lambda i, v: self._update_bg(),
        )

        # Заголовок
        title = Label(
            text=f"Действия: {target_player.name}",
            font_size=dp(16),
            size_hint_y=None, height=dp(34),
            color=COLORS.get("gold_light", (0.9, 0.8, 0.5, 1)),
            bold=True,
        )
        self.add_widget(title)

        # Кнопка "Следовать за..."
        btn_follow = Button(
            text="Следовать за...",
            size_hint_y=None, height=dp(40),
            font_size=dp(14),
            background_color=(0.3, 0.45, 0.55, 0.9),
            color=(1, 1, 1, 1),
            bold=True,
            background_normal="",
        )
        btn_follow.bind(on_press=lambda _: self._show_follow_menu())
        self.add_widget(btn_follow)

        # Кнопка "Обменяться вещами"
        btn_trade = Button(
            text="Обменяться вещами",
            size_hint_y=None, height=dp(40),
            font_size=dp(14),
            background_color=(0.3, 0.5, 0.35, 0.9),
            color=(1, 1, 1, 1),
            bold=True,
            background_normal="",
        )
        btn_trade.bind(on_press=lambda _: self._show_trade_menu())
        self.add_widget(btn_trade)

        # Закрыть
        btn_close = Button(
            text="\u2715 Назад",
            size_hint_y=None, height=dp(40),
            font_size=dp(13),
            background_color=(0.2, 0.22, 0.28, 0.95),
            color=(0.9, 0.9, 0.9, 1),
            bold=True,
            background_normal="",
        )
        btn_close.bind(on_press=lambda _: on_close())
        self.add_widget(btn_close)

        spacer = BoxLayout(size_hint_y=1)
        self.add_widget(spacer)

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _show_follow_menu(self):
        """Показать список персонажей для выбора цели следования."""
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(15))
        content.add_widget(Label(
            text=f"За кем {self.target.name} будет следовать?",
            font_size=dp(16), size_hint_y=None, height=dp(34),
        ))

        app = App.get_running_app()
        session = app.game if app.game else None
        candidates = []
        if session:
            # Все члены отряда, кроме самого target
            for pm in session.party_members:
                if pm is self.target:
                    continue
                candidates.append(pm)
            if session.player is not self.target:
                candidates.append(session.player)

        scroll = ScrollView(size_hint_y=1)
        list_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        list_box.bind(minimum_height=list_box.setter("height"))

        has_follow = getattr(self.target, "target_to_follow", None)
        if has_follow:
            btn_clear = Button(
                text=f"Отменить следование (сейчас: {has_follow})",
                size_hint_y=None, height=dp(40),
                font_size=dp(13),
                background_color=(0.5, 0.2, 0.2, 0.9),
                color=(1, 1, 1, 1),
                bold=True,
                background_normal="",
            )
            btn_clear.bind(on_press=lambda _: self._set_follow(None, content))
            list_box.add_widget(btn_clear)

        for candidate in candidates:
            btn = Button(
                text=f"{candidate.name} (LVL {candidate.level})",
                size_hint_y=None, height=dp(44),
                font_size=dp(14),
                background_color=(0.25, 0.3, 0.4, 0.9),
                color=(1, 1, 1, 1),
                bold=True,
                background_normal="",
            )
            btn.bind(on_press=lambda _, c=candidate: self._set_follow(c.name, content))
            list_box.add_widget(btn)

        btn_cancel = Button(
            text="Отмена",
            size_hint_y=None, height=dp(40),
            font_size=dp(14),
            background_color=(0.2, 0.22, 0.28, 0.95),
            color=(0.9, 0.9, 0.9, 1),
            background_normal="",
        )
        list_box.add_widget(btn_cancel)

        scroll.add_widget(list_box)
        content.add_widget(scroll)

        pop = Popup(
            title="",
            content=content,
            size_hint=(0.4, 0.6),
            background="",
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
            auto_dismiss=True,
        )
        for child in list_box.children:
            if isinstance(child, Button):
                if child.text == "Отмена":
                    child.bind(on_press=pop.dismiss)
        pop.open()

    def _set_follow(self, target_name, content_widget):
        """Установить или сбросить target_to_follow."""
        self.target.target_to_follow = target_name
        for child in App.get_running_app()._app_window.children:
            if hasattr(child, "dismiss"):
                child.dismiss()
                break
        result = Popup(
            title="Следование",
            content=Label(
                text=f"{self.target.name} теперь следует за {target_name}" if target_name
                else f"{self.target.name}: следование отменено",
            ),
            size_hint=(0.5, 0.25),
            background="",
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        result.open()

    def _show_trade_menu(self):
        """Открыть TradePopup для обмена с выбранным персонажем."""
        app = App.get_running_app()
        session = app.game if app.game else None
        if not session:
            return
        active_player = session.active_player if session else session.player
        if not active_player:
            return
        if active_player is self.target:
            # Сначала выберите с кем обменяться
            TradePopup.select_exchange_partner(self.target, session, self._open_trade_with)
        else:
            self._open_trade_with(active_player)

    def _open_trade_with(self, partner_player):
        """Открыть окно обмена между target и partner."""
        from kivy.clock import Clock

        content = TradePopup(self.target, partner_player, on_done=lambda: None)
        pop = Popup(
            title="",
            content=content,
            size_hint=(0.7, 0.85),
            background="",
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
            auto_dismiss=False,
        )
        for child in App.get_running_app()._app_window.children:
            if hasattr(child, "dismiss"):
                child.dismiss()
                break

        def open_popup(dt):
            pop.open()

        Clock.schedule_once(open_popup, 0.05)


class CompanionsPopup(BoxLayout):
    """Главное окно управления отрядом — список всех персонажей."""

    def __init__(self, player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(4)
        self.padding = dp(8)
        self.player_obj = player
        self.on_done = on_done

        # Фон
        with self.canvas.before:
            Color(0.08, 0.1, 0.15, 0.94)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLORS.get("border_gold", (0.6, 0.5, 0.3, 0.6)))
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)),
                width=dp(1.2),
            )
        self.bind(
            pos=lambda i, v: self._update_bg(),
            size=lambda i, v: self._update_bg(),
        )

        # Заголовок
        title = Label(
            text="\u041e\u0422\u0420\u042f\u0414",
            font_size=dp(20),
            size_hint_y=None, height=dp(34),
            color=COLORS.get("gold_light", (0.9, 0.8, 0.5, 1)),
            bold=True,
        )
        self.add_widget(title)

        # Список членов отряда
        self._card_container = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            padding=(dp(2), dp(4)),
        )
        self._card_container.bind(minimum_height=self._card_container.setter("height"))

        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self._card_container)
        self.add_widget(scroll)

        # Закрыть
        btn_close = Button(
            text="\u2715 \u0417\u0430\u043a\u0440\u044b\u0442\u044c",
            size_hint_y=None, height=dp(42),
            font_size=dp(15),
            background_color=(0.2, 0.22, 0.28, 0.95),
            color=(0.9, 0.9, 0.9, 1),
            bold=True,
            background_normal="",
        )
        btn_close.bind(on_press=lambda _: self._close())
        self.add_widget(btn_close)

        self._populate()

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _populate(self):
        """Заполнить список всех членов отряда."""
        self._card_container.clear_widgets()

        app = App.get_running_app()
        session = app.game if app.game else None
        if not session:
            lbl = Label(text="Нет активной игры", font_size=dp(14))
            self._card_container.add_widget(lbl)
            return

        all_members = []
        if session.player:
            all_members.append(session.player)
        for pm in session.party_members:
            if pm is not session.player:
                all_members.append(pm)

        if not all_members:
            lbl = Label(
                text="В отряде только вы.\nНаймите спутников в таверне!",
                font_size=dp(13),
                size_hint_y=None, height=dp(50),
                color=(0.7, 0.7, 0.7, 1),
            )
            self._card_container.add_widget(lbl)
            return

        for member in all_members:
            card = _PartyCard(member, on_click=self._on_member_click)
            self._card_container.add_widget(card)

    def _on_member_click(self, player_obj):
        """Открыть меню действий для выбранного члена отряда.
        Заменяет содержимое попапа на PartyActionMenu.
        """
        app = App.get_running_app()
        session = app.game if app.game else None
        all_players = []
        if session:
            if session.player:
                all_players.append(session.player)
            all_players.extend(session.party_members)

        # Закрываем текущий popup и открываем новый с меню действий
        for child in list(app._app_window.children):
            if hasattr(child, "dismiss"):
                child.dismiss()

        action_content = PartyActionMenu(
            player_obj, all_players,
            on_close=lambda: self._reopen_main(),
        )
        pop = Popup(
            title="",
            content=action_content,
            size_hint=(0.35, 0.6),
            pos_hint={"x": 0.02, "y": 0.2},
            auto_dismiss=True,
            background="",
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        pop.open()

    def _reopen_main(self):
        """Закрыть подменю и открыть главное окно заново."""
        # Popup с подменю закроется сам, а CompanionsPopup откроем снова
        app = App.get_running_app()
        from ui.companions_popup import CompanionsPopup
        from kivy.clock import Clock

        def open_main(dt):
            content = CompanionsPopup(
                app.game.player if app.game else None,
                on_done=lambda: None,
            )
            pop = Popup(
                title="",
                content=content,
                size_hint=(0.35, 0.85),
                pos_hint={"x": 0.02, "y": 0.07},
                auto_dismiss=True,
                background="",
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            pop.open()

        Clock.schedule_once(open_main, 0.05)

    def _close(self):
        if self.on_done:
            self.on_done()