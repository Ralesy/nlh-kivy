#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран магазина."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import StyledButton, StyledLabel, COLORS
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import (
    add_back_to_map_button,
    add_back_to_city_button,
)
from data.items import (
    ItemDatabase, Weapon, Armor, Potion,
    WEAPON_MATERIALS, ARMOR_MATERIALS,
)


class ShopScreen(Screen, KeyboardHandler):
    """Экран магазина."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        with layout.canvas.before:
            Color(*COLORS["dark_bg"])
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, "size", i.size),
                pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            )

        title = StyledLabel(
            text="[Магазин] МАГАЗИН",
            font_size=dp(36),
            size_hint_y=None,
            height=dp(60),
            color=COLORS["gold"],
            bold=True,
        )
        layout.add_widget(title)

        coins_label = StyledLabel(
            text="",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40),
            color=COLORS["gold"],
        )
        layout.add_widget(coins_label)
        self.coins_label = coins_label

        tab_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(5))
        btn_buy = StyledButton(
            text="📦 КУПИТЬ",
            color=COLORS["stone_light"],
            size_hint_x=0.5,
            font_size=dp(16),
        )
        btn_buy.bind(on_press=lambda x: self.show_buy())
        tab_layout.add_widget(btn_buy)

        btn_sell = StyledButton(
            text="💵 ПРОДАТЬ",
            color=COLORS["gold"],
            size_hint_x=0.5,
            font_size=dp(16),
        )
        btn_sell.bind(on_press=lambda x: self.show_sell())
        tab_layout.add_widget(btn_sell)
        layout.add_widget(tab_layout)

        scroll = ScrollView()
        self.content_layout = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self.content_layout.bind(minimum_height=self.content_layout.setter("height"))
        scroll.add_widget(self.content_layout)
        layout.add_widget(scroll)

        self.add_widget(layout)
        self._btn_back_map = add_back_to_map_button(self, self.manager)
        add_back_to_city_button(self, self.manager)
        self.current_tab = "buy"
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

    def update_shop(self):
        self.show_buy()

    def show_buy(self):
        self.current_tab = "buy"
        self.content_layout.clear_widgets()

        app = App.get_running_app()
        if not app.game:
            return

        self.coins_label.text = f"Ваши монеты: {app.game.player.coins} [Монеты]"

        # Получить модификатор цен от DangerManager
        price_mod = 1.0
        danger_info_text = ""
        if hasattr(app.game, 'danger_manager'):
            dm = app.game.danger_manager
            price_mod = dm.get_price_modifier()
            danger_level = dm.danger_level
            tier_name = dm.tier_name

            # Иконка градации
            tier_icons = {
                "Безопасно": "[Зеленый]",
                "Повышенная опасность": "[Желтый]",
                "Критическая опасность": "[Оранжевый]",
                "Апокалипсис": "[Красный]",
            }
            icon = tier_icons.get(tier_name, "[Зеленый]")

            if price_mod > 1.0:
                pct_increase = int((price_mod - 1.0) * 100)
                danger_info_text = (
                    f"{icon} Опасность: {danger_level:.0f}% ({tier_name}) "
                    f"— цены +{pct_increase}%"
                )
            else:
                danger_info_text = (
                    f"{icon} Опасность: {danger_level:.0f}% ({tier_name})"
                )

        # Показать индикатор опасности
        if danger_info_text:
            danger_color = COLORS["text_light"]
            if price_mod >= 2.0:
                danger_color = (0.9, 0.3, 0.2, 1)  # красный
            elif price_mod >= 1.5:
                danger_color = (0.9, 0.5, 0.2, 1)  # оранжевый
            elif price_mod >= 1.2:
                danger_color = (0.9, 0.8, 0.2, 1)  # жёлтый

            danger_label = StyledLabel(
                text=danger_info_text,
                font_size=dp(14),
                size_hint_y=None,
                height=dp(32),
                color=danger_color,
            )
            self.content_layout.add_widget(danger_label)

        for iid, qty in app.game.shop.stock.items():
            item = ItemDatabase.get(iid)
            if not item:
                continue

            q = "∞" if qty is None else str(qty)
            display_price = int(item.price * price_mod)

            item_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=dp(5))
            item_label = StyledLabel(
                text=f"{item.display_name()} — {display_price} [Монеты] (осталось: {q})",
                font_size=dp(14),
                size_hint_x=0.65,
                color=COLORS["text_light"],
            )
            item_layout.add_widget(item_label)

            btn_info = StyledButton(
                text="[Инфо]",
                color=COLORS["stone_light"],
                size_hint_x=0.1,
                font_size=dp(14),
            )
            btn_info.bind(on_press=lambda x, it=item: self.show_item_info(it))
            item_layout.add_widget(btn_info)

            btn_buy = StyledButton(
                text="КУПИТЬ",
                color=COLORS["hp_green"],
                size_hint_x=0.25,
                font_size=dp(12),
            )
            btn_buy.bind(on_press=lambda x, item_id=iid: self.buy_item(item_id))
            item_layout.add_widget(btn_buy)

            self.content_layout.add_widget(item_layout)

    def show_sell(self):
        self.current_tab = "sell"
        self.content_layout.clear_widgets()

        app = App.get_running_app()
        if not app.game:
            return

        self.coins_label.text = f"Ваши монеты: {app.game.player.coins} [Монеты]"

        items = app.game.player.inventory.list_items()
        for item, qty in items:
            item_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=dp(5))
            price = (item.price * qty) // 5
            item_label = StyledLabel(
                text=f"{item.display_name()} x{qty} → {price} [Монеты]",
                font_size=dp(14),
                size_hint_x=0.65,
                color=COLORS["text_light"],
            )
            item_layout.add_widget(item_label)

            btn_info = StyledButton(
                text="[Инфо]",
                color=COLORS["stone_light"],
                size_hint_x=0.1,
                font_size=dp(14),
            )
            btn_info.bind(on_press=lambda x, it=item: self.show_item_info(it))
            item_layout.add_widget(btn_info)

            btn_sell = StyledButton(
                text="ПРОДАТЬ",
                color=COLORS["stone_light"],
                size_hint_x=0.25,
                font_size=dp(12),
            )
            btn_sell.bind(on_press=lambda x, item_id=item.id: self.sell_item(item_id))
            item_layout.add_widget(btn_sell)

            self.content_layout.add_widget(item_layout)

    def show_item_info(self, item):
        """Показать информацию о предмете."""
        info_text = f"{item.display_name()}\n\n"

        if isinstance(item, Weapon):
            info_text += f"[Бой] Урон: {item.damage_bonus}\n"
            mat_str = WEAPON_MATERIALS.get(item.material, "неизвестный")
            info_text += f"Материал: {mat_str}\n"
            info_text += f"Состояние: {item.condition_display}\n"
        elif isinstance(item, Armor):
            info_text += f"[Защита] Защита: {item.defense}\n"
            mat_str = ARMOR_MATERIALS.get(item.material, "неизвестная")
            info_text += f"Материал: {mat_str}\n"
            info_text += f"Состояние: {item.condition_display}\n"
        elif isinstance(item, Potion):
            info_text += f"[HP] Восстанавливает: {item.heal_amount} HP\n"

        info_text += f"Цена: {item.price} монет\n"
        if item.description:
            info_text += f"\n📝 {item.description}"

        if hasattr(item, "ability") and item.ability:
            ab = item.ability
            info_text += "\n\n"
            info_text += f"Способность: {ab.name}"
            if hasattr(ab, "ability_type"):
                info_text += f" ({ab.ability_type})"
            info_text += "\n"
            if hasattr(ab, "damage_per_hit"):
                info_text += f"+{ab.damage_per_hit} урона за удар\n"
            if hasattr(ab, "armor_ignore"):
                ign_pct = int(ab.armor_ignore * 100)
                info_text += f"Игнорирует {ign_pct}% брони\n"
            if hasattr(ab, "crit_multiplier"):
                info_text += f"Крит. множитель: x{ab.crit_multiplier}\n"

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))
        scroll = ScrollView()
        info_label = Label(
            text=info_text,
            font_size=dp(16),
            size_hint_y=None,
            text_size=(dp(300), None),
            halign="left",
            valign="top",
        )
        info_label.bind(texture_size=info_label.setter("size"))
        scroll.add_widget(info_label)
        content.add_widget(scroll)

        btn_close = Button(text="Закрыть", size_hint_y=None, height=dp(50))
        content.add_widget(btn_close)

        popup = Popup(
            title="📖 Информация о предмете",
            content=content,
            size_hint=(0.8, 0.7),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    def buy_item(self, item_id):
        app = App.get_running_app()
        if not app.game:
            return

        # Получить модификатор цен от DangerManager
        price_mod = 1.0
        if hasattr(app.game, 'danger_manager'):
            price_mod = app.game.danger_manager.get_price_modifier()

        result = app.game.shop.buy(
            app.game.player, item_id, 1, price_modifier=price_mod
        )
        popup = Popup(
            title="Результат",
            content=Label(text=result),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
        self.show_buy()

    def sell_item(self, item_id):
        app = App.get_running_app()
        if not app.game:
            return

        result = app.game.player.sell(app.game.shop, item_id, 1)
        popup = Popup(
            title="Результат",
            content=Label(text=result),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
        self.show_sell()
