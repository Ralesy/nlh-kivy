#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VISUAL SHOWCASE - How to use enhanced UI components

This file demonstrates all components with working examples.
Run this to see what each component looks like in action.
"""

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.clock import Clock
import math

from ui.ui_enhanced import (
    HUDPanel, EnhancedProgressBar, LocationMarker, PlayerMarker,
    EnhancedButton, FANTASY_COLORS, create_progress_bar,
    create_player_marker, create_location_marker
)


class ShowcaseScreen(FloatLayout):
    """Main showcase screen demonstrating all components."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Title
        title = Label(
            text='ENHANCED UI COMPONENT SHOWCASE',
            font_size=dp(24),
            color=FANTASY_COLORS['gold'],
            bold=True,
            size_hint=(None, None),
            size=(dp(600), dp(40)),
            pos=(dp(20), self.height - dp(60))
        )
        self.add_widget(title)
        
        # Create sections
        self._create_hud_section()
        self._create_buttons_section()
        self._create_progress_section()
        self._create_markers_section()
    
    def _create_hud_section(self):
        """Display HUD panel."""
        hud = HUDPanel()
        hud.pos_hint = None
        hud.pos = (dp(20), self.height - dp(150))
        hud.update_stats(
            level=10,
            hp=85,
            hp_max=100,
            dmg=20,
            def_stat=12,
            xp=750,
            xp_max=1000,
            coins=5000
        )
        self.add_widget(hud)
        self.hud = hud
        
        # Animate HUD stats
        Clock.schedule_interval(self._update_hud_demo, 0.1)
    
    def _update_hud_demo(self, dt):
        """Animate HUD stats for demo."""
        import math
        t = Clock.get_time()
        
        hp = 70 + int(30 * math.sin(t * 0.5))
        xp = int(750 + 250 * math.sin(t * 0.3))
        coins = 5000 + int(1000 * math.sin(t * 0.2))
        
        self.hud.update_stats(
            level=10 + int(2 * math.sin(t * 0.1)),
            hp=hp,
            hp_max=100,
            dmg=15 + int(5 * math.sin(t * 0.4)),
            def_stat=12,
            xp=xp,
            xp_max=1000,
            coins=coins
        )
    
    def _create_buttons_section(self):
        """Display various buttons."""
        buttons_container = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(dp(650), dp(80)),
            spacing=dp(10),
            pos=(dp(20), self.height - dp(250))
        )
        
        button_configs = [
            ("ATTACK", FANTASY_COLORS['deep_red']),
            ("DEFEND", FANTASY_COLORS['dark_green']),
            ("ESCAPE", FANTASY_COLORS['copper']),
            ("INVENTORY", FANTASY_COLORS['gold']),
        ]
        
        for text, color in button_configs:
            btn = EnhancedButton(
                text=text,
                color=color,
                size_hint_x=None,
                width=dp(140),
                height=dp(60),
                font_size=dp(14)
            )
            btn.bind(on_press=lambda x, t=text: print(f"Clicked: {t}"))
            buttons_container.add_widget(btn)
        
        self.add_widget(buttons_container)
        
        label = Label(
            text="BUTTONS - Hover to see color change",
            font_size=dp(12),
            color=FANTASY_COLORS['parchment'],
            size_hint=(None, None),
            size=(dp(400), dp(20)),
            pos=(dp(20), self.height - dp(275))
        )
        self.add_widget(label)
    
    def _create_progress_section(self):
        """Display progress bars."""
        progress_container = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(400), dp(150)),
            spacing=dp(8),
            pos=(dp(20), self.height - dp(420))
        )
        
        # Health bar
        health_label = Label(
            text="HEALTH:",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20),
            color=FANTASY_COLORS['deep_red']
        )
        progress_container.add_widget(health_label)
        
        health_bar = create_progress_bar(100, 75, 'health')
        progress_container.add_widget(health_bar)
        self.health_bar = health_bar
        
        # Experience bar
        xp_label = Label(
            text="EXPERIENCE:",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20),
            color=(0.52, 0.42, 0.48, 1)
        )
        progress_container.add_widget(xp_label)
        
        xp_bar = create_progress_bar(200, 100, 'experience')
        progress_container.add_widget(xp_bar)
        self.xp_bar = xp_bar
        
        self.add_widget(progress_container)
        
        # Animate progress bars
        Clock.schedule_interval(self._update_progress_demo, 0.05)
    
    def _update_progress_demo(self, dt):
        """Animate progress bars for demo."""
        import math
        t = Clock.get_time()
        
        hp = 50 + int(45 * math.sin(t * 0.7))
        self.health_bar.set_value(hp, animate=True)
        
        xp = int(100 + 95 * math.sin(t * 0.5))
        self.xp_bar.set_value(xp, animate=True)
    
    def _create_markers_section(self):
        """Display location and player markers."""
        marker_label = Label(
            text="MAP MARKERS - Player moves in circle, markers pulse when nearby",
            font_size=dp(12),
            color=FANTASY_COLORS['parchment'],
            size_hint=(None, None),
            size=(dp(600), dp(20)),
            pos=(dp(20), self.height - dp(500))
        )
        self.add_widget(marker_label)
        
        # Marker container
        self.marker_container = Widget(
            size_hint=(None, None),
            size=(dp(600), dp(300)),
            pos=(dp(20), self.height - dp(850))
        )
        self.add_widget(self.marker_container)
        
        # Location markers
        locations = [
            (dp(100), dp(100), "Forest", FANTASY_COLORS['dark_green']),
            (dp(500), dp(100), "Mountain", FANTASY_COLORS['copper']),
            (dp(100), dp(250), "Swamp", (0.4, 0.3, 0.2, 1)),
            (dp(500), dp(250), "Temple", FANTASY_COLORS['gold']),
        ]
        
        self.location_markers = []
        for x, y, name, color in locations:
            marker = LocationMarker(x, y, name, color=color)
            self.marker_container.add_widget(marker)
            self.location_markers.append((marker, x, y))
        
        # Player marker
        self.player_marker = PlayerMarker(dp(300), dp(175))
        self.marker_container.add_widget(self.player_marker)
        
        # Animate markers
        Clock.schedule_interval(self._update_markers_demo, 0.05)
    
    def _update_markers_demo(self, dt):
        """Animate player movement and marker interactions."""
        import math
        t = Clock.get_time()
        
        # Player moves in circle
        center_x = dp(300)
        center_y = dp(175)
        radius = dp(100)
        
        player_x = center_x + radius * math.cos(t * 0.3)
        player_y = center_y + radius * math.sin(t * 0.3)
        
        self.player_marker.update_position(player_x, player_y)
        
        # Check distance to each location
        for marker, loc_x, loc_y in self.location_markers:
            dist = ((player_x - loc_x)**2 + (player_y - loc_y)**2)**0.5
            
            if dist < dp(150):
                marker.start_pulse()
            else:
                marker.stop_pulse()


class EnhancedUIShowcaseApp(App):
    """Main app for showcasing enhanced UI components."""
    
    def build(self):
        """Build the showcase UI."""
        main_layout = FloatLayout()
        showcase = ShowcaseScreen()
        main_layout.add_widget(showcase)
        
        return main_layout


# ============================================================================
# HOW TO RUN THIS
# ============================================================================

"""
To see all enhanced UI components in action:

1. Make sure you're in the project directory
2. Run: python -m kivy.examples.run showcase_enhanced_ui.py
   
   OR
   
   python << 'EOF'
   from ui.showcase_enhanced_ui import EnhancedUIShowcaseApp
   app = EnhancedUIShowcaseApp()
   app.run()
   EOF

What you'll see:

- HUD Panel at top left showing player stats that animate
- Buttons that change color on hover
- Progress bars that animate smoothly
- Location markers on a mini-map that pulse when you're close
- Player marker that moves in a circle and breathes with animation

This demonstrates all the capabilities of the enhanced UI system!
"""


if __name__ == '__main__':
    app = EnhancedUIShowcaseApp()
    app.run()
