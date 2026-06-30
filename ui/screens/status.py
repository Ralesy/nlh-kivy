#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран статуса персонажа с распределением очков навыков."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp

from ui.ui_styles import StyledLabel, COLORS
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import add_back_to_map_button


SKILL_DISPLAY = [
    ("endurance", "Выносливость", "+15 HP"),
    ("strength", "Сила", "+2 урона, +5 вместимости"),
    ("agility", "Ловкость", "+5% крит. шанса"),
    ("luck", "Удача", "+0.15 удачи"),
    ("trade", "Торговля", "+0.1 множ. продажи"),
    ("speed", "Скорость", "+15 скорости"),
]

PANEL_BG = (0.16, 0.14, 0.12, 0.95)
PANEL_BORDER = (0.35, 0.30, 0.25, 0.6)


def _build_panel(widgets):
    panel = BoxLayout(
        orientation='vertical',
        size_hint_y=None,
        padding=(dp(10), dp(8)),
        spacing=dp(4),
    )
    with panel.canvas.before:
        Color(*PANEL_BG)
        bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(6)])
        Color(*PANEL_BORDER)
        border = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(6)])
    panel.bind(
        pos=lambda i, v: setattr(bg, 'pos', i.pos) or setattr(border, 'pos', i.pos),
        size=lambda i, v: setattr(bg, 'size', i.size) or setattr(border, 'size', i.size),
    )
    panel.bind(minimum_height=panel.setter('height'))
    for w in widgets:
        panel.add_widget(w)
    return panel


def _make_row():
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22))
    lbl = StyledLabel(
        text='',
        font_size=dp(13),
        size_hint_x=1,
        size_hint_y=1,
        halign='left',
        valign='middle',
        color=COLORS['text_light'],
        bold=False,
        shadow=False,
    )
    row.add_widget(lbl)
    return row, lbl


def _make_skill_row():
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28), spacing=dp(6))
    name_lbl = StyledLabel(
        text='',
        font_size=dp(13),
        size_hint_x=0.50,
        size_hint_y=1,
        halign='left',
        valign='middle',
        color=COLORS['text_light'],
        bold=False,
        shadow=False,
    )
    effect_lbl = StyledLabel(
        text='',
        font_size=dp(11),
        size_hint_x=0.30,
        size_hint_y=1,
        halign='left',
        valign='middle',
        color=COLORS['stone_light'],
        bold=False,
        shadow=False,
    )
    btn = Button(
        text='+',
        size_hint=(None, None),
        size=(dp(26), dp(26)),
        font_size=dp(15),
        bold=True,
        background_color=COLORS['gold'],
        background_normal='',
        color=(0, 0, 0, 1),
        opacity=0,
        disabled=True,
    )
    row.add_widget(name_lbl)
    row.add_widget(effect_lbl)
    row.add_widget(btn)
    return row, name_lbl, effect_lbl, btn


class StatusScreen(Screen, KeyboardHandler):
    """Экран статуса с возможностью распределения очков навыков."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        with self._root.canvas.before:
            Color(*COLORS['dark_bg'])
            self._bg = Rectangle()
            self._root.bind(
                size=lambda i, v: setattr(self._bg, 'size', i.size),
                pos=lambda i, v: setattr(self._bg, 'pos', i.pos),
            )

        title = StyledLabel(
            text='[Бой]  ПЕРСОНАЖ',
            font_size=dp(34),
            size_hint_y=None,
            height=dp(50),
            color=COLORS['gold_light'],
            bold=True,
        )
        self._root.add_widget(title)

        scroll = ScrollView(bar_width=dp(6))
        self._content = BoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            padding=(dp(4), 0),
        )
        self._content.bind(minimum_height=self._content.setter('height'))

        self._build_ui()
        scroll.add_widget(self._content)
        self._root.add_widget(scroll)
        self.add_widget(self._root)

        self._btn_back_map = add_back_to_map_button(self, self.manager)
        self.bind_keyboard()

    def _build_ui(self):
        c = self._content

        header = StyledLabel(
            text='[Цель]  ОБЩАЯ ИНФОРМАЦИЯ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._info_rows = []
        info_widgets = []
        for _ in ("name", "class", "level", "day"):
            row, lbl = _make_row()
            info_widgets.append(row)
            self._info_rows.append((row, lbl))
        c.add_widget(_build_panel(info_widgets))

        header = StyledLabel(
            text='[Статистика]  ОЧКИ НАВЫКОВ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._pts_lbl = StyledLabel(
            text='',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(22),
            color=COLORS['gold_light'],
            bold=True,
            shadow=False,
        )
        self._skill_controls = []
        skill_widgets = [self._pts_lbl]
        for skill_key, display_name, effect_text in SKILL_DISPLAY:
            row, name_lbl, effect_lbl, btn = _make_skill_row()
            btn.skill_key = skill_key
            btn.bind(on_press=self._on_allocate)
            skill_widgets.append(row)
            self._skill_controls.append((skill_key, display_name, effect_text, name_lbl, effect_lbl, btn))
        c.add_widget(_build_panel(skill_widgets))

        header = StyledLabel(
            text='[Сила]  ХАРАКТЕРИСТИКИ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._stat_rows = []
        stat_widgets = []
        for _ in ("hp", "damage", "defense", "crit", "speed"):
            row, lbl = _make_row()
            stat_widgets.append(row)
            self._stat_rows.append((row, lbl))
        c.add_widget(_build_panel(stat_widgets))

        header = StyledLabel(
            text='[Монеты]  РЕСУРСЫ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._res_rows = []
        res_widgets = []
        for _ in ("coins", "xp"):
            row, lbl = _make_row()
            res_widgets.append(row)
            self._res_rows.append((row, lbl))
        c.add_widget(_build_panel(res_widgets))

        header = StyledLabel(
            text='[Бой]  ЭКИПИРОВКА',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._equip_lbl = StyledLabel(
            text='',
            font_size=dp(13),
            size_hint_y=None,
            color=COLORS['text_light'],
            bold=False,
            shadow=False,
        )
        self._equip_lbl.bind(texture_size=lambda i, v: setattr(self._equip_lbl, 'height', v[1]))
        c.add_widget(_build_panel([self._equip_lbl]))

        header = StyledLabel(
            text='[Спутник]  СПУТНИКИ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._comp_lbl = StyledLabel(
            text='',
            font_size=dp(13),
            size_hint_y=None,
            color=COLORS['text_light'],
            bold=False,
            shadow=False,
        )
        self._comp_lbl.bind(texture_size=lambda i, v: setattr(self._comp_lbl, 'height', v[1]))
        c.add_widget(_build_panel([self._comp_lbl]))

        header = StyledLabel(
            text='[Статистика]  СТАТИСТИКА СЕССИИ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._sess_rows = []
        sess_widgets = []
        for _ in ("defeated", "battles", "dmg_dealt", "dmg_taken", "items"):
            row, lbl = _make_row()
            sess_widgets.append(row)
            self._sess_rows.append((row, lbl))
        c.add_widget(_build_panel(sess_widgets))

        header = StyledLabel(
            text='[Свиток]  ПОСЛЕДНИЕ СОБЫТИЯ',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(26),
            color=COLORS['gold'],
            bold=True,
            shadow=False,
        )
        c.add_widget(header)
        self._hist_lbl = StyledLabel(
            text='',
            font_size=dp(12),
            size_hint_y=None,
            color=COLORS['stone_light'],
            bold=False,
            shadow=False,
        )
        self._hist_lbl.bind(texture_size=lambda i, v: setattr(self._hist_lbl, 'height', v[1]))
        c.add_widget(_build_panel([self._hist_lbl]))

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action in ("exit_location", "open_menu", "open_locations") and pressed:
            try:
                if getattr(self, "_btn_back_map", None):
                    self._btn_back_map.trigger_action(duration=0)
                    return True
            except Exception:
                pass
        return False

    def _on_allocate(self, btn) -> None:
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and player.allocate_skill_point(btn.skill_key):
            self.update_status()
            hud = getattr(app, 'game_hud', None)
            if hud:
                try:
                    hud.update()
                except Exception:
                    pass

    def update_status(self) -> None:
        app = App.get_running_app()
        if not app.game:
            return
        p = app.game.player

        bg_map = {
            "noble": "Обедневший дворянин",
            "squire": "Оруженосец",
            "hunter": "Охотник",
        }
        bg_display = bg_map.get(p.background, p.background)

        info_texts = [
            f"Имя: {p.name}",
            f"Класс: {bg_display}",
            f"Уровень: {p.level}  [Уровень]",
            f"День: {app.game.day}  📅",
        ]
        for (_, lbl), text in zip(self._info_rows, info_texts):
            lbl.text = text

        available = getattr(p, 'skill_points_available', 0)
        self._pts_lbl.text = f"Доступно очков: {available}"

        for skill_key, display_name, effect_text, name_lbl, effect_lbl, btn in self._skill_controls:
            level = p.skill_points_allocated.get(skill_key, 0)
            name_lbl.text = f"{display_name}: {level}"
            effect_lbl.text = f"({effect_text})"
            has = available > 0
            btn.opacity = 1.0 if has else 0.3
            btn.disabled = not has

        hp_pct = (p.health / p.max_health * 100) if p.max_health else 0
        crit_pct = int(p.critical_chance * 100)

        stat_texts = [
            f"HP:  {p.health} / {p.max_health}  ({hp_pct:.0f}%)",
            f"Урон:  {p.damage}  [Бой]",
            f"Защита:  {p.defense}  [Защита]",
            f"Крит. шанс:  {crit_pct}%",
            f"Скорость:  {p.move_speed}  💨",
        ]
        stat_colors = [
            (0.75, 0.30, 0.25, 1),
            (0.85, 0.55, 0.20, 1) if p.damage >= 15 else COLORS['gold_light'],
            (0.35, 0.50, 0.70, 1),
            COLORS['gold_light'],
            (0.45, 0.60, 0.35, 1),
        ]
        for (_, lbl), text, color in zip(self._stat_rows, stat_texts, stat_colors):
            lbl.text = text
            lbl.color = color

        xp_progress = (p.experience / (p.level * 100)) * 100 if p.level > 0 else 0
        res_texts = [
            f"Монеты:  {p.coins}  [Монеты]",
            f"Опыт:  {p.experience} / {p.level * 100}  ({xp_progress:.0f}%)  [Опыт]",
        ]
        res_colors = [COLORS['gold_light'], (0.45, 0.60, 0.35, 1)]
        for (_, lbl), text, color in zip(self._res_rows, res_texts, res_colors):
            lbl.text = text
            lbl.color = color

        weapon_name = p.weapon.name if p.weapon else "—"
        armor_name = p.armor.name if p.armor else "—"
        self._equip_lbl.text = f"Оружие:  {weapon_name}\nБроня:    {armor_name}"

        if not p.companions:
            self._comp_lbl.text = "(Нет спутников)"
        else:
            lines = []
            for c in p.companions:
                status = "[Да]" if c.is_alive else "[Смерть]"
                lines.append(f"{c.name} ({c.role})  HP: {c.health}/{c.max_health}  DMG: {c.damage}  {status}")
            self._comp_lbl.text = "\n".join(lines)

        stats = p.get_session_stats()
        sess_texts = [
            f"Врагов повержено:  {stats['enemies_defeated']}  [Смерть]",
            f"Битв проведено:  {stats['battles_fought']}  [Бой]",
            f"Выданный урон:  {stats['total_damage_dealt']}  [Урон]",
            f"Полученный урон:  {stats['total_damage_taken']}  [Защита]",
            f"Предметов:  {stats['inventory_items']}  [Инвентарь]",
        ]
        for (_, lbl), text in zip(self._sess_rows, sess_texts):
            lbl.text = text

        if not app.game.history:
            self._hist_lbl.text = "(Нет событий)"
        else:
            self._hist_lbl.text = "\n".join(f"  • {h}" for h in app.game.history[-7:])