#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
StatusPopup — всплывающее окно характеристик персонажа слева экрана.

Показывает: имя, класс, уровень, день, характеристики, очки навыков.
Без: ресурсов, экипировки, спутников, последних событий, статистики сессии.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle

from ui.ui_styles import COLORS


SKILL_DISPLAY = [
    ("endurance", "Выносливость", "+15 HP"),
    ("strength", "Сила", "+2 урона, +5 вместимости"),
    ("agility", "Ловкость", "+5% крит. шанса"),
    ("luck", "Удача", "+0.15 удачи"),
    ("trade", "Торговля", "+0.1 множ. продажи"),
    ("speed", "Скорость", "+15 скорости"),
]


class _TitleLabel(Label):
    """Золотой заголовок секции."""

    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = dp(14)
        self.size_hint_y = None
        self.height = dp(22)
        self.halign = 'left'
        self.valign = 'middle'
        self.color = COLORS['gold']
        self.bold = True


class _InfoLabel(Label):
    """Строка информации."""

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


class StatusPopup(BoxLayout):
    """Полупрозрачное окно характеристик персонажа (левая сторона экрана)."""

    def __init__(self, player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
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
            text='⚔️ ПЕРСОНАЖ',
            font_size=dp(20),
            size_hint_y=None,
            height=dp(34),
            color=COLORS['gold_light'],
            bold=True,
        )
        self.add_widget(title)

        # ── Информация ──
        self._info_labels = []
        info_widgets = BoxLayout(
            orientation='vertical', size_hint_y=None,
            padding=(dp(4), dp(2)), spacing=dp(1),
        )
        info_widgets.bind(minimum_height=info_widgets.setter('height'))
        info_widgets.add_widget(_TitleLabel(text='🎯 ОБЩАЯ ИНФОРМАЦИЯ'))
        for _ in range(4):
            lbl = _InfoLabel()
            self._info_labels.append(lbl)
            info_widgets.add_widget(lbl)
        self.add_widget(info_widgets)

        # ── Характеристики ──
        self._stat_labels = []
        stat_widgets = BoxLayout(
            orientation='vertical', size_hint_y=None,
            padding=(dp(4), dp(2)), spacing=dp(1),
        )
        stat_widgets.bind(minimum_height=stat_widgets.setter('height'))
        stat_widgets.add_widget(_TitleLabel(text='💪 ХАРАКТЕРИСТИКИ'))
        for _ in range(5):
            lbl = _InfoLabel()
            self._stat_labels.append(lbl)
            stat_widgets.add_widget(lbl)
        self.add_widget(stat_widgets)

        # ── Очки навыков ──
        skill_widgets = BoxLayout(
            orientation='vertical', size_hint_y=None,
            padding=(dp(4), dp(2)), spacing=dp(1),
        )
        skill_widgets.bind(minimum_height=skill_widgets.setter('height'))
        skill_widgets.add_widget(_TitleLabel(text='📊 ОЧКИ НАВЫКОВ'))
        self._pts_label = _InfoLabel()
        skill_widgets.add_widget(self._pts_label)

        self._skill_buttons = []
        for skill_key, display_name, effect_text in SKILL_DISPLAY:
            row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(24),
                spacing=dp(4),
            )
            name_lbl = _InfoLabel(
                text=f"{display_name}: 0",
                size_hint_x=0.55,
            )
            effect_lbl = _InfoLabel(
                text=f"({effect_text})",
                size_hint_x=0.35,
                color=COLORS['stone_light'],
            )
            btn = Button(
                text='+',
                size_hint=(None, None),
                size=(dp(22), dp(22)),
                font_size=dp(12),
                bold=True,
                background_color=COLORS['gold'],
                background_normal='',
                color=(0, 0, 0, 1),
            )
            btn.skill_key = skill_key
            btn.bind(on_press=self._on_allocate)
            row.add_widget(name_lbl)
            row.add_widget(effect_lbl)
            row.add_widget(btn)
            self._skill_buttons.append((skill_key, display_name, effect_text, name_lbl, effect_lbl, btn))
            skill_widgets.add_widget(row)

        self.add_widget(skill_widgets)

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
        """Обновить все данные."""
        p = self.player
        if not p:
            return

        bg_map = {
            "noble": "Обедневший дворянин",
            "squire": "Оруженосец",
            "hunter": "Охотник",
        }
        bg_display = bg_map.get(p.background, p.background)
        app = App.get_running_app()

        info_texts = [
            f"Имя: {p.name}",
            f"Класс: {bg_display}",
            f"Уровень: {p.level}  ⭐",
            f"День: {app.game.day}  📅" if app.game else "День: 1",
        ]
        info_colors = [
            COLORS['text_light'],
            COLORS['text_light'],
            COLORS['gold_light'],
            COLORS['stone_light'],
        ]
        for lbl, text, color in zip(self._info_labels, info_texts, info_colors):
            lbl.text = text
            lbl.color = color

        hp_pct = (p.health / p.max_health * 100) if p.max_health else 0
        crit_pct = int(p.critical_chance * 100)

        stat_texts = [
            (f"HP:  {p.health} / {p.max_health}  ({hp_pct:.0f}%)", (0.75, 0.30, 0.25, 1)),
            (f"Урон:  {p.damage}  ⚔️", (0.85, 0.55, 0.20, 1) if p.damage >= 15 else COLORS['gold_light']),
            (f"Защита:  {p.defense}  🛡️", (0.35, 0.50, 0.70, 1)),
            (f"Крит. шанс:  {crit_pct}%", COLORS['gold_light']),
            (f"Скорость:  {p.move_speed}  💨", (0.45, 0.60, 0.35, 1)),
        ]
        for lbl, (text, color) in zip(self._stat_labels, stat_texts):
            lbl.text = text
            lbl.color = color

        available = getattr(p, 'skill_points_available', 0)
        self._pts_label.text = f"Доступно очков: {available}"
        self._pts_label.color = COLORS['gold_light'] if available > 0 else COLORS['stone_light']

        for skill_key, display_name, effect_text, name_lbl, effect_lbl, btn in self._skill_buttons:
            level = p.skill_points_allocated.get(skill_key, 0)
            name_lbl.text = f"{display_name}: {level}"
            effect_lbl.text = f"({effect_text})"
            has = available > 0
            btn.disabled = not has
            btn.opacity = 1.0 if has else 0.3

    def _on_allocate(self, btn) -> None:
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and player.allocate_skill_point(btn.skill_key):
            self._refresh()
            hud = getattr(app, 'game_hud', None)
            if hud:
                try:
                    hud.update()
                except Exception:
                    pass

    def _close(self):
        if self.on_done:
            self.on_done()