from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
import random


class LocalLocationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.location_id = None
        self.location_name = None
        self._defeated_enemies = set()
        self._player_pos_norm = [0.5, 0.1]  # normalized player position
        self._player_pos = [0, 0]  # actual pixel position
        self._target_pos = None
        self._enemies = []
        self._current_enemy = None
        self._update_event = None
        self.layout = FloatLayout()
        self.add_widget(self.layout)
        # Bind to size changes to update positions
        self.bind(size=self._on_size_changed)

    def _on_size_changed(self, instance, value):
        """Update positions when screen size changes."""
        self._update_positions()
        self._update_enemy_positions()

    def _update_positions(self):
        """Update actual positions from normalized coordinates."""
        self._player_pos = [
            self.width * self._player_pos_norm[0],
            self.height * self._player_pos_norm[1]
        ]

    def _update_enemy_positions(self):
        """Update enemy positions based on current screen size."""
        for enemy in self._enemies:
            norm_x, norm_y = enemy.get('norm_pos', (0, 0))
            enemy['x'] = self.width * norm_x
            enemy['y'] = self.height * norm_y

    def on_enter(self):
        print(f"[DEBUG] on_enter: location_id={self.location_id}")
        self.layout.clear_widgets()
        bg_path = f"assets/backgrounds/locations/{self.location_id}/"
        bg_path += f"{self.location_id}_map.png"
        try:
            bg = Image(source=bg_path, allow_stretch=True, keep_ratio=False,
                       size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            self.layout.add_widget(bg)
        except Exception as e:
            print(f"[ERROR] Failed to load background: {e}")
        self._target_pos = None
        self._enemies = []
        self._current_enemy = None
        # Whether to draw the player circle. Hidden while in battle.
        self._player_visible = True
        self._player_pos_norm = [0.5, 0.5]
        self._update_positions()
        self._init_enemies()
        self._update_positions()
        self._update_enemy_positions()
        self._init_ui()
        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self.on_update, 1/60)
    
    def _init_enemies(self):
        print("[DEBUG] _init_enemies called")
        count = 3
        for i in range(count):
            while True:
                x = random.uniform(0.1, 0.9)
                y = random.uniform(0.1, 0.9)
                if (x - 0.5)**2 + (y - 0.5)**2 > 0.1**2:
                    break
            enemy_data = {
                'id': i,
                'norm_pos': (x, y),
                'radius': dp(15),
                'defeated': False
            }
            self._enemies.append(enemy_data)
    
    def _init_ui(self):
        print("[DEBUG] _init_ui called")
        btn_exit = Button(text='Выход', size_hint=(0.15, 0.08),
                          pos_hint={'right': 0.98, 'top': 0.98})
        btn_exit.bind(on_press=self.on_exit_location)
        self.layout.add_widget(btn_exit)
        lbl_name = Label(text=self.location_name or 'Локация',
                         size_hint=(0.3, 0.08),
                         pos_hint={'x': 0.02, 'top': 0.98},
                         font_size='18sp')
        self.layout.add_widget(lbl_name)
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        self._target_pos = list(touch.pos)
        print("[DEBUG] on_touch_down")
        return True
    
    def on_update(self, dt):
        if not self.location_id:
            return
        if self._target_pos:
            dx = self._target_pos[0] - self._player_pos[0]
            dy = self._target_pos[1] - self._player_pos[1]
            distance = (dx**2 + dy**2)**0.5
            if distance < dp(5):
                self._target_pos = None
            else:
                speed = dp(147) * dt
                if distance > 0:
                    self._player_pos[0] += (dx / distance) * speed
                    self._player_pos[1] += (dy / distance) * speed
                    # Update normalized position
                    if self.width > 0 and self.height > 0:
                        self._player_pos_norm[0] = (
                            self._player_pos[0] / self.width
                        )
                        self._player_pos_norm[1] = (
                            self._player_pos[1] / self.height
                        )
        self._check_enemy_collisions()
        self._draw_game()
    
    def _check_enemy_collisions(self):
        if self.width == 0 or self.height == 0:
            return
        player_radius = dp(10)
        for enemy in self._enemies:
            if enemy['defeated']:
                continue
            dx = self._player_pos[0] - enemy['x']
            dy = self._player_pos[1] - enemy['y']
            distance = (dx**2 + dy**2)**0.5
            if distance < player_radius + enemy['radius']:
                self._start_battle_with_enemy(enemy)
                break
    
    def _start_battle_with_enemy(self, enemy):
        print(f"[DEBUG] Battle with enemy {enemy['id']}")
        self._current_enemy = enemy
        app = App.get_running_app()
        player = app.game.player

        # Generate actual enemy creature
        from systems.battle import EnemyGenerator, Battlefield
        enemies = EnemyGenerator.generate_for_location(
            self.location_id, player.level, count=1
        )
        if not enemies:
            print(f"[ERROR] No enemies generated for {self.location_id}")
            return

        # Create battlefield with the generated enemy
        battlefield = Battlefield(player, enemies)

        app._battle_from_local_location = True
        app.battle_screen.from_local_location = True
        # hide player marker so it doesn't overlap battle UI
        self._player_visible = False
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

        # Start the battle
        app.battle_screen.start_battle(battlefield, enemies[0].name)
        self.manager.current = 'battle'
    
    def _mark_enemy_defeated(self, enemy_id):
        for enemy in self._enemies:
            if enemy['id'] == enemy_id:
                enemy['defeated'] = True
                self._defeated_enemies.add(enemy_id)
                break
    
    def on_return_from_battle(self):
        print("[DEBUG] Return from battle")
        if self._current_enemy:
            self._mark_enemy_defeated(self._current_enemy['id'])
            self._current_enemy = None
        if self._update_event:
            self._update_event.cancel()
        # restore player visibility and resume updates
        self._player_visible = True
        self._player_pos_norm = [0.5, 0.5]
        self._update_positions()
        self._update_event = Clock.schedule_interval(self.on_update, 1/60)
    
    def _draw_game(self):
        self.layout.canvas.after.clear()
        with self.layout.canvas.after:
            for enemy in self._enemies:
                # skip defeated enemies entirely so they disappear from the map
                defeated = enemy.get('defeated')
                if defeated or 'x' not in enemy or 'y' not in enemy:
                    continue
                Color(1, 0, 0, 0.7)
                Ellipse(pos=(enemy['x'] - enemy['radius'],
                             enemy['y'] - enemy['radius']),
                        size=(enemy['radius'] * 2, enemy['radius'] * 2))
                Color(0.8, 0, 0, 1)
                Line(circle=(enemy['x'], enemy['y'], enemy['radius']), width=2)
            player_radius = dp(10)
            if getattr(self, '_player_visible', True):
                Color(1, 1, 0, 0.8)
                Ellipse(pos=(self._player_pos[0] - player_radius,
                             self._player_pos[1] - player_radius),
                        size=(player_radius * 2, player_radius * 2))
                Color(1, 0.8, 0, 1)
                Line(circle=(self._player_pos[0], self._player_pos[1],
                             player_radius), width=2)
    
    def on_exit_location(self, *args):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        self.location_id = None
        # Restore global map player marker to entry point
        try:
            app = App.get_running_app()
            if self._entry_map_norm and app.location_select_screen:
                nx, ny = self._entry_map_norm
                lss = app.location_select_screen
                if lss._player_marker and lss.map_overlay:
                    pm = lss._player_marker
                    w = max(1, lss.map_overlay.width)
                    h = max(1, lss.map_overlay.height)
                    px = int(w * nx - pm.width / 2)
                    py = int(h * ny - pm.height / 2)
                    pm.pos = (px, py)
        except Exception:
            pass
        self.manager.current = 'location_select'
