#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
import random
import os

BUTTONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'ui', 'buttons')


class LocalLocationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.location_id = None
        self.location_name = None
        self._defeated_enemies = set()
        self._player_pos = [0, 0]  # actual pixel position
        self._target_pos = None
        self._enemies = []
        self._current_enemy = None
        self._update_event = None
        self._entry_map_norm = None
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        self._drawing_widget = None
        self._btn_exit = None

    def on_enter(self):
        print(f"[DEBUG] LocalLocationScreen.on_enter: location_id={self.location_id}")
        self.layout.clear_widgets()
        
        # Load and add background image
        bg_path = f"assets/backgrounds/locations/{self.location_id}/{self.location_id}_map.png"
        try:
            bg = Image(source=bg_path, allow_stretch=True, keep_ratio=False, size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            self.layout.add_widget(bg)
            print(f"[DEBUG] Background loaded: {bg_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load background: {e}")
        
        # Initialize state
        self._target_pos = None
        self._enemies = []
        self._current_enemy = None
        self._player_pos = [self.width * 0.5, self.height * 0.5]
        
        # Create drawing widget for player and enemies
        self._drawing_widget = Widget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.layout.add_widget(self._drawing_widget)
        
        # Initialize enemies
        self._init_enemies()
        
        # Initialize UI (buttons, labels)
        self._init_ui()
        
        # Start update loop
        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1/60)
        
        print(f"[DEBUG] LocalLocationScreen ready with {len(self._enemies)} enemies")

    def _init_enemies(self):
        """Initialize 3 random enemies on the map."""
        for i in range(3):
            # Generate random position avoiding center (where player starts)
            while True:
                x_norm = random.uniform(0.1, 0.9)
                y_norm = random.uniform(0.3, 0.9)
                dist_from_center = ((x_norm - 0.5) ** 2 + (y_norm - 0.5) ** 2) ** 0.5
                if dist_from_center > 0.15:  # Keep away from center
                    break
            
            enemy = {
                'id': i,
                'x_norm': x_norm,
                'y_norm': y_norm,
                'x': self.width * x_norm,
                'y': self.height * y_norm,
                'radius': dp(12),
                'defeated': False
            }
            self._enemies.append(enemy)
        print(f"[DEBUG] Initialized {len(self._enemies)} enemies")

    def _init_ui(self):
        """Initialize UI elements (exit button, location name)."""
        # Exit button (top-right corner) - using Image widget
        btn_exit = Image(
            source=os.path.join(BUTTONS_DIR, 'global_map.png'),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={'right': 0.98, 'top': 0.98}
        )
        self.layout.add_widget(btn_exit)
        self._btn_exit = btn_exit
        self._btn_exit_rect = (btn_exit.pos[0], btn_exit.pos[1], btn_exit.size[0], btn_exit.size[1])
        print(f"[DEBUG] Exit button added at pos {btn_exit.pos} with size {btn_exit.size}")
        
        # Location name label (top-left)
        lbl_name = Label(
            text=self.location_name or 'Локация',
            size_hint=(None, None),
            size=(dp(200), dp(40)),
            pos_hint={'x': 0.02, 'top': 0.98},
            font_size='18sp'
        )
        self.layout.add_widget(lbl_name)

    def on_touch_down(self, touch):
        """Handle touch/click events for player movement."""
        # Check if touch hit the exit button
        if self._btn_exit:
            btn_x, btn_y = self._btn_exit.pos
            btn_w, btn_h = self._btn_exit.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                print(f"[DEBUG] Touch hit exit button at ({touch.x}, {touch.y})")
                self._on_exit_location()
                return True
        
        # If we get here, the click was on the map for movement
        print(f"[DEBUG] Touch at ({touch.x}, {touch.y}) - setting movement target")
        self._target_pos = [touch.x, touch.y]
        return True

    def _on_game_update(self, dt):
        """Main game loop update."""
        if not self.location_id:
            return
        
        # Update player position
        if self._target_pos:
            dx = self._target_pos[0] - self._player_pos[0]
            dy = self._target_pos[1] - self._player_pos[1]
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance < dp(8):
                # Reached target
                self._target_pos = None
                print("[DEBUG] Player reached target")
            else:
                # Move towards target
                speed = dp(200) * dt  # pixels per second
                move_dist = min(speed, distance)
                self._player_pos[0] += (dx / distance) * move_dist
                self._player_pos[1] += (dy / distance) * move_dist
        
        # Check collisions with enemies
        self._check_enemy_collisions()
        
        # Draw game state
        self._draw_game()

    def _check_enemy_collisions(self):
        """Check if player collides with any enemy and start battle."""
        if not self._drawing_widget:
            return
        
        player_radius = dp(12)
        for enemy in self._enemies:
            if enemy['defeated']:
                continue
            
            dx = self._player_pos[0] - enemy['x']
            dy = self._player_pos[1] - enemy['y']
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance < player_radius + enemy['radius']:
                print(f"[DEBUG] Collision with enemy {enemy['id']}!")
                self._start_battle_with_enemy(enemy)
                return

    def _start_battle_with_enemy(self, enemy):
        """Start a battle with the given enemy."""
        print(f"[DEBUG] Starting battle with enemy {enemy['id']}")
        self._current_enemy = enemy
        
        # Stop the game loop
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        
        # Get the app and player
        app = App.get_running_app()
        player = app.game.player
        
        # Generate enemy for battle
        try:
            from systems.battle import EnemyGenerator, Battlefield
            enemies = EnemyGenerator.generate_for_location(self.location_id, player.level, count=1)
            if not enemies:
                print(f"[ERROR] Failed to generate enemies for {self.location_id}")
                return
            
            # Create battlefield
            battlefield = Battlefield(player, enemies)
            
            # Mark that we're in a battle from local location
            app._battle_from_local_location = True
            app.battle_screen.from_local_location = True
            
            # Start the battle
            app.battle_screen.start_battle(battlefield, enemies[0].name)
            self.manager.current = 'battle'
        except Exception as e:
            print(f"[ERROR] Failed to start battle: {e}")
            import traceback
            traceback.print_exc()

    def on_return_from_battle(self):
        """Called when returning from a battle."""
        print("[DEBUG] Returning from battle")
        if self._current_enemy:
            self._current_enemy['defeated'] = True
            self._defeated_enemies.add(self._current_enemy['id'])
            self._current_enemy = None
        
        # Resume game loop
        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1/60)

    def _draw_game(self):
        """Draw player and enemies on the canvas."""
        if not self._drawing_widget:
            return
        
        self._drawing_widget.canvas.clear()
        with self._drawing_widget.canvas:
            # Draw enemies
            for enemy in self._enemies:
                if enemy['defeated']:
                    continue
                
                # Update position based on screen size
                enemy['x'] = self.width * enemy['x_norm']
                enemy['y'] = self.height * enemy['y_norm']
                
                # Draw enemy circle (red)
                Color(1, 0, 0, 0.7)
                Ellipse(
                    pos=(enemy['x'] - enemy['radius'], enemy['y'] - enemy['radius']),
                    size=(enemy['radius'] * 2, enemy['radius'] * 2)
                )
                Color(0.8, 0, 0, 1)
                Line(circle=(enemy['x'], enemy['y'], enemy['radius']), width=2)
            
            # Draw player (yellow)
            player_radius = dp(12)
            Color(1, 1, 0, 0.8)
            Ellipse(
                pos=(self._player_pos[0] - player_radius, self._player_pos[1] - player_radius),
                size=(player_radius * 2, player_radius * 2)
            )
            Color(1, 0.8, 0, 1)
            Line(circle=(self._player_pos[0], self._player_pos[1], player_radius), width=2)

    def _on_exit_location(self, *args):
        """Exit the local location and return to global map."""
        print("[DEBUG] Exiting local location")
        
        # Stop the update loop
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        
        # Clear state
        self.location_id = None
        self._enemies = []
        self._current_enemy = None
        self._target_pos = None
        
        # Auto-save game
        try:
            app = App.get_running_app()
            if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                from systems.save_system import save_game
                save_game(app.game.player, 'autosave')
                print("[DEBUG] Game auto-saved")
        except Exception as e:
            print(f"[DEBUG] Auto-save failed: {e}")
        
        # Return to location select screen
        self.manager.current = 'location_select'
        print("[DEBUG] Returned to location_select")
