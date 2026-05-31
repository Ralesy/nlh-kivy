#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI Styles: переиспользуемые компоненты и цветовая схема для красивого интерфейса.
"""

import os

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.app import App

# Repo root (ui/ui_styles.py -> ui/ -> project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUTTONS_DIR = os.path.join(PROJECT_ROOT, "assets", "ui", "buttons")
BACKGROUNDS_DIR = os.path.join(PROJECT_ROOT, "assets", "backgrounds")


# ============================================================================
# ЦВЕТОВАЯ ПАЛИТРА - Натуральные, земляные тона
# ============================================================================

COLORS = {
    # Основные нейтральные цвета
    'dark_bg': (0.10, 0.09, 0.07, 1),           # Очень тёмный коричневый (земля)
    'panel': (0.18, 0.15, 0.12, 0.95),          # Тёмный коричневый (панели)
    'panel_light': (0.25, 0.22, 0.18, 0.95),    # Светло-коричневый (светлые панели)
    
    # Золотой акцент
    'gold': (0.80, 0.70, 0.40, 1),              # Приглушённое золото (листва)
    'gold_dark': (0.65, 0.55, 0.30, 1),         # Тёмное золото
    
    # Зелень (листва, трава)
    'green_leaf': (0.45, 0.50, 0.35, 1),        # Приглушённый зелёный (листья)
    'green_moss': (0.38, 0.42, 0.30, 1),        # Мох
    'green_dark': (0.28, 0.32, 0.22, 1),        # Тёмная листва
    
    # Камень
    'stone_light': (0.45, 0.42, 0.38, 1),       # Светлый камень
    'stone': (0.35, 0.33, 0.30, 1),             # Серый камень
    'stone_dark': (0.28, 0.26, 0.24, 1),        # Тёмный камень
    
    # Акценты для действий (более приглушённые)
    'hp_red': (0.65, 0.35, 0.30, 1),            # Ржавый красный (здоровье)
    'hp_green': (0.50, 0.55, 0.38, 1),          # Живой зелёный
    'mana_blue': (0.38, 0.45, 0.50, 1),         # Небесно-синий (вода)
    'xp_purple': (0.52, 0.42, 0.48, 1),         # Приглушённый фиолетовый
    
    # Текст
    'text_light': (0.88, 0.85, 0.78, 1),        # Светлый кремовый текст
    'text_dark': (0.15, 0.14, 0.12, 1),         # Тёмный коричневый текст
    
    # Граница
    'border_gold': (0.72, 0.62, 0.35, 0.7),     # Приглушённая золотая граница
    
    # Тень и эффекты
    'shadow': (0, 0, 0, 0.4),                   # Тень
}


# ============================================================================
# СТИЛИЗОВАННЫЕ КОМПОНЕНТЫ
# ============================================================================

class StyledButton(Button):
    """Красивая кнопка с золотой каёмкой."""
    
    def __init__(self, text="Button", color=None, **kwargs):
        self.button_color = color or COLORS['gold']
        super().__init__(**kwargs)
        self.text = text
        self.background_normal = ''
        self.background_down = ''
        self.background_color = self.button_color
        self.font_size = kwargs.get('font_size', dp(16))
        self.bold = True
        self.color = COLORS['text_light']
        
        # Рисуем фон с границей
        self._update_canvas()
        self.bind(pos=lambda i, v: self._update_canvas(),
                 size=lambda i, v: self._update_canvas())
    
    def _update_canvas(self):
        """Обновить canvas."""
        self.canvas.before.clear()
        with self.canvas.before:
            # Основной фон кнопки
            Color(*self.button_color)
            Rectangle(pos=self.pos, size=self.size)
            # Золотая граница
            Color(*COLORS['border_gold'])
            Line(rectangle=(self.x, self.y, self.width, self.height), width=dp(2))
    
    def on_enter(self):
        """Эффект при наведении мыши."""
        # Осветляем кнопку
        r = min(1, self.button_color[0] * 1.2)
        g = min(1, self.button_color[1] * 1.2)
        b = min(1, self.button_color[2] * 1.2)
        self.background_color = (r, g, b, self.button_color[3])
    
    def on_leave(self):
        """Эффект при уходе мыши."""
        self.background_color = self.button_color


class StyledLabel(Label):
    """Красивая метка с золотым цветом и тенью."""
    
    def __init__(self, text="", color=None, font_size=dp(16), bold=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color = color or COLORS['text_light']
        self.font_size = font_size
        self.bold = bold


class StyledPanel(BoxLayout):
    """Красивая панель с текстурой и золотой границей."""
    
    def __init__(self, title="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(12)
        self.spacing = dp(8)
        
        # Фон панели
        with self.canvas.before:
            # Основной тёмный фон
            Color(*COLORS['panel'])
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            # Золотая граница
            Color(*COLORS['border_gold'])
            self._border_line = Line(rectangle=(self.x, self.y, self.width, self.height), width=dp(1.5))
        
        self.bind(pos=lambda i, v: (setattr(self._bg_rect, 'pos', v), 
                                   setattr(self._border_line, 'rectangle', (i.x, i.y, i.width, i.height))),
                 size=lambda i, v: (setattr(self._bg_rect, 'size', v),
                                   setattr(self._border_line, 'rectangle', (self.x, self.y, v[0], v[1]))))
        
        # Заголовок если передан
        if title:
            header = StyledLabel(
                text=title,
                font_size=dp(18),
                size_hint_y=None,
                height=dp(35),
                color=COLORS['gold'],
                bold=True
            )
            self.add_widget(header)


class StatRow(BoxLayout):
    """Строка со статистикой (название: значение)."""
    
    def __init__(self, label_text="", value_text="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(28)
        
        # Левая метка (название)
        label = StyledLabel(
            text=label_text,
            font_size=dp(13),
            size_hint_x=0.5,
            color=COLORS['text_light']
        )
        self.add_widget(label)
        
        # Правое значение (значение)
        value = StyledLabel(
            text=value_text,
            font_size=dp(14),
            size_hint_x=0.5,
            color=COLORS['gold'],
            bold=True
        )
        self.value_label = value
        self.add_widget(value)
    
    def update_value(self, new_value):
        """Обновить значение на правой стороне."""
        self.value_label.text = str(new_value)


class CustomProgressBar(Widget):
    """Пользовательский прогресс-бар с текстурой (не конфликт с Kivy ProgressBar)."""
    
    def __init__(self, max_value=100, current_value=50, 
                 bar_color=None, bg_color=None, **kwargs):
        self.max_value = max_value
        self.current_value = current_value
        self.bar_color = bar_color or COLORS['hp_red']
        self.bg_color = bg_color or (0.12, 0.12, 0.12, 1)
        
        super().__init__(**kwargs)
        
        self.size_hint_y = None
        self.height = dp(20)
        
        with self.canvas:
            # Фон бара
            Color(*self.bg_color)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            # Передний план бара
            Color(*self.bar_color)
            bar_width = self._calculate_bar_width()
            self._bar_rect = Rectangle(pos=self.pos, size=(bar_width, self.height))
            # Граница
            Color(0.5, 0.5, 0.5, 0.5)
            self._border = Line(rectangle=(self.x, self.y, self.width, self.height), width=dp(0.5))
        
        self.bind(pos=self._update_pos,
                 size=self._update_size)
    
    def __setattr__(self, name, value):
        """Переопределить setattr чтобы игнорировать странные атрибуты."""
        if name in ('max', 'min', 'value'):
            # Kivy иногда пытается установить эти атрибуты, игнорируем
            return
        super().__setattr__(name, value)
    
    def _calculate_bar_width(self):
        """Рассчитать ширину передней части бара."""
        if self.max_value <= 0:
            return 0
        ratio = self.current_value / self.max_value
        return self.width * max(0, min(1, ratio))
    
    def _update_pos(self, instance, value):
        """Обновить позицию бара."""
        self._bg_rect.pos = value
        self._bar_rect.pos = value
        self._border.rectangle = (self.x, self.y, self.width, self.height)
    
    def _update_size(self, instance, value):
        """Обновить размер бара."""
        self._bg_rect.size = value
        bar_width = self._calculate_bar_width()
        self._bar_rect.size = (bar_width, self.height)
        self._border.rectangle = (self.x, self.y, self.width, self.height)
    
    def set_value(self, current, max_val=None):
        """Обновить значение бара."""
        if max_val is not None:
            self.max_value = max_val
        self.current_value = min(current, self.max_value)
        self._update_size(self, self.size)


class StatGrid(GridLayout):
    """Сетка статистики в 2 колонки."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 2
        self.spacing = dp(15)
        self.padding = dp(10)
        self.size_hint_y = None


class PopupTitle(Label):
    """Красивый заголовок для Popup'ов."""
    
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = dp(22)
        self.color = COLORS['gold']
        self.bold = True
        self.size_hint_y = None
        self.height = dp(40)


def create_styled_popup(title="", content_widget=None, width_hint=0.7, height_hint=0.5):
    """Создать красивый Popup."""
    from kivy.uix.popup import Popup
    
    main_box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
    
    # Заголовок
    title_label = PopupTitle(text=title)
    main_box.add_widget(title_label)
    
    # Контент
    if content_widget:
        main_box.add_widget(content_widget)
    
    popup = Popup(
        content=main_box,
        size_hint=(width_hint, height_hint),
        background='',
        separator_height=0
    )
    
    # Стилизованный фон Popup'а
    with popup.canvas.before:
        Color(*COLORS['panel'])
        popup_bg = Rectangle(pos=popup.pos, size=popup.size)
        # Граница
        Color(*COLORS['border_gold'])
        popup_border = Line(rectangle=(popup.x, popup.y, popup.width, popup.height), width=dp(2))
    
    def update_bg(instance, value):
        popup_bg.pos = instance.pos
        popup_bg.size = instance.size
        popup_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
    
    popup.bind(pos=update_bg, size=update_bg)
    
    return popup
