#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ENHANCED UI SYSTEM - COMPLETE DOCUMENTATION

This document describes all enhanced UI components and how to use them
in your Kivy RPG game.

All components use ONLY:
- Kivy canvas instructions (Color, Rectangle, Line, Ellipse)
- Built-in widgets (BoxLayout, Label, Button, Widget)
- NO external images, textures, or fonts

The UI has a cohesive fantasy aesthetic with dark browns, gold accents,
and deep natural colors.
"""

# ============================================================================
# COMPONENT OVERVIEW
# ============================================================================

"""
1. HUDPanel
   - Top overlay showing player stats
   - Semi-transparent dark background (rgba 0,0,0,0.45)
   - Thin light border
   - Soft drop shadow
   - Displays: Level, HP, Damage, Defense, XP, Coins
   
   Usage:
   ------
   hud = HUDPanel(player=game.player)
   screen.add_widget(hud)
   
   # Update when stats change
   hud.update_stats(
       level=10,
       hp=85,
       hp_max=100,
       dmg=20,
       def_stat=10,
       xp=500,
       xp_max=1000,
       coins=5000
   )

2. EnhancedProgressBar
   - Beautiful progress bars for HP, XP, Mana, etc.
   - Rounded corner effect (using padding)
   - Two-layer visual (dark background, bright foreground)
   - Thin border around bar
   - Smooth animation when values change
   
   Usage:
   ------
   hp_bar = create_progress_bar(
       max_value=100,
       current_value=75,
       bar_type='health'  # or 'experience', 'mana', 'stamina'
   )
   screen.add_widget(hp_bar)
   
   # Update with animation
   hp_bar.set_value(50, max_val=100, animate=True)
   
   # Update instantly (no animation)
   hp_bar.set_value(60, animate=False)

3. LocationMarker
   - Map markers showing locations
   - Semi-transparent fill (opacity 0.25-0.35)
   - Gold/copper border (2-3px)
   - Optional soft glow effect
   - Pulsing animation when player enters interaction radius
   
   Usage:
   ------
   marker = create_location_marker(
       x=500,
       y=300,
       name="Forest",
       color=FANTASY_COLORS['dark_green']
   )
   map_screen.add_widget(marker)
   
   # Start pulsing when player gets close
   marker.start_pulse()
   
   # Stop pulsing
   marker.stop_pulse()
   
   # Update position
   marker.update_position(new_x, new_y)

4. PlayerMarker
   - Player's position indicator on the map
   - Soft outer glow (semi-transparent)
   - Automatic breathing/pulse animation
   - Small inner highlight for depth
   
   Usage:
   ------
   player_marker = create_player_marker(x=400, y=300)
   map_screen.add_widget(player_marker)
   
   # Update position each frame (breathing continues automatically)
   player_marker.update_position(player.x, player.y)
   
   # Stop breathing when needed
   player_marker.stop()

5. EnhancedButton
   - Menu buttons, action buttons, etc.
   - Rounded border appearance
   - Hover visual effects (brightens)
   - Press visual effects (darkens)
   - Thin border outline
   
   Usage:
   ------
   btn = EnhancedButton(
       text="ATTACK",
       color=FANTASY_COLORS['deep_red'],
       size_hint_y=None,
       height=dp(50),
       font_size=dp(16)
   )
   btn.bind(on_press=self.on_attack_pressed)
   screen.add_widget(btn)

6. CanvasBorder
   - Decorative frame/border for important UI sections
   - Drawn entirely with canvas
   - Customizable color and width
   
   Usage:
   ------
   border = CanvasBorder(
       border_color=FANTASY_COLORS['copper'],
       border_width=dp(2),
       size=self.size,
       pos=self.pos
   )
   screen.add_widget(border)
"""


# ============================================================================
# COLOR PALETTE REFERENCE
# ============================================================================

"""
FANTASY_COLORS dictionary available in ui_enhanced.py:

{
    'dark_brown': (0.10, 0.09, 0.07, 1)         # Very dark background
    'panel_brown': (0.18, 0.15, 0.12, 0.95)     # Panel backgrounds
    'gold': (0.80, 0.70, 0.40, 1)               # Accent gold
    'copper': (0.75, 0.55, 0.35, 1)             # Copper borders
    'parchment': (0.88, 0.85, 0.78, 1)          # Light text
    'deep_red': (0.65, 0.35, 0.30, 1)           # HP/damage
    'dark_green': (0.28, 0.32, 0.22, 1)         # Defense/nature
    'dark_text': (0.15, 0.14, 0.12, 1)          # Dark text
    'shadow': (0, 0, 0, 0.35)                   # Shadows
    'glow': (0.72, 0.62, 0.35, 0.4)             # Glow effects
}

Usage:
------
from ui.ui_enhanced import FANTASY_COLORS

label = Label(color=FANTASY_COLORS['parchment'])
btn = EnhancedButton(color=FANTASY_COLORS['deep_red'])
"""


# ============================================================================
# PRACTICAL EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Complete Game Screen with HUD and Stats
---------------------------------------------------

from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from ui.ui_enhanced import HUDPanel, EnhancedProgressBar

class GameScreen(FloatLayout):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        
        # Add HUD at top
        self.hud = HUDPanel(player=player)
        self.add_widget(self.hud)
        
        # Update HUD every frame
        Clock.schedule_interval(self._update_hud, 0.1)
    
    def _update_hud(self, dt):
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


EXAMPLE 2: Map Screen with Markers
-----------------------------------

from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from ui.ui_enhanced import (
    HUDPanel, create_player_marker, create_location_marker,
    FANTASY_COLORS
)

class MapScreen(FloatLayout):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        
        # HUD
        self.hud = HUDPanel(player=player)
        self.add_widget(self.hud)
        
        # Location markers
        self.markers = []
        self._add_location("Forest", 200, 200, FANTASY_COLORS['dark_green'])
        self._add_location("Mountain", 600, 200, FANTASY_COLORS['copper'])
        self._add_location("Swamp", 200, 400, (0.4, 0.3, 0.2, 1))
        
        # Player marker
        self.player_marker = create_player_marker(
            player.x,
            player.y
        )
        self.add_widget(self.player_marker)
        
        # Update positions
        Clock.schedule_interval(self._update_positions, 0.05)
    
    def _add_location(self, name, x, y, color):
        marker = create_location_marker(x, y, name=name, color=color)
        self.add_widget(marker)
        self.markers.append(marker)
    
    def _update_positions(self, dt):
        # Update player marker position
        self.player_marker.update_position(self.player.x, self.player.y)
        
        # Check for location interactions
        for marker in self.markers:
            dist = ((self.player.x - marker.marker_x)**2 + 
                   (self.player.y - marker.marker_y)**2) ** 0.5
            
            if dist < 100:  # Within interaction radius
                marker.start_pulse()
            else:
                marker.stop_pulse()
    
    def on_location_enter(self, location_name):
        print(f"Entered: {location_name}")


EXAMPLE 3: Battle Screen with Action Buttons
---------------------------------------------

from kivy.uix.boxlayout import BoxLayout
from ui.ui_enhanced import EnhancedButton, FANTASY_COLORS

class BattleScreen(BoxLayout):
    def __init__(self, player, enemy, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(15)
        
        # Battle info (existing code)
        info_label = Label(text=f"Fighting: {enemy.name}")
        self.add_widget(info_label)
        
        # Action buttons
        actions_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        
        attack_btn = EnhancedButton(
            text="⚔️ ATTACK",
            color=FANTASY_COLORS['deep_red'],
            size_hint_y=None,
            height=dp(60)
        )
        attack_btn.bind(on_press=self.on_attack)
        actions_layout.add_widget(attack_btn)
        
        defend_btn = EnhancedButton(
            text="🛡️ DEFEND",
            color=FANTASY_COLORS['dark_green'],
            size_hint_y=None,
            height=dp(60)
        )
        defend_btn.bind(on_press=self.on_defend)
        actions_layout.add_widget(defend_btn)
        
        escape_btn = EnhancedButton(
            text="🏃 ESCAPE",
            color=FANTASY_COLORS['copper'],
            size_hint_y=None,
            height=dp(60)
        )
        escape_btn.bind(on_press=self.on_escape)
        actions_layout.add_widget(escape_btn)
        
        self.add_widget(actions_layout)
    
    def on_attack(self, instance):
        # Battle logic here
        pass
    
    def on_defend(self, instance):
        pass
    
    def on_escape(self, instance):
        pass


EXAMPLE 4: Status Screen with Character Stats and Progress Bars
----------------------------------------------------------------

from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from ui.ui_enhanced import (
    create_progress_bar, StyledLabel, FANTASY_COLORS
)
from kivy.metrics import dp

class StatusScreen(ScrollView):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # Title
        title = StyledLabel(
            text="CHARACTER STATUS",
            font_size=dp(24),
            color=FANTASY_COLORS['gold'],
            bold=True,
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(title)
        
        # HP section
        hp_label = StyledLabel(
            text="HEALTH POINTS",
            font_size=dp(16),
            color=FANTASY_COLORS['deep_red'],
            size_hint_y=None,
            height=dp(25)
        )
        main_layout.add_widget(hp_label)
        
        hp_bar = create_progress_bar(
            max_value=player.max_hp,
            current_value=player.hp,
            bar_type='health'
        )
        main_layout.add_widget(hp_bar)
        
        hp_text = Label(
            text=f"{int(player.hp)}/{int(player.max_hp)}",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20),
            color=FANTASY_COLORS['parchment']
        )
        main_layout.add_widget(hp_text)
        
        # XP section
        xp_label = StyledLabel(
            text="EXPERIENCE",
            font_size=dp(16),
            color=(0.52, 0.42, 0.48, 1),
            size_hint_y=None,
            height=dp(25)
        )
        main_layout.add_widget(xp_label)
        
        xp_bar = create_progress_bar(
            max_value=player.xp_to_level,
            current_value=player.xp,
            bar_type='experience'
        )
        main_layout.add_widget(xp_bar)
        
        xp_text = Label(
            text=f"{int(player.xp)}/{int(player.xp_to_level)}",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20),
            color=FANTASY_COLORS['parchment']
        )
        main_layout.add_widget(xp_text)
        
        self.add_widget(main_layout)
"""


# ============================================================================
# IMPLEMENTATION CHECKLIST
# ============================================================================

"""
When integrating enhanced UI into your game:

□ Import components at top of ui_app.py
□ Replace GameHUD with HUDPanel
□ Replace plain buttons with EnhancedButton
□ Add location markers to MapScreen
□ Add player marker to MapScreen
□ Replace progress bars with EnhancedProgressBar
□ Update animation loop to refresh marker positions
□ Test colors match fantasy aesthetic
□ Verify no external images/textures are used
□ Test hover effects on buttons
□ Test pulsing animations on location markers
□ Test breathing animation on player marker
□ Verify all animations are smooth (60 FPS)
□ Check performance with multiple markers
□ Ensure UI is responsive to window resizing
"""


# ============================================================================
# PERFORMANCE NOTES
# ============================================================================

"""
Canvas-based rendering is VERY lightweight:

- Each component uses only basic shapes (Ellipse, Rectangle, Line)
- No shader compilation
- Minimal GPU memory usage
- Suitable for low-end systems
- Smooth animations even with many markers

Optimization tips:
- Reuse LocationMarker instances instead of creating new ones
- Update marker positions only when needed
- Use update_position() instead of recreating markers
- Batch canvas updates when possible
- Schedule updates at reasonable intervals (0.05s = 20 FPS for movement)
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Issue: Buttons don't respond to clicks
Solution: Make sure button state is 'normal' or 'down', not disabled

Issue: Progress bar doesn't animate smoothly
Solution: Use animate=True parameter: bar.set_value(50, animate=True)

Issue: Player marker stops breathing
Solution: Marker stops when stop() is called. Don't call it unintentionally.

Issue: Location markers aren't visible
Solution: Check z-index - add markers BEFORE add_widget(map_container)

Issue: Canvas doesn't update on position change
Solution: All components have bind() calls - make sure you're using
         update_position() or the position/size bindings will handle it

Issue: Colors look wrong
Solution: Remember RGBA values are 0-1, not 0-255
         Use FANTASY_COLORS dict instead of guessing colors
"""
