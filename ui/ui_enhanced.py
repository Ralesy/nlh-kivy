#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced UI Components: Polished Kivy canvas-based UI elements
for a fantasy RPG game with beautiful visual effects.

All components use only Kivy canvas instructions - no external images or fonts.
"""

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
import math


# Color palette for fantasy aesthetic
FANTASY_COLORS = {
    'dark_brown': (0.10, 0.09, 0.07, 1),        # Very dark background
    'panel_brown': (0.18, 0.15, 0.12, 0.95),    # Panel backgrounds
    'gold': (0.80, 0.70, 0.40, 1),              # Accent gold
    'copper': (0.75, 0.55, 0.35, 1),            # Copper border
    'parchment': (0.88, 0.85, 0.78, 1),         # Light text
    'deep_red': (0.65, 0.35, 0.30, 1),          # HP/damage color
    'dark_green': (0.28, 0.32, 0.22, 1),        # Dark forest green
    'dark_text': (0.15, 0.14, 0.12, 1),         # Dark text for light backgrounds
    'shadow': (0, 0, 0, 0.35),                  # Shadow color
    'glow': (0.72, 0.62, 0.35, 0.4),            # Glow effect
}


# ============================================================================
# HUD PANEL - Top overlay with stats
# ============================================================================

class HUDPanel(BoxLayout):
    """
    Top HUD panel showing player stats with semi-transparent background,
    thin light border, and soft drop shadow.
    """
    
    def __init__(self, player=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.width = dp(700)
        self.height = dp(70)
        self.pos_hint = {'x': 0.01, 'top': 0.98}
        self.padding = dp(8)
        self.spacing = dp(4)
        self.player = player
        
        # Draw background with shadow and border
        self._draw_panel_background()
        self.bind(pos=self._on_pos_change, size=self._on_size_change)
        
        # Create stat display
        self._create_stat_rows()
    
    def _draw_panel_background(self):
        """Draw semi-transparent background with border and shadow."""
        with self.canvas.before:
            # Shadow effect (dark ellipse below)
            Color(0, 0, 0, 0.25)
            self._shadow = Ellipse(
                pos=(self.x - dp(10), self.y - dp(3)),
                size=(self.width + dp(20), dp(8))
            )
            
            # Main panel background
            Color(0, 0, 0, 0.45)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            
            # Thin light border
            Color(0.72, 0.62, 0.35, 0.6)
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=dp(1.5)
            )
    
    def _on_pos_change(self, instance, value):
        """Update canvas elements on position change."""
        self._bg.pos = value
        self._border.rectangle = (self.x, self.y, self.width, self.height)
        self._shadow.pos = (self.x - dp(10), self.y - dp(3))
    
    def _on_size_change(self, instance, value):
        """Update canvas elements on size change."""
        self._bg.size = value
        self._border.rectangle = (self.x, self.y, self.width, self.height)
        self._shadow.size = (self.width + dp(20), dp(8))
    
    def _create_stat_rows(self):
        """Create neat stat display rows."""
        # Row 1: Level, HP, DMG
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22), spacing=dp(12))
        
        level_label = Label(
            text='LVL: 1',
            font_size=dp(14),
            size_hint_x=None,
            width=dp(80),
            color=FANTASY_COLORS['gold'],
            bold=True
        )
        self.level_label = level_label
        row1.add_widget(level_label)
        
        hp_label = Label(
            text='HP: 100/100',
            font_size=dp(12),
            size_hint_x=None,
            width=dp(130),
            color=FANTASY_COLORS['parchment']
        )
        self.hp_label = hp_label
        row1.add_widget(hp_label)
        
        dmg_label = Label(
            text='DMG: 10',
            font_size=dp(12),
            size_hint_x=None,
            width=dp(100),
            color=FANTASY_COLORS['deep_red'],
            bold=True
        )
        self.dmg_label = dmg_label
        row1.add_widget(dmg_label)
        
        row1.add_widget(Widget())  # Spacer
        
        coins_label = Label(
            text='💰 0',
            font_size=dp(12),
            size_hint_x=None,
            width=dp(100),
            color=FANTASY_COLORS['gold'],
            bold=True
        )
        self.coins_label = coins_label
        row1.add_widget(coins_label)
        
        self.add_widget(row1)
        
        # Row 2: XP and DEF
        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(24), spacing=dp(12))
        
        xp_label = Label(
            text='XP: 0/100',
            font_size=dp(11),
            size_hint_x=None,
            width=dp(110),
            color=FANTASY_COLORS['parchment']
        )
        self.xp_label = xp_label
        row2.add_widget(xp_label)
        
        def_label = Label(
            text='DEF: 5',
            font_size=dp(12),
            size_hint_x=None,
            width=dp(100),
            color=FANTASY_COLORS['dark_green'],
            bold=True
        )
        self.def_label = def_label
        row2.add_widget(def_label)
        
        row2.add_widget(Widget())  # Spacer
        
        self.add_widget(row2)
    
    def update_stats(self, level=None, hp=None, hp_max=None, dmg=None, 
                    def_stat=None, xp=None, xp_max=None, coins=None):
        """Update HUD display values."""
        if level is not None:
            self.level_label.text = f'LVL: {level}'
        if hp is not None and hp_max is not None:
            self.hp_label.text = f'HP: {int(hp)}/{int(hp_max)}'
        if dmg is not None:
            self.dmg_label.text = f'DMG: {int(dmg)}'
        if def_stat is not None:
            self.def_label.text = f'DEF: {int(def_stat)}'
        if xp is not None and xp_max is not None:
            self.xp_label.text = f'XP: {int(xp)}/{int(xp_max)}'
        if coins is not None:
            self.coins_label.text = f'💰 {int(coins)}'


# ============================================================================
# ENHANCED PROGRESS BAR - Rounded corners, two-layer effect, animation
# ============================================================================

class EnhancedProgressBar(Widget):
    """
    Beautiful progress bar with:
    - Rounded corners (simulated with rectangles)
    - Two-layer effect (dark background, bright foreground)
    - Thin border
    - Smooth animation on value changes
    """
    
    def __init__(self, max_value=100, current_value=50, 
                 bar_color=FANTASY_COLORS['deep_red'],
                 bg_color=(0.12, 0.12, 0.12, 1),
                 **kwargs):
        super().__init__(**kwargs)
        self.max_value = max_value
        self.current_value = current_value
        self.bar_color = bar_color
        self.bg_color = bg_color
        
        self.size_hint_y = None
        self.height = dp(24)
        
        self._padding = dp(2)  # Padding for rounded effect
        
        with self.canvas:
            # Background (darker layer)
            Color(*self.bg_color)
            self._bg_rect = Rectangle(
                pos=(self.x + self._padding, self.y + self._padding),
                size=(self.width - 2*self._padding, self.height - 2*self._padding)
            )
            
            # Foreground (bright layer)
            Color(*self.bar_color)
            bar_width = self._calculate_bar_width()
            self._bar_rect = Rectangle(
                pos=(self.x + self._padding, self.y + self._padding),
                size=(bar_width - 2*self._padding, self.height - 2*self._padding)
            )
            
            # Border
            Color(0.6, 0.5, 0.3, 0.7)
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=dp(1)
            )
        
        self.bind(pos=self._on_pos_change, size=self._on_size_change)
    
    def _calculate_bar_width(self):
        """Calculate foreground bar width based on current/max values."""
        if self.max_value <= 0:
            return 0
        ratio = max(0, min(1, self.current_value / self.max_value))
        return self.width * ratio
    
    def _on_pos_change(self, instance, value):
        """Update canvas on position change."""
        self._bg_rect.pos = (value[0] + self._padding, value[1] + self._padding)
        self._bar_rect.pos = (value[0] + self._padding, value[1] + self._padding)
        self._border.rectangle = (value[0], value[1], self.width, self.height)
    
    def _on_size_change(self, instance, value):
        """Update canvas on size change."""
        self._bg_rect.size = (value[0] - 2*self._padding, value[1] - 2*self._padding)
        bar_width = self._calculate_bar_width()
        self._bar_rect.size = (bar_width - 2*self._padding, value[1] - 2*self._padding)
        self._border.rectangle = (self.x, self.y, value[0], value[1])
    
    def set_value(self, current, max_val=None, animate=True):
        """
        Set progress bar value with optional animation.
        
        Args:
            current: Current value
            max_val: Maximum value (optional)
            animate: Whether to animate the change
        """
        if max_val is not None:
            self.max_value = max_val
        
        old_value = self.current_value
        self.current_value = min(current, self.max_value)
        
        if animate and old_value != self.current_value:
            # Smooth animation from old to new value
            anim = Animation(
                current_value=self.current_value,
                duration=0.3
            )
            anim.bind(on_progress=self._on_animation_progress)
            anim.start(self)
        else:
            self._on_size_change(self, self.size)
    
    def _on_animation_progress(self, animation, widget, progress):
        """Update bar during animation."""
        self._on_size_change(self, self.size)


# ============================================================================
# LOCATION MARKER - Map markers with glow and animations
# ============================================================================

class LocationMarker(Widget):
    """
    Enhanced location marker with:
    - Semi-transparent fill with opacity
    - Gold/copper border
    - Optional soft glow effect
    - Pulsing animation when in interaction radius
    """
    
    def __init__(self, x, y, name="Location", interactive=False, 
                 color=FANTASY_COLORS['gold'], **kwargs):
        super().__init__(**kwargs)
        self.marker_x = x
        self.marker_y = y
        self.name = name
        self.interactive = interactive
        self.marker_color = color
        self.radius = dp(12)
        self.pulse_anim = None
        self.is_pulsing = False
        
        self._draw_marker()
    
    def _draw_marker(self):
        """Draw the location marker with glow effect."""
        with self.canvas:
            # Outer glow (low opacity)
            Color(*self.marker_color[:-1], 0.15)
            self._glow = Ellipse(
                pos=(self.marker_x - self.radius*1.5, self.marker_y - self.radius*1.5),
                size=(self.radius*3, self.radius*3)
            )
            
            # Main circle fill (semi-transparent)
            Color(*self.marker_color[:-1], 0.30)
            self._fill = Ellipse(
                pos=(self.marker_x - self.radius, self.marker_y - self.radius),
                size=(self.radius*2, self.radius*2)
            )
            
            # Border
            Color(*self.marker_color)
            self._border = Line(
                circle=(self.marker_x, self.marker_y, self.radius),
                width=dp(2.5)
            )
    
    def start_pulse(self):
        """Start pulsing animation when player enters radius."""
        if not self.is_pulsing:
            self.is_pulsing = True
            # Pulse the radius
            anim = Animation(radius=self.radius*1.3, duration=0.6)
            anim += Animation(radius=self.radius, duration=0.6)
            anim.repeat = True
            anim.bind(on_progress=self._on_pulse_progress)
            self.pulse_anim = anim
            anim.start(self)
    
    def stop_pulse(self):
        """Stop pulsing animation."""
        if self.pulse_anim:
            self.pulse_anim.cancel(self)
            self.pulse_anim = None
        self.is_pulsing = False
        self.radius = dp(12)
        self._draw_marker()
    
    def _on_pulse_progress(self, animation, widget, progress):
        """Update marker during pulse animation."""
        self._draw_marker()
    
    def update_position(self, x, y):
        """Update marker position."""
        self.marker_x = x
        self.marker_y = y
        self._draw_marker()


# ============================================================================
# PLAYER MARKER - Enhanced player position indicator
# ============================================================================

class PlayerMarker(Widget):
    """
    Polished player marker with:
    - Soft outer glow
    - Breathing/pulse animation
    """
    
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.marker_x = x
        self.marker_y = y
        self.base_radius = dp(10)
        self.current_radius = self.base_radius
        self.glow_opacity = 0.3
        self.breathing = True
        
        self._draw_marker()
        self._start_breathing()
    
    def _draw_marker(self):
        """Draw the player marker with glow."""
        with self.canvas:
            # Outer glow (soft, pulsing opacity)
            Color(1.0, 0.95, 0.3, self.glow_opacity)
            self._glow = Ellipse(
                pos=(self.marker_x - self.current_radius*2, 
                     self.marker_y - self.current_radius*2),
                size=(self.current_radius*4, self.current_radius*4)
            )
            
            # Main circle (bright yellow)
            Color(1.0, 0.98, 0.4, 0.9)
            self._fill = Ellipse(
                pos=(self.marker_x - self.current_radius, 
                     self.marker_y - self.current_radius),
                size=(self.current_radius*2, self.current_radius*2)
            )
            
            # Inner highlight
            Color(1.0, 1.0, 0.6, 0.5)
            self._highlight = Ellipse(
                pos=(self.marker_x - self.current_radius*0.6, 
                     self.marker_y - self.current_radius*0.6),
                size=(self.current_radius*1.2, self.current_radius*1.2)
            )
            
            # Border
            Color(0.9, 0.85, 0.2, 1)
            self._border = Line(
                circle=(self.marker_x, self.marker_y, self.current_radius),
                width=dp(2)
            )
    
    def _start_breathing(self):
        """Start gentle breathing animation."""
        if self.breathing:
            anim = Animation(current_radius=self.base_radius*1.2, duration=1.2)
            anim += Animation(current_radius=self.base_radius, duration=1.2)
            anim.repeat = True
            anim.bind(on_progress=self._on_breathing_progress)
            self.breathing_anim = anim
            anim.start(self)
    
    def _on_breathing_progress(self, animation, widget, progress):
        """Update marker during breathing animation."""
        self._draw_marker()
    
    def update_position(self, x, y):
        """Update player marker position."""
        self.marker_x = x
        self.marker_y = y
        self._draw_marker()
    
    def stop(self):
        """Stop breathing animation."""
        if hasattr(self, 'breathing_anim'):
            self.breathing_anim.cancel(self)
        self.breathing = False


# ============================================================================
# ENHANCED BUTTON - Rounded-ish borders, hover/press effects
# ============================================================================

class EnhancedButton(Button):
    """
    Beautiful button with:
    - Rounded border appearance (using rectangles with spacing)
    - Hover visual effects
    - Press visual effects
    - Thin border outline
    """
    
    def __init__(self, color=FANTASY_COLORS['gold'], **kwargs):
        self.button_color = color
        self.base_color = color
        self.hover_color = self._brighten_color(color, 1.15)
        self.press_color = self._darken_color(color, 0.8)
        
        super().__init__(**kwargs)
        
        self.background_normal = ''
        self.background_down = ''
        self.color = FANTASY_COLORS['parchment']
        self.font_size = kwargs.get('font_size', dp(14))
        self.bold = True
        
        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            state=self._on_state_change
        )
        
        self._update_canvas()
    
    @staticmethod
    def _brighten_color(color, factor):
        """Brighten a color tuple."""
        return (
            min(1, color[0] * factor),
            min(1, color[1] * factor),
            min(1, color[2] * factor),
            color[3]
        )
    
    @staticmethod
    def _darken_color(color, factor):
        """Darken a color tuple."""
        return (
            color[0] * factor,
            color[1] * factor,
            color[2] * factor,
            color[3]
        )
    
    def _update_canvas(self, *args):
        """Update button canvas."""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.button_color)
            Rectangle(pos=self.pos, size=self.size)
            
            # Border
            Color(0.72, 0.62, 0.35, 0.8)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=dp(1.5))
    
    def _on_state_change(self, instance, value):
        """Handle button state changes."""
        if value == 'down':
            self.button_color = self.press_color
        else:
            self.button_color = self.base_color
        self._update_canvas()
    
    def on_enter(self):
        """Handle mouse enter."""
        self.button_color = self.hover_color
        self._update_canvas()
    
    def on_leave(self):
        """Handle mouse leave."""
        self.button_color = self.base_color if self.state == 'normal' else self.press_color
        self._update_canvas()


# ============================================================================
# UTILITY: Create a fancy border/frame using canvas
# ============================================================================

class CanvasBorder(Widget):
    """
    A decorative border/frame drawn with canvas instructions.
    Useful for framing panels and important UI elements.
    """
    
    def __init__(self, border_color=FANTASY_COLORS['copper'], 
                 border_width=dp(2), **kwargs):
        super().__init__(**kwargs)
        self.border_color = border_color
        self.border_width = border_width
        
        with self.canvas:
            Color(*self.border_color)
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=self.border_width
            )
        
        self.bind(pos=self._on_change, size=self._on_change)
    
    def _on_change(self, *args):
        """Update border on position/size change."""
        self._border.rectangle = (self.x, self.y, self.width, self.height)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_hud_panel(player=None):
    """Factory function to create a new HUD panel."""
    return HUDPanel(player=player)


def create_progress_bar(max_value=100, current_value=50, bar_type='health'):
    """
    Factory function to create progress bars.
    
    Args:
        max_value: Maximum value for the bar
        current_value: Starting current value
        bar_type: 'health', 'experience', 'mana', etc.
    """
    color_map = {
        'health': FANTASY_COLORS['deep_red'],
        'experience': (0.52, 0.42, 0.48, 1),
        'mana': (0.38, 0.45, 0.50, 1),
        'stamina': (0.45, 0.50, 0.35, 1),
    }
    
    bar_color = color_map.get(bar_type, FANTASY_COLORS['gold'])
    
    return EnhancedProgressBar(
        max_value=max_value,
        current_value=current_value,
        bar_color=bar_color,
        size_hint_x=1,
        size_hint_y=None,
        height=dp(24)
    )


def create_player_marker(x, y):
    """Factory function to create a player marker."""
    return PlayerMarker(x, y)


def create_location_marker(x, y, name="Location", color=FANTASY_COLORS['gold']):
    """Factory function to create a location marker."""
    return LocationMarker(x, y, name=name, color=color)
