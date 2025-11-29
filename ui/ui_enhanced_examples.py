#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example: How to integrate enhanced UI components into your Kivy game.

This file shows best practices for using HUDPanel, EnhancedProgressBar,
LocationMarker, PlayerMarker, and EnhancedButton in your game screens.
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.clock import Clock

from ui.ui_enhanced import (
    HUDPanel, EnhancedProgressBar, LocationMarker, PlayerMarker, EnhancedButton,
    FANTASY_COLORS, create_progress_bar, create_player_marker, create_location_marker
)


class ExampleGameScreen(FloatLayout):
    """
    Example screen showing how to use enhanced UI components.
    This demonstrates integration with your game logic.
    """
    
    def __init__(self, player=None, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        
        # Create HUD panel at top
        self.hud = HUDPanel(player=player)
        self.add_widget(self.hud)
        
        # Update HUD with player stats (call this whenever stats change)
        Clock.schedule_once(self._update_hud_demo, 0.1)
    
    def _update_hud_demo(self, dt):
        """Example: Update HUD with player stats."""
        if self.player:
            self.hud.update_stats(
                level=self.player.level,
                hp=self.player.hp,
                hp_max=self.player.max_hp,
                dmg=self.player.dmg,
                def_stat=self.player.defense,
                xp=self.player.xp,
                xp_max=self.player.xp_to_level,
                coins=self.player.coins
            )


class ExampleMapScreen(FloatLayout):
    """
    Example showing how to use location markers and player marker on a world map.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create HUD
        self.hud = HUDPanel()
        self.add_widget(self.hud)
        
        # Create a map container (in your actual game, this would be your map overlay)
        self.map_container = Widget(size_hint=None, size=(dp(800), dp(600)))
        self.map_container.pos = (dp(100), dp(100))
        self.add_widget(self.map_container)
        
        # Add location markers to the map
        self._create_location_markers()
        
        # Create player marker
        self.player_marker = create_player_marker(
            x=dp(400),
            y=dp(300)
        )
        self.add_widget(self.player_marker)
        
        # Simulate player movement
        Clock.schedule_interval(self._simulate_player_movement, 0.05)
    
    def _create_location_markers(self):
        """Add some example location markers."""
        locations = [
            (dp(200), dp(200), "Forest", FANTASY_COLORS['dark_green']),
            (dp(600), dp(200), "Mountains", FANTASY_COLORS['copper']),
            (dp(200), dp(400), "Swamp", (0.4, 0.3, 0.2, 1)),
            (dp(600), dp(400), "Ancient Temple", FANTASY_COLORS['gold']),
        ]
        
        for x, y, name, color in locations:
            marker = create_location_marker(x, y, name=name, color=color)
            self.add_widget(marker)
            self.map_container.add_widget(Widget())  # Placeholder for interaction
    
    def _simulate_player_movement(self, dt):
        """Example: Simulate player movement across the map."""
        import math
        import time
        
        # Simple circular movement pattern
        t = time.time() * 0.3
        x = dp(400) + dp(150) * math.cos(t)
        y = dp(300) + dp(150) * math.sin(t)
        
        self.player_marker.update_position(x, y)


class ExampleHUDDemo(FloatLayout):
    """
    Example showing HUD panel with animated progress bars.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # HUD panel
        self.hud = HUDPanel()
        self.add_widget(self.hud)
        
        # Simulate stat changes
        self.frame = 0
        Clock.schedule_interval(self._simulate_stat_changes, 0.1)
    
    def _simulate_stat_changes(self, dt):
        """Simulate HP and XP changes."""
        import math
        
        self.frame += 1
        
        # Simulate HP: oscillate between 50-95
        hp = 70 + int(25 * math.sin(self.frame * 0.05))
        
        # Simulate XP: gradually increase
        xp = (self.frame * 2) % 200
        
        # Update HUD
        self.hud.update_stats(
            level=5 + (self.frame // 100),
            hp=hp,
            hp_max=100,
            dmg=15 + (self.frame // 50),
            def_stat=8,
            xp=xp,
            xp_max=200,
            coins=1500 + self.frame
        )


class ExampleButtonsDemo(BoxLayout):
    """
    Example showing how to use EnhancedButton in your game.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(15)
        
        # Create various styled buttons
        buttons_config = [
            ("ATTACK", FANTASY_COLORS['deep_red']),
            ("DEFEND", FANTASY_COLORS['dark_green']),
            ("ESCAPE", FANTASY_COLORS['copper']),
            ("INVENTORY", FANTASY_COLORS['gold']),
            ("SETTINGS", FANTASY_COLORS['dark_brown']),
        ]
        
        for text, color in buttons_config:
            btn = EnhancedButton(
                text=text,
                color=color,
                size_hint_y=None,
                height=dp(50),
                font_size=dp(16)
            )
            btn.bind(on_press=self._on_button_press)
            self.add_widget(btn)
    
    def _on_button_press(self, instance):
        """Handle button press."""
        print(f"Button pressed: {instance.text}")


# ============================================================================
# INTEGRATION GUIDE
# ============================================================================

"""
QUICK INTEGRATION GUIDE:

1. Import the components at the top of your ui_app.py:
   
   from ui.ui_enhanced import (
       HUDPanel, EnhancedProgressBar, LocationMarker, PlayerMarker,
       EnhancedButton, FANTASY_COLORS
   )

2. In your GameScreen class, add the HUD:
   
   self.hud = HUDPanel(player=self.player)
   self.add_widget(self.hud)

3. Update HUD whenever player stats change:
   
   self.hud.update_stats(
       level=self.player.level,
       hp=self.player.hp,
       hp_max=self.player.max_hp,
       dmg=self.player.dmg,
       def_stat=self.player.defense,
       xp=self.player.xp,
       xp_max=self.player.xp_to_level,
       coins=self.player.coins
   )

4. For progress bars in inventory/status screens:
   
   hp_bar = create_progress_bar(
       max_value=100,
       current_value=75,
       bar_type='health'
   )
   container.add_widget(hp_bar)
   hp_bar.set_value(50, animate=True)  # Smooth animation

5. For map screens with location markers:
   
   marker = create_location_marker(
       x=500,
       y=300,
       name="Forest",
       color=FANTASY_COLORS['dark_green']
   )
   self.add_widget(marker)
   
   player = create_player_marker(x=400, y=250)
   self.add_widget(player)
   player.update_position(x, y)  # Update each frame

6. Replace plain Button widgets with EnhancedButton:
   
   btn = EnhancedButton(
       text="ATTACK",
       color=FANTASY_COLORS['deep_red'],
       size_hint_y=None,
       height=dp(50)
   )
   btn.bind(on_press=self.on_attack)
   container.add_widget(btn)

7. Color reference - use FANTASY_COLORS dict:
   
   FANTASY_COLORS = {
       'dark_brown': Dark background
       'panel_brown': Panel backgrounds
       'gold': Accent color
       'copper': Borders
       'parchment': Light text
       'deep_red': HP/damage
       'dark_green': Defense/nature
       'dark_text': Text on light backgrounds
       'shadow': Shadow effects
       'glow': Glow effects
   }

ANIMATION EXAMPLES:

# Smooth progress bar animation
bar.set_value(50, max_val=100, animate=True)

# Location marker pulsing
marker.start_pulse()  # Start when player enters radius
marker.stop_pulse()   # Stop when player leaves

# Player marker breathing (automatic)
marker = create_player_marker(x, y)  # Breathing starts automatically
marker.stop()  # Stop when needed

# HUD stat updates (instant)
hud.update_stats(
    level=10,
    hp=85,
    hp_max=100,
    dmg=20,
    def_stat=10,
    xp=50,
    xp_max=100,
    coins=5000
)
"""
