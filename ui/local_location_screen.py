#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
import random
import os

try:
    from ui.ui_styles import COLORS
except ImportError:
    COLORS = {
        'stone_light': (0.7, 0.7, 0.7, 1),
        'hp_red': (0.8, 0.2, 0.2, 1)
    }

BUTTONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'ui', 'buttons')

# Фиксированные позиции врагов на карте (нормализованные координаты)
ENEMY_POSITIONS = [
    (0.23, 0.42),  # Левый враг
    (0.5, 0.44),  # Центральный враг
    (0.7, 0.25)   # Правый враг
]


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
        self._returning_from_battle = False
        self.btn_enter_cave = Button(
            text='Войти в пещеру',
            size_hint=(None, None),
            size=(dp(150), dp(50)),
            background_color=COLORS['stone_light'],
            opacity=0
        )
        self.btn_enter_cave.bind(on_press=self._enter_cave)

        # Hover tooltip widget
        self._hover_widget = Label(
            text='',
            size_hint=(None, None),
            size=(dp(200), dp(40)),
            color=COLORS['text_light'],
            opacity=0,
            halign='center',
            valign='middle'
        )
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        self._drawing_widget = None
        self._btn_exit = None
        self._player_label = None

    def on_enter(self):
        print(f"[DEBUG] LocalLocationScreen.on_enter: location_id={self.location_id}")
        app = App.get_running_app()
        app.return_to_local_location = True
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

        # Set player position
        if self._returning_from_battle:
            # Returning from battle: keep current position (already set)
            pass
        else:
            # Normal entry: restore saved position or default to center
            app = App.get_running_app()
            player = app.game.player if app.game else None
            if player and self.location_id in player.last_location_pos:
                x_norm, y_norm = player.last_location_pos[self.location_id]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * 0.5, self.height * 0.5]

        # Create drawing widget for player and enemies
        self._drawing_widget = Widget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.layout.add_widget(self._drawing_widget)

        # Initialize enemies
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if self.location_id and player and getattr(player, 'last_location_visited', None) == self.location_id:
            # Returning to location: use saved positions
            self._init_enemies(use_saved=True)
        else:
            # First entry to location: generate new random positions
            self._init_enemies(use_saved=False)
            if player:
                player.last_location_visited = self.location_id
        
        # Initialize UI (buttons, labels)
        self._init_ui()

        # Add cave button to layout
        self.layout.add_widget(self.btn_enter_cave)

        # Add hover tooltip
        self.layout.add_widget(self._hover_widget)

        # Create player name label
        app = App.get_running_app()
        if app.game and app.game.player:
            player_name = app.game.player.name
            self._player_label = Label(
                text=player_name,
                size_hint=(None, None),
                size=(dp(100), dp(25)),
                font_size=dp(14),
                color=COLORS['gold'],
                bold=True
            )
            self.layout.add_widget(self._player_label)

        # Bind mouse position for tooltips
        from kivy.core.window import Window
        try:
            Window.bind(mouse_pos=self._on_mouse_pos)
        except Exception:
            pass

        # Start update loop
        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1/60)
        
        print(f"[DEBUG] LocalLocationScreen ready with {len(self._enemies)} enemies")

    def _init_enemies(self, use_saved=False):
        """Initialize enemies on saved or random positions, skipping defeated ones."""
        from systems.battle import EnemyGenerator
        app = App.get_running_app()
        player = app.game.player if app.game else None

        # Get saved enemy positions and creatures or generate new ones
        saved_positions = []
        saved_creatures = []
        if use_saved and player and hasattr(player, 'last_enemy_positions') and self.location_id in player.last_enemy_positions:
            saved_positions = player.last_enemy_positions[self.location_id]
            if hasattr(player, 'last_enemy_creatures') and self.location_id in player.last_enemy_creatures:
                saved_creatures = player.last_enemy_creatures[self.location_id]
            print(f"[DEBUG] Using {len(saved_positions)} saved enemy positions: {saved_positions} and {len(saved_creatures)} creatures for {self.location_id}")
        else:
            # Generate random positions and creatures
            saved_positions = self._generate_random_enemy_positions(3)
            saved_creatures = []
            for _ in range(3):
                enemy_creature = EnemyGenerator.generate_for_location(self.location_id, player.level, count=1)[0] if player else None
                saved_creatures.append(enemy_creature)
            # Save for future use
            if player:
                if not hasattr(player, 'last_enemy_positions'):
                    player.last_enemy_positions = {}
                player.last_enemy_positions[self.location_id] = saved_positions
                if not hasattr(player, 'last_enemy_creatures'):
                    player.last_enemy_creatures = {}
                player.last_enemy_creatures[self.location_id] = saved_creatures
                print(f"[DEBUG] Generated and saved {len(saved_positions)} random enemy positions and creatures for {self.location_id}")

        for i in range(3):
            if i in self._defeated_enemies:
                continue  # Skip defeated enemy positions

            if i < len(saved_positions):
                x_norm, y_norm = saved_positions[i]
            else:
                # Fallback
                x_norm, y_norm = random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)

            # Use saved creature or generate new
            enemy_creature = saved_creatures[i] if i < len(saved_creatures) and saved_creatures[i] else (
                EnemyGenerator.generate_for_location(self.location_id, player.level, count=1)[0] if player else None
            )

            enemy = {
                'type': 'enemy',
                'id': i,
                'x_norm': x_norm,
                'y_norm': y_norm,
                'x': self.width * x_norm,
                'y': self.height * y_norm,
                'radius': dp(12),
                'defeated': False,
                'creature': enemy_creature,
                'name': enemy_creature.name if enemy_creature else 'Неизвестный',
                'level': enemy_creature.level if enemy_creature else 1,
            }
            self._enemies.append(enemy)

        # Add cave zone for forest if boss not defeated
        if self.location_id == 'forest' and player and 'forest_cave' not in player.defeated_bosses:
            zone = {
                'type': 'zone',
                'id': 'forest_cave',
                'x_norm': 0.7,
                'y_norm': 0.68,
                'x': self.width * 0.7,
                'y': self.height * 0.65,
                'radius': dp(50),  # Proximity radius
                'defeated': False,
                'description': 'Пещера с боссом: Безумный мародер'
            }
            self._enemies.append(zone)

        print(f"[DEBUG] Initialized {len(self._enemies)} enemies/zones")

    def _generate_random_enemy_positions(self, count=3):
        """Generate random enemy positions with minimum distance."""
        import random
        positions = []
        for _ in range(count):
            attempts = 0
            while attempts < 50:
                x_norm = random.uniform(0.15, 0.85)
                y_norm = random.uniform(0.15, 0.85)
                # Check minimum distance from other enemies (at least 0.2 normalized units)
                too_close = False
                for sx, sy in positions:
                    if ((x_norm - sx)**2 + (y_norm - sy)**2)**0.5 < 0.2:
                        too_close = True
                        break
                if not too_close:
                    positions.append((x_norm, y_norm))
                    break
                attempts += 1
            else:
                # Fallback
                x_norm = random.uniform(0.15, 0.85)
                y_norm = random.uniform(0.15, 0.85)
                positions.append((x_norm, y_norm))
        return positions

    def _init_ui(self):
        """Initialize UI elements (exit button, location name, service buttons)."""
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

        # Service buttons (bottom-left, matching global map positions)
        # Inventory button
        inv_btn = Image(
            source=os.path.join(BUTTONS_DIR, 'inventory.png'),
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.01, 'y': 0.01}
        )
        self.layout.add_widget(inv_btn)
        self._btn_inventory = inv_btn

        # Status button
        status_btn = Image(
            source=os.path.join(BUTTONS_DIR, 'status.png'),
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.12, 'y': 0.01}
        )
        self.layout.add_widget(status_btn)
        self._btn_status = status_btn

        # Companions button
        comp_btn = Image(
            source=os.path.join(BUTTONS_DIR, 'companion.png'),
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.23, 'y': 0.01}
        )
        self.layout.add_widget(comp_btn)
        self._btn_companions = comp_btn

        # Quests button
        quests_btn = Image(
            source=os.path.join(BUTTONS_DIR, 'active_quests.png'),
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.34, 'y': 0.01}
        )
        self.layout.add_widget(quests_btn)
        self._btn_quests = quests_btn

    def _open_inventory(self, *args):
        """Open inventory screen."""
        app = App.get_running_app()
        if getattr(app, 'inventory_screen', None):
            try:
                app.inventory_screen.update_inventory()
            except Exception:
                pass
        if getattr(app, 'game', None) and getattr(app.game, 'player', None):
            try:
                self.manager.current = 'inventory'
            except Exception:
                pass

    def _open_status(self, *args):
        """Open status screen."""
        app = App.get_running_app()
        if getattr(app, 'status_screen', None):
            try:
                app.status_screen.update_status()
            except Exception:
                pass
        if getattr(app, 'game', None) and getattr(app.game, 'player', None):
            try:
                self.manager.current = 'status'
            except Exception:
                pass

    def _open_companions(self, *args):
        """Open companions management screen."""
        app = App.get_running_app()
        if getattr(app, 'companion_management_screen', None):
            try:
                app.companion_management_screen.update_companion()
            except Exception:
                pass
        if getattr(app, 'game', None) and getattr(app.game, 'player', None):
            try:
                self.manager.current = 'companion_management'
            except Exception:
                pass

    def _open_quests(self, *args):
        """Open active quests screen."""
        app = App.get_running_app()
        if getattr(app, 'active_quests_screen', None):
            try:
                app.active_quests_screen.update_quests()
            except Exception:
                pass
        if getattr(app, 'game', None) and getattr(app.game, 'player', None):
            try:
                self.manager.current = 'active_quests'
            except Exception:
                pass

    def on_touch_down(self, touch):
        """Handle touch/click events for player movement and UI buttons."""
        # Check if touch hit the exit button
        if self._btn_exit:
            btn_x, btn_y = self._btn_exit.pos
            btn_w, btn_h = self._btn_exit.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                print(f"[DEBUG] Touch hit exit button at ({touch.x}, {touch.y})")
                self._on_exit_location()
                return True

        # Check if touch hit the inventory button
        if self._btn_inventory:
            btn_x, btn_y = self._btn_inventory.pos
            btn_w, btn_h = self._btn_inventory.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                self._open_inventory()
                return True

        # Check if touch hit the status button
        if self._btn_status:
            btn_x, btn_y = self._btn_status.pos
            btn_w, btn_h = self._btn_status.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                self._open_status()
                return True

        # Check if touch hit the companions button
        if self._btn_companions:
            btn_x, btn_y = self._btn_companions.pos
            btn_w, btn_h = self._btn_companions.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                self._open_companions()
                return True

        # Check if touch hit the quests button
        if self._btn_quests:
            btn_x, btn_y = self._btn_quests.pos
            btn_w, btn_h = self._btn_quests.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                self._open_quests()
                return True

        # Check if touch hit the enter cave button
        if self.btn_enter_cave and self.btn_enter_cave.opacity > 0:
            btn_x, btn_y = self.btn_enter_cave.pos
            btn_w, btn_h = self.btn_enter_cave.size
            if btn_x <= touch.x <= btn_x + btn_w and btn_y <= touch.y <= btn_y + btn_h:
                self._enter_cave()
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
        
        # Update enemy positions (enemies slowly move towards player)
        self._update_enemy_positions(dt)

        # Check collisions with enemies
        self._check_enemy_collisions()

        # Draw game state
        self._draw_game()

    def _update_enemy_positions(self, dt):
        """Update enemy positions to slowly move towards player."""
        enemy_speed = dp(30) * dt  # Slower than player speed (dp(200))

        for enemy in self._enemies:
            if enemy['defeated'] or enemy.get('type') == 'zone':
                continue

            # Calculate direction to player
            dx = self._player_pos[0] - enemy['x']
            dy = self._player_pos[1] - enemy['y']
            distance = (dx**2 + dy**2) ** 0.5

            if distance > 0:
                # Move towards player
                move_dist = min(enemy_speed, distance)
                enemy['x'] += (dx / distance) * move_dist
                enemy['y'] += (dy / distance) * move_dist

                # Update normalized coordinates
                enemy['x_norm'] = enemy['x'] / self.width
                enemy['y_norm'] = enemy['y'] / self.height

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

            if enemy.get('type') == 'zone':
                # Zone proximity check
                if distance < enemy['radius']:
                    self.btn_enter_cave.opacity = 1
                    self.btn_enter_cave.pos = (enemy['x'] - self.btn_enter_cave.width / 2, enemy['y'] + enemy['radius'] + 10)
                    print(f"[DEBUG] Cave button shown at pos {self.btn_enter_cave.pos}")
                else:
                    self.btn_enter_cave.opacity = 0
            elif distance < player_radius + enemy['radius']:
                print(f"[DEBUG] Collision with enemy {enemy['id']}!")
                self._start_battle_with_enemy(enemy)
                return

    def _start_battle_with_enemy(self, enemy):
        """Start a battle with the given enemy."""
        print(f"[DEBUG] Starting battle with enemy {enemy['id']}")
        self._current_enemy = enemy
        self._returning_from_battle = True

        # Save current enemy positions and creatures before battle
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player:
            enemy_positions = []
            enemy_creatures = []
            for e in self._enemies:
                if e.get('type') == 'enemy' and not e['defeated']:
                    enemy_positions.append((e['x_norm'], e['y_norm']))
                    enemy_creatures.append(e['creature'])
            if enemy_positions:
                if not hasattr(player, 'last_enemy_positions'):
                    player.last_enemy_positions = {}
                player.last_enemy_positions[self.location_id] = enemy_positions
                if not hasattr(player, 'last_enemy_creatures'):
                    player.last_enemy_creatures = {}
                player.last_enemy_creatures[self.location_id] = enemy_creatures
                print(f"[DEBUG] Saved {len(enemy_positions)} current enemy positions and creatures before battle")

        # Stop the game loop
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

        # Start battle immediately using the pre-generated enemy
        if not app.game or not app.game.player:
            return

        player = app.game.player
        enemy_creature = enemy.get('creature')
        if not enemy_creature:
            print(f"[ERROR] No creature for enemy {enemy['id']}")
            return

        try:
            from systems.battle import Battlefield
            battlefield = Battlefield(player, [enemy_creature])

            # Mark that we're in a battle from local location
            app._battle_from_local_location = True
            app.battle_screen.from_local_location = True

            # Start the battle
            app.battle_screen.start_battle(battlefield, enemy_creature.name)
            self.manager.current = 'battle'
        except Exception as e:
            print(f"[ERROR] Failed to start battle: {e}")
            import traceback
            traceback.print_exc()

    def on_leave(self):
        """Cleanup when leaving screen."""
        # Save current position before leaving
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and self.location_id:
            x_norm = self._player_pos[0] / self.width if self.width else 0.5
            y_norm = self._player_pos[1] / self.height if self.height else 0.5
            player.last_location_pos[self.location_id] = (x_norm, y_norm)
            print(f"[DEBUG] Saved position for {self.location_id}: ({x_norm:.3f}, {y_norm:.3f})")

            # Save enemy positions
            enemy_positions = []
            for enemy in self._enemies:
                if enemy.get('type') == 'enemy' and not enemy['defeated']:
                    enemy_positions.append((enemy['x_norm'], enemy['y_norm']))
            if enemy_positions:
                if not hasattr(player, 'last_enemy_positions'):
                    player.last_enemy_positions = {}
                player.last_enemy_positions[self.location_id] = enemy_positions
                print(f"[DEBUG] Saved {len(enemy_positions)} enemy positions for {self.location_id}")

        # Hide cave button
        self.btn_enter_cave.opacity = 0
        # Hide tooltip
        self._hover_widget.opacity = 0
        # Remove player label
        if self._player_label:
            try:
                self.layout.remove_widget(self._player_label)
            except Exception:
                pass
            self._player_label = None
        # Unbind mouse position
        from kivy.core.window import Window
        try:
            Window.unbind(mouse_pos=self._on_mouse_pos)
        except Exception:
            pass

    def on_return_from_battle(self):
        """Called when returning from a battle."""
        print(f"[DEBUG] on_return_from_battle called for {self._current_enemy}")
        app = App.get_running_app()
        player = app.game.player if app.game else None

        if self._current_enemy:
            if self._current_enemy.get('type') == 'boss':
                # Check if boss was defeated
                print(f"[DEBUG] Checking boss defeat: battle_result exists: {hasattr(app, 'battle_result')}, victory: {app.battle_result.victory if hasattr(app, 'battle_result') and app.battle_result else 'N/A'}")
                if player and hasattr(app, 'battle_result') and app.battle_result and app.battle_result.victory:
                    print(f"[DEBUG] Boss {self._current_enemy['id']} defeated! defeated_bosses before: {player.defeated_bosses}")
                    player.defeated_bosses.add(self._current_enemy['id'])
                    print(f"[DEBUG] defeated_bosses after: {player.defeated_bosses}")
                    # Remove the zone from enemies list
                    self._enemies = [e for e in self._enemies if not (e.get('type') == 'zone' and e.get('id') == self._current_enemy['id'])]
                    # Hide the button
                    self.btn_enter_cave.opacity = 0
                    # Save game to persist defeated bosses
                    try:
                        from systems.save_system import save_game
                        save_game(player, 'autosave')
                        print("[DEBUG] Game auto-saved after boss defeat")
                    except Exception as e:
                        print(f"[ERROR] Failed to save after boss defeat: {e}")
            else:
                # Regular enemy defeat
                self._current_enemy['defeated'] = True
                self._defeated_enemies.add(self._current_enemy['id'])
            self._current_enemy = None

        # Update saved positions to current positions of remaining enemies
        if player:
            enemy_positions = []
            for enemy in self._enemies:
                if enemy.get('type') == 'enemy' and not enemy['defeated']:
                    enemy_positions.append((enemy['x_norm'], enemy['y_norm']))
            if enemy_positions:
                if not hasattr(player, 'last_enemy_positions'):
                    player.last_enemy_positions = {}
                player.last_enemy_positions[self.location_id] = enemy_positions
                print(f"[DEBUG] Updated saved enemy positions after battle return")

        # Resume game loop
        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1/60)

    def _on_mouse_pos(self, window, pos):
        """Handle mouse position for enemy tooltips."""
        # Convert to local coordinates
        local_pos = self.to_local(*pos)

        # Check enemies
        for enemy in self._enemies:
            dx = local_pos[0] - enemy['x']
            dy = local_pos[1] - enemy['y']
            distance = (dx**2 + dy**2) ** 0.5
            if distance <= enemy['radius']:
                if enemy.get('type') == 'enemy':
                    tooltip = f"{enemy['name']} (Lv.{enemy['level']})"
                elif enemy.get('type') == 'zone':
                    tooltip = enemy.get('description', 'Специальная зона')
                else:
                    tooltip = enemy.get('name', 'Неизвестный')
                self._hover_widget.text = tooltip
                self._hover_widget.opacity = 1
                self._hover_widget.pos = (local_pos[0] + dp(10), local_pos[1] + dp(10))
                return

        # Hide tooltip if not hovering over anything
        self._hover_widget.opacity = 0

    def _enter_cave(self, instance=None):
        """Enter the cave and start boss battle."""
        print(f"[DEBUG] Enter cave pressed")
        from systems.battle import EnemyGenerator, Battlefield
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label

        app = App.get_running_app()
        if not app.game or not app.game.player:
            return

        player = app.game.player
        boss_id = 'forest_cave'

        # Check if boss already defeated
        if boss_id in player.defeated_bosses:
            popup = Popup(
                title='Пещера исследована',
                content=Label(text='Вы уже победили Безумного мародера!\nЭта пещера больше не представляет угрозы.'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return

        boss = EnemyGenerator.generate_boss("enemy_ancient_cave_berserker")
        if boss:
            battlefield = Battlefield(app.game.player, [boss])

            # Mark that we're in a battle from local location
            app._battle_from_local_location = True
            app.battle_screen.from_local_location = True

            app.battle_screen.start_battle(battlefield, "Безумный мародер")
            self._current_enemy = {'type': 'boss', 'id': boss_id}
            self.manager.current = 'battle'

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
                
                if enemy.get('type') == 'zone':
                    # Draw zone circle (blue)
                    Color(0, 0, 1, 0.5)
                    Ellipse(
                        pos=(enemy['x'] - enemy['radius'], enemy['y'] - enemy['radius']),
                        size=(enemy['radius'] * 2, enemy['radius'] * 2)
                    )
                    Color(0, 0, 0.8, 1)
                    Line(circle=(enemy['x'], enemy['y'], enemy['radius']), width=2)
                else:
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

            # Update player name label position
            if self._player_label:
                label_x = self._player_pos[0] - self._player_label.width / 2
                label_y = self._player_pos[1] + player_radius + dp(5)
                self._player_label.pos = (label_x, label_y)

    def _on_exit_location(self, *args):
        """Exit the local location and return to global map."""
        print("[DEBUG] Exiting local location")

        app = App.get_running_app()
        app.return_to_local_location = False

        # Stop the update loop
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        
        # Save current position before exiting
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player:
            x_norm = self._player_pos[0] / self.width if self.width else 0.5
            y_norm = self._player_pos[1] / self.height if self.height else 0.5
            player.last_location_pos[self.location_id] = (x_norm, y_norm)

        # Clear state
        self.location_id = None
        self._enemies = []
        self._current_enemy = None
        self._target_pos = None

        # Clear last visited location and enemy data
        if player:
            player.last_location_visited = None
            if hasattr(player, 'last_enemy_positions'):
                player.last_enemy_positions.pop(self.location_id, None)
            if hasattr(player, 'last_enemy_creatures'):
                player.last_enemy_creatures.pop(self.location_id, None)
        
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
