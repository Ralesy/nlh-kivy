#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экраны инвентаря (обычный и боевой)."""

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
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import (
    add_back_to_map_button,
    add_back_to_city_button,
    sync_inventory_city_button,
)
from data.items import (
    Weapon, Armor, Potion,
    WEAPON_MATERIALS, ARMOR_MATERIALS,
)


class InventoryScreen(Screen, KeyboardHandler):
    """Экран инвентаря."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(12))

        with layout.canvas.before:
            Color(0.18, 0.22, 0.28, 1)
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, "size", i.size),
                pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            )

        title = Label(
            text="ИНВЕНТАРЬ",
            font_size=dp(40),
            size_hint_y=None,
            height=dp(70),
            color=(0.9, 0.8, 0.3, 1),
        )
        layout.add_widget(title)

        self.equipment_label = Label(
            text="",
            font_size=dp(19),
            size_hint_y=None,
            height=dp(85),
            text_size=(None, None),
            halign="left",
            valign="top",
            color=(0.9, 0.9, 0.9, 1),
        )
        layout.add_widget(self.equipment_label)

        scroll = ScrollView()
        self.items_layout = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter("height"))
        scroll.add_widget(self.items_layout)
        layout.add_widget(scroll)

        self.add_widget(layout)
        self._btn_back_map = add_back_to_map_button(self, self.manager)
        self._btn_back_city = add_back_to_city_button(self, self.manager)
        sync_inventory_city_button(self._btn_back_city)
        self.bind_keyboard()

    def on_enter(self, *args):
        """Скрыть «в город», если инвентарь открыт с карты или локации."""
        sync_inventory_city_button(self._btn_back_city)

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action in ("exit_location", "open_menu", "open_locations") and pressed:
            try:
                if getattr(self, "_btn_back_map", None):
                    self._btn_back_map.trigger_action(duration=0)
                    return True
            except Exception:
                pass
        return False

    def update_inventory(self):
        app = App.get_running_app()
        if not app.game:
            return

        p = app.game.player

        weapon_name = p.weapon.name if p.weapon else "Нет"
        armor_name = p.armor.name if p.armor else "Нет"
        self.equipment_label.text = (
            f"Оружие: {weapon_name}\n"
            f"Броня: {armor_name}"
        )

        self.items_layout.clear_widgets()
        items = p.inventory.list_items()
        for item, qty in items:
            item_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(80), spacing=dp(3))

            top_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
            item_label = Label(
                text=f"{item.display_name()} x{qty}",
                font_size=dp(16),
                size_hint_x=0.7,
            )
            top_layout.add_widget(item_label)

            btn_info = Button(
                text="",
                size_hint_x=0.1,
                background_color=COLORS["stone_light"],
            )
            btn_info.bind(on_press=lambda x, it=item: self.show_item_info(it))
            top_layout.add_widget(btn_info)
            item_layout.add_widget(top_layout)

            btn_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(5))

            if isinstance(item, Weapon) or isinstance(item, Armor):
                btn_equip = Button(
                    text="Экипировать",
                    size_hint_x=0.5,
                    font_size=dp(12),
                    background_color=COLORS["stone_light"],
                )
                btn_equip.bind(on_press=lambda x, it=item: self.equip_item(it))
                btn_layout.add_widget(btn_equip)

            if (p.weapon and p.weapon.id == item.id) or (p.armor and p.armor.id == item.id):
                btn_unequip = Button(
                    text="Снять",
                    size_hint_x=0.5,
                    font_size=dp(12),
                    background_color=COLORS["stone_light"],
                )
                btn_unequip.bind(on_press=lambda x, it=item: self.unequip_item(it))
                btn_layout.add_widget(btn_unequip)

            if isinstance(item, Potion):
                btn_use = Button(
                    text="Использовать",
                    size_hint_x=0.5,
                    font_size=dp(12),
                    background_color=COLORS["stone_light"],
                )
                btn_use.bind(on_press=lambda x, it=item: self.use_potion(it))
                btn_layout.add_widget(btn_use)

            item_layout.add_widget(btn_layout)
            self.items_layout.add_widget(item_layout)

    def show_item_info(self, item):
        """Показать информацию о предмете (синхронизировано с магазином)."""
        lines = []
        lines.append(item.display_name())

        if isinstance(item, Weapon):
            lines.append(f"Урон: {item.damage_bonus}")
            mat = WEAPON_MATERIALS.get(item.material, "неизвестный")
            lines.append(f"Материал: {mat}")
            lines.append(f"Состояние: {item.condition_display}")
        elif isinstance(item, Armor):
            lines.append(f"Защита: {item.defense}")
            mat = ARMOR_MATERIALS.get(item.material, "неизвестная")
            lines.append(f"Материал: {mat}")
            lines.append(f"Состояние: {item.condition_display}")
        elif isinstance(item, Potion):
            lines.append(f"Восстанавливает: {item.heal_amount} HP")

        lines.append(f"Цена: {item.price} монет")
        if item.description:
            lines.append("")
            lines.append(f"📝 {item.description}")

        if hasattr(item, "ability") and item.ability:
            ab = item.ability
            lines.append("")
            lines.append(f"Способность: {ab.name} ({ab.ability_type})")
            if hasattr(ab, "damage_per_hit"):
                lines.append(f"+{ab.damage_per_hit} урона за удар")
            if hasattr(ab, "armor_ignore"):
                pct = int(ab.armor_ignore * 100)
                lines.append(f"Игнорирует {pct}% брони")
            if hasattr(ab, "crit_multiplier"):
                lines.append(f"Крит. множитель: x{ab.crit_multiplier}")

        popup_text = "\n".join(lines)
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        scroll = ScrollView()
        info_label = Label(
            text=popup_text,
            font_size=dp(16),
            size_hint_y=None,
            text_size=(dp(320), None),
            halign="left",
            valign="top",
        )
        info_label.bind(texture_size=info_label.setter("size"))
        scroll.add_widget(info_label)
        content.add_widget(scroll)

        btn_close = Button(text="Закрыть", size_hint_y=None, height=dp(48), background_color=COLORS["stone_light"])
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

    def equip_item(self, item):
        app = App.get_running_app()
        if not app.game:
            return

        if isinstance(item, Weapon):
            if app.game.player.equip_weapon(item):
                popup = Popup(
                    title="Успех",
                    content=Label(text=f"Экипировано {item.display_name()}"),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
            else:
                popup = Popup(
                    title="Ошибка",
                    content=Label(text="Не удалось экипировать. Проверьте инвентарь."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
        elif isinstance(item, Armor):
            if app.game.player.equip_armor(item):
                popup = Popup(
                    title="Успех",
                    content=Label(text=f"Экипировано {item.display_name()}"),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
            else:
                popup = Popup(
                    title="Ошибка",
                    content=Label(text="Не удалось экипировать. Проверьте инвентарь."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()

        self.update_inventory()

    def use_potion(self, potion):
        """Использование зелья с выбором цели."""
        app = App.get_running_app()
        if not app.game or not app.game.player:
            return

        player = app.game.player

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text=f"Кому дать {potion.display_name()}?", font_size=dp(18)))

        targets_layout = BoxLayout(orientation="vertical", spacing=dp(10))

        if player.is_alive and player.health < player.max_health:
            btn_player = Button(
                text=f"Игрок ({player.health}/{player.max_health} HP)",
                size_hint_y=None,
                height=dp(50),
            )
            btn_player.bind(on_press=lambda x: self._heal_target(potion, player))
            targets_layout.add_widget(btn_player)

        for companion in player.companions:
            if companion.is_alive and companion.health < companion.max_health:
                btn_comp = Button(
                    text=f"{companion.name} ({companion.health}/{companion.max_health} HP)",
                    size_hint_y=None,
                    height=dp(50),
                )
                btn_comp.bind(on_press=lambda x, c=companion: self._heal_target(potion, c))
                targets_layout.add_widget(btn_comp)

        content.add_widget(targets_layout)

        btn_cancel = Button(text="Отмена", size_hint_y=None, height=dp(50))
        content.add_widget(btn_cancel)

        popup = Popup(
            title="🎁 Использование зелья",
            content=content,
            size_hint=(0.7, 0.6),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        popup.open()

    def _heal_target(self, potion, target):
        """Лечение цели зельем."""
        app = App.get_running_app()
        if not app.game or not app.game.player:
            return

        player = app.game.player

        healed = target.heal(potion.heal_amount)
        player.inventory.remove(potion.id, 1)

        popup = None
        for widget in App.get_running_app()._app_window.children:
            if hasattr(widget, "dismiss"):
                popup = widget
                break
        if popup:
            popup.dismiss()

        result_popup = Popup(
            title="Зелье использовано",
            content=Label(
                text=f"{target.name} восстановил {healed} HP!\n"
                     f"({target.health}/{target.max_health} HP)",
                font_size=dp(18),
            ),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        result_popup.open()

        self.update_inventory()

    def unequip_item(self, item):
        app = App.get_running_app()
        if not app.game:
            return

        if isinstance(item, Weapon):
            if app.game.player.unequip_weapon():
                popup = Popup(
                    title="Успех",
                    content=Label(text="Оружие снято."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
        elif isinstance(item, Armor):
            if app.game.player.unequip_armor():
                popup = Popup(
                    title="Успех",
                    content=Label(text="Броня снята."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()

        self.update_inventory()


class BattleInventoryScreen(Screen):
    """Экран инвентаря в бою."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.battlefield = None

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        title = Label(text="ИНВЕНТАРЬ В БОЮ", font_size=dp(32), size_hint_y=None, height=dp(60))
        layout.add_widget(title)

        self.player_info = Label(
            text="",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(80),
            text_size=(None, None),
            halign="left",
            valign="top",
        )
        layout.add_widget(self.player_info)

        self.equipment_label = Label(text="", font_size=dp(18), size_hint_y=None, height=dp(60))
        layout.add_widget(self.equipment_label)

        scroll = ScrollView()
        self.items_layout = BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter("height"))
        scroll.add_widget(self.items_layout)
        layout.add_widget(scroll)

        btn_back = Button(text="← Назад в бой", size_hint_y=None, height=dp(50), font_size=dp(20))
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def update_inventory(self, battlefield):
        """Обновление инвентаря для боя."""
        self.battlefield = battlefield
        if not battlefield:
            return

        p = battlefield.player

        self.player_info.text = (
            f"HP: {p.health}/{p.max_health} | "
            f"DMG: {p.damage} | DEF: {p.defense}"
        )

        weapon_name = p.weapon.name if p.weapon else "Нет"
        armor_name = p.armor.name if p.armor else "Нет"
        self.equipment_label.text = (
            f"Оружие: {weapon_name} | Броня: {armor_name}"
        )

        self.items_layout.clear_widgets()
        items = p.inventory.list_items()

        for item, qty in items:
            item_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(70))

            item_info = BoxLayout(orientation="vertical", size_hint_x=0.6, spacing=dp(2))
            item_name = Label(
                text=f"{item.display_name()} x{qty}",
                font_size=dp(16),
                text_size=(None, None),
                halign="left",
                valign="top",
            )
            item_info.add_widget(item_name)

            if isinstance(item, Potion):
                desc = Label(
                    text=f"Восстанавливает {item.heal_amount} HP",
                    font_size=dp(12),
                    text_size=(None, None),
                    halign="left",
                    valign="top",
                    color=(0.7, 0.9, 0.7, 1),
                )
                item_info.add_widget(desc)

            item_layout.add_widget(item_info)

            btn_layout = BoxLayout(orientation="vertical", size_hint_x=0.4, spacing=dp(5))

            if isinstance(item, Potion):
                btn_use = Button(
                    text="Использовать",
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(14),
                )
                btn_use.bind(on_press=lambda x, it=item: self.use_item(it))
                btn_layout.add_widget(btn_use)

            if isinstance(item, Weapon) or isinstance(item, Armor):
                btn_equip = Button(
                    text="Экипировать",
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(14),
                )
                btn_equip.bind(on_press=lambda x, it=item: self.equip_item(it))
                btn_layout.add_widget(btn_equip)

            if (p.weapon and p.weapon.id == item.id) or (p.armor and p.armor.id == item.id):
                btn_unequip = Button(
                    text="Снять",
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(14),
                )
                btn_unequip.bind(on_press=lambda x, it=item: self.unequip_item(it))
                btn_layout.add_widget(btn_unequip)

            item_layout.add_widget(btn_layout)
            self.items_layout.add_widget(item_layout)

    def use_item(self, item):
        """Использование предмета в бою."""
        if not self.battlefield:
            return

        if not isinstance(item, Potion):
            popup = Popup(
                title="Ошибка",
                content=Label(text="Этот предмет нельзя использовать в бою."),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        result = self.battlefield.player.use_item(item.id, self.battlefield)

        self.update_inventory(self.battlefield)

        popup = Popup(
            title="Результат",
            content=Label(text=result),
            size_hint=(0.6, 0.3),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

        Clock.schedule_once(lambda dt: self.return_to_battle(), 1.0)

    def equip_item(self, item):
        """Экипировка предмета в бою."""
        if not self.battlefield:
            return

        p = self.battlefield.player

        if isinstance(item, Weapon):
            if p.equip_weapon(item):
                popup = Popup(
                    title="Успех",
                    content=Label(text=f"Экипировано {item.display_name()}"),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
                self.update_inventory(self.battlefield)
            else:
                popup = Popup(
                    title="Ошибка",
                    content=Label(text="Не удалось экипировать. Проверьте инвентарь."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
        elif isinstance(item, Armor):
            if p.equip_armor(item):
                popup = Popup(
                    title="Успех",
                    content=Label(text=f"Экипировано {item.display_name()}"),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
                self.update_inventory(self.battlefield)
            else:
                popup = Popup(
                    title="Ошибка",
                    content=Label(text="Не удалось экипировать. Проверьте инвентарь."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()

    def unequip_item(self, item):
        """Снятие экипировки в бою."""
        if not self.battlefield:
            return

        p = self.battlefield.player

        if isinstance(item, Weapon):
            if p.unequip_weapon():
                popup = Popup(
                    title="Успех",
                    content=Label(text="Оружие снято."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
                self.update_inventory(self.battlefield)
        elif isinstance(item, Armor):
            if p.unequip_armor():
                popup = Popup(
                    title="Успех",
                    content=Label(text="Броня снята."),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup.open()
                self.update_inventory(self.battlefield)

    def return_to_battle(self):
        """Возврат в бой после использования предмета."""
        app = App.get_running_app()
        battle_screen = app.battle_screen

        battle_screen.update_battle_display()

        if not battle_screen.battlefield.is_over():
            battle_screen.is_processing_turn = True
            battle_screen.update_battle_display()
            Clock.schedule_once(lambda dt: battle_screen.enemy_turn(), 1.0)
        else:
            battle_screen.is_processing_turn = False
            battle_screen.end_battle()

        self.manager.current = "battle"

    def on_back(self, instance):
        """Возврат в бой без действий."""
        self.manager.current = "battle"
