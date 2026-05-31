#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран статуса персонажа."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import StyledLabel, COLORS
from ui.widgets.navigation_buttons import add_back_to_map_button

class StatusScreen(Screen):
    """Экран статуса с красивым дизайном."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Основной layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Тёмный фон
        with main_layout.canvas.before:
            Color(*COLORS['dark_bg'])
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )
        
        # Заголовок
        title = StyledLabel(
            text='⚔️ ПЕРСОНАЖ',
            font_size=dp(40),
            size_hint_y=None,
            height=dp(60),
            color=COLORS['gold'],
            bold=True
        )
        main_layout.add_widget(title)
        
        # Прокручиваемая область
        scroll = ScrollView()
        self.status_label = StyledLabel(
            text='',
            font_size=dp(15),
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            color=COLORS['text_light']
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        scroll.add_widget(self.status_label)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # Добавить кнопку назад
        add_back_to_map_button(self, self.manager)
    
    def update_status(self):
        """Обновить информацию статуса."""
        app = App.get_running_app()
        if not app.game:
            return
        
        p = app.game.player
        stats = p.get_session_stats()
        
        # Прогресс до следующего уровня
        xp_progress = (p.experience / (p.level * 100)) * 100 if p.level > 0 else 0
        
        text = (
            f"═══════════════════════════════════\n"
            f"👤 ПЕРСОНАЖ\n"
            f"═══════════════════════════════════\n"
            f"Имя: {p.name}\n"
            f"Класс: {p.background}\n"
            f"Уровень: {p.level} ⭐\n"
            f"День: {app.game.day} 📅\n\n"
            f"═══════════════════════════════════\n"
            f"💪 ХАРАКТЕРИСТИКИ\n"
            f"═══════════════════════════════════\n"
            f"HP: {p.health}/{p.max_health}\n"
            f"Урон: {p.damage} ⚔️\n"
            f"Защита: {p.defense} 🛡️\n\n"
            f"═══════════════════════════════════\n"
            f"💰 РЕСУРСЫ\n"
            f"═══════════════════════════════════\n"
            f"Монеты: {p.coins} 💰\n"
            f"Опыт: {p.experience}/{p.level*100} ({int(xp_progress)}%) ✨\n\n"
        )
        
        # Экипировка
        weapon_name = p.weapon.name if p.weapon else "—"
        armor_name = p.armor.name if p.armor else "—"
        text += (
            f"═══════════════════════════════════\n"
            f"⚔️ ЭКИПИРОВКА\n"
            f"═══════════════════════════════════\n"
            f"Оружие: {weapon_name}\n"
            f"Броня: {armor_name}\n\n"
        )
        
        # Спутники
        text += (
            f"═══════════════════════════════════\n"
            f"🤝 СПУТНИКИ\n"
            f"═══════════════════════════════════\n"
        )
        if not p.companions:
            text += "  (Нет спутников)\n\n"
        else:
            for c in p.companions:
                status = "✅ Жив" if c.is_alive else "💀 Мертв"
                text += f"  • {c.name} ({c.role})\n"
                text += f"    HP: {c.health}/{c.max_health} | DMG: {c.damage} | {status}\n"
            text += "\n"
        
        # Статистика сессии
        text += (
            f"═══════════════════════════════════\n"
            f"📊 СТАТИСТИКА СЕССИИ\n"
            f"═══════════════════════════════════\n"
            f"Врагов повержено: {stats['enemies_defeated']} 💀\n"
            f"Битв проведено: {stats['battles_fought']} ⚔️\n"
            f"Выданный урон: {stats['total_damage_dealt']} 🔥\n"
            f"Полученный урон: {stats['total_damage_taken']} 🛡️\n"
            f"Предметов в инвентаре: {stats['inventory_items']} 🎒\n\n"
        )
        
        # История
        text += (
            f"═══════════════════════════════════\n"
            f"📜 ПОСЛЕДНИЕ СОБЫТИЯ\n"
            f"═══════════════════════════════════\n"
        )
        if not app.game.history:
            text += "  (Нет событий)\n"
        else:
            for h in app.game.history[-8:]:
                text += f"  • {h}\n"
        
        self.status_label.text = text
