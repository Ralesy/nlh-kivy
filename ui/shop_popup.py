#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ShopPopup — всплывающее окно магазина (покупка/продажа).

Открывается поверх карты/локации, не затемняет фон.
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
from data.items import ItemDatabase, Weapon, Armor, Potion, WEAPON_MATERIALS, ARMOR_MATERIALS


class _StyledShopBtn(Button):
    """Маленькая стилизованная кнопка для магазина."""

    def __init__(self, text="", color=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = dp(11)
        self.size_hint_y = None
        self.height = dp(30)
        self.background_normal = ''
        self.background_down = ''
        self.bold = True
        self.color = (1, 1, 1, 1)
        self._bg_color = color or (0.25, 0.30, 0.40, 0.9)
        self._update_canvas()
        self.bind(
            pos=lambda i, v: self._update_canvas(),
            size=lambda i, v: self._update_canvas(),
        )

    def _update_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(0.4, 0.35, 0.25, 0.5)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(4)), width=dp(1))


class _ItemCard(BoxLayout):
    """Карточка товара: название, цена, кнопки."""
    pass


class ShopPopup(BoxLayout):
    """Всплывающее окно магазина (левая сторона экрана)."""

    def __init__(self, player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
        self.padding = dp(8)
        self.player = player
        self.on_done = on_done
        self._current_tab = "buy"
        self._price_mod = 1.0

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
            text='МАГАЗИН',
            font_size=dp(20),
            size_hint_y=None,
            height=dp(34),
            color=COLORS['gold_light'],
            bold=True,
        )
        self.add_widget(title)

        # ── Монеты ──
        self.coins_label = Label(
            text='',
            font_size=dp(13),
            size_hint_y=None,
            height=dp(22),
            color=COLORS['gold'],
            bold=True,
            halign='left',
            valign='middle',
        )
        self.add_widget(self.coins_label)

        # ── Вкладки ──
        tabs = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(4))
        self.btn_buy = _StyledShopBtn(
            text='📦 КУПИТЬ', color=(0.25, 0.30, 0.40, 0.9), size_hint_x=0.5,
        )
        self.btn_buy.bind(on_press=lambda x: self._show_tab('buy'))
        tabs.add_widget(self.btn_buy)

        self.btn_sell = _StyledShopBtn(
            text='💵 ПРОДАТЬ', color=(0.30, 0.25, 0.20, 0.9), size_hint_x=0.5,
        )
        self.btn_sell.bind(on_press=lambda x: self._show_tab('sell'))
        tabs.add_widget(self.btn_sell)
        self.add_widget(tabs)

        # ── Контент (скролл) ──
        scroll = ScrollView(size_hint_y=1, bar_width=dp(4))
        self.content_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
            padding=(dp(2), dp(2)),
        )
        self.content_layout.bind(minimum_height=self.content_layout.setter('height'))
        scroll.add_widget(self.content_layout)
        self.add_widget(scroll)

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

        self._show_tab('buy')

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _update_coins(self):
        self.coins_label.text = f"Монеты: {self.player.coins} "

    def _show_tab(self, tab):
        self._current_tab = tab
        self.content_layout.clear_widgets()
        self._update_coins()

        self.btn_buy._bg_color = (0.30, 0.35, 0.45, 0.95) if tab == 'buy' else (0.25, 0.30, 0.40, 0.9)
        self.btn_sell._bg_color = (0.35, 0.30, 0.25, 0.95) if tab == 'sell' else (0.30, 0.25, 0.20, 0.9)
        self.btn_buy._update_canvas()
        self.btn_sell._update_canvas()

        if tab == 'buy':
            self._show_buy()
        else:
            self._show_sell()

    def _show_buy(self):
        app = App.get_running_app()
        if not app.game:
            return

        self._price_mod = 1.0
        danger_text = ""
        if hasattr(app.game, 'danger_manager'):
            dm = app.game.danger_manager
            self._price_mod = dm.get_price_modifier()
            pct = int((self._price_mod - 1.0) * 100) if self._price_mod > 1.0 else 0
            tier_name = dm.tier_name
            icons = {"Безопасно": "[Зеленый]", "Повышенная опасность": "[Желтый]", "Критическая опасность": "[Оранжевый]", "Апокалипсис": "[Красный]"}
            icon = icons.get(tier_name, "[Зеленый]")
            if pct > 0:
                danger_text = f"{icon} {tier_name} | Цены +{pct}%"

        if danger_text:
            dl = Label(
                text=danger_text,
                font_size=dp(10),
                size_hint_y=None,
                height=dp(22),
                color=COLORS['stone_light'],
                halign='left',
                valign='middle',
            )
            self.content_layout.add_widget(dl)

        for iid, qty in app.game.shop.stock.items():
            item = ItemDatabase.get(iid)
            if not item:
                continue

            q = "∞" if qty is None else str(qty)
            price = int(item.price * self._price_mod)

            card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(42), spacing=dp(4))

            # Название + цена
            name_lbl = Label(
                text=f"{item.display_name()} — {price}({q})",
                font_size=dp(11),
                size_hint_x=0.65,
                halign='left',
                valign='middle',
                color=COLORS['text_light'],
            )
            card.add_widget(name_lbl)

            # Инфо
            btn_info = _StyledShopBtn(text='', color=(0.30, 0.30, 0.35, 0.9), size_hint_x=0.12)
            btn_info.bind(on_press=lambda x, it=item: self._item_info(it))
            card.add_widget(btn_info)

            # КУПИТЬ
            btn_buy = _StyledShopBtn(text='КУПИТЬ', color=(0.25, 0.45, 0.25, 0.9), size_hint_x=0.23)
            btn_buy.bind(on_press=lambda x, iid=iid: self._buy_item(iid))
            card.add_widget(btn_buy)

            self.content_layout.add_widget(card)

    def _show_sell(self):
        items = self.player.inventory.list_items()
        for item, qty in items:
            price = (item.price * qty) // 5

            card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(42), spacing=dp(4))

            name_lbl = Label(
                text=f"{item.display_name()} x{qty} → {price}",
                font_size=dp(11),
                size_hint_x=0.65,
                halign='left',
                valign='middle',
                color=COLORS['text_light'],
            )
            card.add_widget(name_lbl)

            btn_info = _StyledShopBtn(text='', color=(0.30, 0.30, 0.35, 0.9), size_hint_x=0.12)
            btn_info.bind(on_press=lambda x, it=item: self._item_info(it))
            card.add_widget(btn_info)

            btn_sell = _StyledShopBtn(text='ПРОДАТЬ', color=(0.45, 0.35, 0.20, 0.9), size_hint_x=0.23)
            btn_sell.bind(on_press=lambda x, iid=item.id: self._sell_item(iid))
            card.add_widget(btn_sell)

            self.content_layout.add_widget(card)

    def _item_info(self, item):
        info = f"{item.display_name()}\n\n"
        if isinstance(item, Weapon):
            info += f"Урон: {item.damage_bonus}\n"
            info += f"Материал: {WEAPON_MATERIALS.get(item.material, '?')}\n"
            info += f"Состояние: {item.condition_display}\n"
        elif isinstance(item, Armor):
            info += f"Защита: {item.defense}\n"
            info += f"Материал: {ARMOR_MATERIALS.get(item.material, '?')}\n"
            info += f"Состояние: {item.condition_display}\n"
        elif isinstance(item, Potion):
            info += f"Восстанавливает: {item.heal_amount} HP\n"
        info += f"Цена: {item.price} монет\n"
        if item.description:
            info += f"\n📝 {item.description}"
        if hasattr(item, 'ability') and item.ability:
            ab = item.ability
            info += f"\n\nСпособность: {ab.name}"
            if hasattr(ab, 'damage_per_hit'):
                info += f"\n+{ab.damage_per_hit} урона за удар"

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        scroll = ScrollView()
        lbl = Label(
            text=info, font_size=dp(14),
            size_hint_y=None, text_size=(dp(260), None),
            halign='left', valign='top',
        )
        lbl.bind(texture_size=lbl.setter('size'))
        scroll.add_widget(lbl)
        content.add_widget(scroll)
        btn_close = Button(text='Закрыть', size_hint_y=None, height=dp(40))
        content.add_widget(btn_close)

        popup = Popup(
            title='📖 Информация',
            content=content,
            size_hint=(0.6, 0.5),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    def _buy_item(self, item_id):
        app = App.get_running_app()
        if not app.game:
            return
        result = app.game.shop.buy(self.player, item_id, 1, price_modifier=self._price_mod)
        self._show_tab(self._current_tab)
        popup = Popup(
            title='Результат',
            content=Label(text=result),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

    def _sell_item(self, item_id):
        app = App.get_running_app()
        if not app.game:
            return
        result = self.player.sell(app.game.shop, item_id, 1)
        self._show_tab(self._current_tab)
        popup = Popup(
            title='Результат',
            content=Label(text=result),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

    def _close(self):
        if self.on_done:
            self.on_done()