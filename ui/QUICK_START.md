#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QUICK START - Enhanced UI Components for Kivy RPG

Copy-paste ready examples for common use cases.
"""

# ============================================================================
# 1. ADD HUD PANEL TO ANY SCREEN
# ============================================================================

"""
Add this to your screen's __init__:

    from ui.ui_enhanced import HUDPanel
    from kivy.clock import Clock
    
    # Create HUD
    self.hud = HUDPanel(player=self.game.player)
    self.add_widget(self.hud)
    
    # Update HUD every 0.1 seconds
    Clock.schedule_interval(self._update_hud, 0.1)

Then add this method:

    def _update_hud(self, dt):
        if self.game and self.game.player:
            self.hud.update_stats(
                level=self.game.player.level,
                hp=self.game.player.hp,
                hp_max=self.game.player.max_hp,
                dmg=self.game.player.dmg,
                def_stat=self.game.player.defense,
                xp=self.game.player.xp,
                xp_max=self.game.player.xp_to_level,
                coins=self.game.player.coins
            )
"""


# ============================================================================
# 2. REPLACE BUTTONS WITH ENHANCED BUTTONS
# ============================================================================

"""
BEFORE:
    btn = Button(text='ATTACK', background_color=(0.8, 0.2, 0.2, 1))

AFTER:
    from ui.ui_enhanced import EnhancedButton, FANTASY_COLORS
    from kivy.metrics import dp
    
    btn = EnhancedButton(
        text='ATTACK',
        color=FANTASY_COLORS['deep_red'],
        size_hint_y=None,
        height=dp(50),
        font_size=dp(16)
    )
    btn.bind(on_press=self.on_attack_pressed)

Available colors:
    'dark_brown', 'panel_brown', 'gold', 'copper', 'parchment',
    'deep_red', 'dark_green', 'dark_text', 'shadow', 'glow'
"""


# ============================================================================
# 3. ADD PROGRESS BARS
# ============================================================================

"""
from ui.ui_enhanced import create_progress_bar
from kivy.metrics import dp

# Health bar
hp_bar = create_progress_bar(
    max_value=100,
    current_value=75,
    bar_type='health'
)
container.add_widget(hp_bar)

# Experience bar
xp_bar = create_progress_bar(
    max_value=200,
    current_value=120,
    bar_type='experience'
)
container.add_widget(xp_bar)

# Mana bar
mana_bar = create_progress_bar(
    max_value=50,
    current_value=30,
    bar_type='mana'
)
container.add_widget(mana_bar)

# Update with smooth animation
hp_bar.set_value(50, animate=True)

# Update instantly
hp_bar.set_value(60, animate=False)

Bar types available:
    'health', 'experience', 'mana', 'stamina'
"""


# ============================================================================
# 4. ADD MARKERS TO WORLD MAP
# ============================================================================

"""
from ui.ui_enhanced import create_player_marker, create_location_marker, FANTASY_COLORS
from kivy.clock import Clock

class MapScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create player marker
        self.player_marker = create_player_marker(x=400, y=300)
        self.add_widget(self.player_marker)
        
        # Create location marker
        forest = create_location_marker(
            x=200,
            y=200,
            name="Forest",
            color=FANTASY_COLORS['dark_green']
        )
        self.add_widget(forest)
        
        # Update positions each frame
        Clock.schedule_interval(self._update_markers, 0.05)
    
    def _update_markers(self, dt):
        # Update player position
        self.player_marker.update_position(
            self.player.x,
            self.player.y
        )
        
        # Check if player is close to locations
        dist_to_forest = ((self.player.x - 200)**2 + (self.player.y - 200)**2)**0.5
        if dist_to_forest < 100:
            forest_marker.start_pulse()  # Pulse when close
        else:
            forest_marker.stop_pulse()

# Location marker colors
Available: FANTASY_COLORS['dark_green'], ['copper'], ['gold'], etc.
"""


# ============================================================================
# 5. FULL INTEGRATION EXAMPLE
# ============================================================================

"""
# In your main screen class:

from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.metrics import dp

from ui.ui_enhanced import (
    HUDPanel, EnhancedButton, EnhancedProgressBar,
    create_player_marker, create_location_marker,
    FANTASY_COLORS
)

class GameScreen(FloatLayout):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        
        # ===== HUD SETUP =====
        self.hud = HUDPanel(player=game.player)
        self.add_widget(self.hud)
        
        # ===== INVENTORY BUTTON =====
        inv_btn = EnhancedButton(
            text='INVENTORY',
            color=FANTASY_COLORS['gold'],
            size_hint=(None, None),
            size=(dp(150), dp(50)),
            pos=(dp(20), dp(20))
        )
        inv_btn.bind(on_press=self.open_inventory)
        self.add_widget(inv_btn)
        
        # ===== MAP MARKERS =====
        self.player_marker = create_player_marker(
            x=game.player.x,
            y=game.player.y
        )
        self.add_widget(self.player_marker)
        
        self.location_markers = {}
        for loc_id, loc_data in game.locations.items():
            marker = create_location_marker(
                x=loc_data['x'],
                y=loc_data['y'],
                name=loc_data['name'],
                color=loc_data.get('marker_color', FANTASY_COLORS['gold'])
            )
            self.add_widget(marker)
            self.location_markers[loc_id] = marker
        
        # ===== UPDATE LOOP =====
        Clock.schedule_interval(self._update_game, 0.016)  # ~60 FPS
        Clock.schedule_interval(self._update_hud, 0.1)
    
    def _update_game(self, dt):
        # Update player marker position
        self.player_marker.update_position(
            self.game.player.x,
            self.game.player.y
        )
        
        # Update location marker interactions
        for loc_id, marker in self.location_markers.items():
            dist = ((self.game.player.x - marker.marker_x)**2 +
                   (self.game.player.y - marker.marker_y)**2)**0.5
            
            if dist < 100:
                marker.start_pulse()
            else:
                marker.stop_pulse()
    
    def _update_hud(self, dt):
        self.hud.update_stats(
            level=self.game.player.level,
            hp=self.game.player.hp,
            hp_max=self.game.player.max_hp,
            dmg=self.game.player.dmg,
            def_stat=self.game.player.defense,
            xp=self.game.player.xp,
            xp_max=self.game.player.xp_to_level,
            coins=self.game.player.coins
        )
    
    def open_inventory(self, instance):
        # Your inventory logic here
        pass
"""


# ============================================================================
# 6. COLOR SCHEME REFERENCE
# ============================================================================

"""
Use these colors throughout your UI for consistency:

FANTASY_COLORS = {
    'dark_brown':   (0.10, 0.09, 0.07, 1)      # Backgrounds
    'panel_brown':  (0.18, 0.15, 0.12, 0.95)   # Panels
    'gold':         (0.80, 0.70, 0.40, 1)      # Accents, important text
    'copper':       (0.75, 0.55, 0.35, 1)      # Borders, secondary accents
    'parchment':    (0.88, 0.85, 0.78, 1)      # Main text color
    'deep_red':     (0.65, 0.35, 0.30, 1)      # Health, damage, danger
    'dark_green':   (0.28, 0.32, 0.22, 1)      # Nature, defense, healing
    'dark_text':    (0.15, 0.14, 0.12, 1)      # Dark text on light BG
    'shadow':       (0, 0, 0, 0.35)             # Shadows
    'glow':         (0.72, 0.62, 0.35, 0.4)    # Glows
}

Best practices:
- Use 'gold' for titles and important information
- Use 'parchment' for regular text
- Use 'deep_red' for danger/attack actions
- Use 'dark_green' for defense/healing actions
- Use 'copper' for borders and outlines
"""


# ============================================================================
# 7. COMMON ISSUES & FIXES
# ============================================================================

"""
Issue: Button doesn't seem to have any visual effect
Fix: Make sure you imported FANTASY_COLORS and passed a color:
    btn = EnhancedButton(
        text='OK',
        color=FANTASY_COLORS['gold'],  # <-- Must specify color
        ...
    )

Issue: Progress bar doesn't move smoothly
Fix: Make sure animate=True when changing value:
    bar.set_value(50, animate=True)

Issue: Location marker not pulsing
Fix: Make sure to call start_pulse():
    marker.start_pulse()

Issue: HUD not showing stats
Fix: Make sure to call update_stats():
    hud.update_stats(
        level=5,
        hp=80,
        hp_max=100,
        dmg=15,
        def_stat=8,
        xp=500,
        xp_max=1000,
        coins=2500
    )

Issue: Player marker not visible
Fix: Make sure add_widget(player_marker) is called LAST,
     so it's on top of other elements
"""


# ============================================================================
# 8. PERFORMANCE TIPS
# ============================================================================

"""
For maximum performance:

1. Don't create new markers every frame
   BAD:
       marker = create_location_marker(...)
       self.add_widget(marker)  # In update loop!
   
   GOOD:
       self.marker = create_location_marker(...)
       self.add_widget(self.marker)
       # In update loop:
       self.marker.update_position(x, y)

2. Update positions only when needed
   BAD:
       def update(self, dt):
           for marker in self.markers:
               marker.update_position(marker.marker_x, marker.marker_y)
   
   GOOD:
       def update(self, dt):
           if self.player.moved:
               self.player_marker.update_position(self.player.x, self.player.y)

3. Use reasonable update frequencies
   - HUD: 0.1 seconds (10 times per second)
   - Markers: 0.05 seconds (20 times per second)
   - Not 0.001 seconds (1000 times per second!)

4. Use animate=False for non-critical updates
   bar.set_value(50, animate=False)  # Faster than animate=True
"""


# ============================================================================
# 9. NEXT STEPS
# ============================================================================

"""
1. Copy ui_enhanced.py to your project (already done)
2. Update your main ui_app.py to use the new components
3. Replace existing buttons with EnhancedButton
4. Replace existing progress bars with EnhancedProgressBar
5. Add HUDPanel to your GameScreen
6. Add markers to your MapScreen
7. Test that everything looks good
8. Adjust colors if needed using FANTASY_COLORS
9. Fine-tune animation timings for your game
10. Enjoy your beautiful fantasy UI!
"""
