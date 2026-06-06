#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран выбора локации на карте региона."""

import os
import random

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp

from ui.ui_styles import COLORS, BUTTONS_DIR
from data.locations import LocationManager
from data.local_scenes import COMBAT_SCENES, enter_local_scene, resolve_global_map_background
from ui.widgets.cover_background import cover_background_image
from ui.widgets.danger_bar import DangerBar
from ui.bindings.keyboard_handler import KeyboardHandler


class LocationSelectScreen(Screen, KeyboardHandler):
    """Экран выбора локации с информацией."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location = None
        self.location_manager = None
        self.game = None
        # Player marker on the global map (widget that moves)
        self._player_marker = None
        self._destination = None
        self._move_ev = None
        self._move_speed = dp(147)  # pixels per second (1.5x slower than 220)
        self._enter_btn = None
        self._kb_move = {"up": False, "down": False, "left": False, "right": False}
        self._kb_move_ev = None
        self.bind_keyboard()
        # positions on the map (normalized 0..1) for location hotspots
        self._map_positions = {
            # NOTE: normalized coordinates (0..1) in map_overlay space,
            # where (0,0) is bottom-left and (1,1) is top-right.
            'city': (0.19, 0.85),
            'forest': (0.18, 0.45),
            'swamp': (0.50, 0.60),
            'village': (0.73, 0.52),  # placeholder "в разработке"
            'mines': (0.70, 0.20),
            'mountains': (0.70, 0.90),
        }

        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(8),
            spacing=dp(8)
        )

        # Фон
        with main_layout.canvas.before:
            Color(0.12, 0.14, 0.16, 1)
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )

        # Заголовок
        title_label = Label(
            text='🗺️ Карта региона',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(48),
            color=(0.95, 0.85, 0.6, 1),
            bold=True
        )
        main_layout.add_widget(title_label)

        # Map container with background image and overlay for small buttons
        self.map_container = FloatLayout(size_hint=(1, 0.82))
        map_src = resolve_global_map_background() or ""
        self.map_image = cover_background_image(map_src) if map_src else Widget(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.map_container.add_widget(self.map_image)

        # overlay for interactive small buttons
        self.map_overlay = FloatLayout(size_hint=(1, 1))
        self.map_container.add_widget(self.map_overlay)

        # Debug label to confirm map is visible (can be removed later)
        debug_lbl = Label(
            text='КАРТА',
            size_hint=(None, None),
            pos_hint={'x': 0.02, 'y': 0.92},
            color=(1, 1, 1, 0.9),
            bold=True
        )
        self.map_overlay.add_widget(debug_lbl)

        main_layout.add_widget(self.map_container)

        # bottom controls removed (status button relocated to map overlay)
        self.add_widget(main_layout)

    def _start_kb_move(self):
        if getattr(self, "_kb_move_ev", None):
            return
        self._kb_move_ev = Clock.schedule_interval(self._kb_move_tick, 1.0 / 60.0)

    def _stop_kb_move(self):
        if getattr(self, "_kb_move_ev", None):
            try:
                self._kb_move_ev.cancel()
            except Exception:
                pass
            self._kb_move_ev = None

    def _kb_move_tick(self, dt):
        if not getattr(self, "_player_marker", None) or not getattr(self, "map_overlay", None):
            self._stop_kb_move()
            return

        mx = (1 if self._kb_move["right"] else 0) - (1 if self._kb_move["left"] else 0)
        my = (1 if self._kb_move["up"] else 0) - (1 if self._kb_move["down"] else 0)
        if not (mx or my):
            self._stop_kb_move()
            return

        if getattr(self, "_destination", None):
            self._destination = None
            self._stop_moving()

        try:
            app = App.get_running_app()
            if getattr(app, "game", None) and getattr(app.game, "danger_manager", None):
                ambush = app.game.danger_manager.update(dt, app.game.location_manager)
                if ambush:
                    self._trigger_ambush(ambush)
                    return
        except Exception:
            pass

        length = (mx * mx + my * my) ** 0.5
        if not length:
            return

        speed = dp(220) * dt
        pm = self._player_marker
        nx = pm.pos[0] + (mx / length) * speed
        ny = pm.pos[1] + (my / length) * speed

        nx = max(0, min(nx, max(0, self.map_overlay.width - pm.width)))
        ny = max(0, min(ny, max(0, self.map_overlay.height - pm.height)))
        pm.pos = (nx, ny)

        if getattr(self, "_player_label", None):
            try:
                cx = nx + pm.size[0] / 2
                cy = ny + pm.size[1] / 2
                player_label = self._player_label
                label_x = cx - player_label.size[0] / 2
                label_y = cy + pm.size[1] + dp(5)
                player_label.pos = (label_x, label_y)
            except Exception:
                pass

        self._update_enter_button()

    def _nearest_hotspot(self):
        try:
            if not getattr(self, "_player_marker", None):
                return None, None
            pm = self._player_marker
            cx = pm.pos[0] + pm.size[0] / 2
            cy = pm.pos[1] + pm.size[1] / 2
            nearest = None
            nearest_dist = None
            for btn in getattr(self, "_hotspot_buttons", []):
                try:
                    bx = btn.pos[0] + btn.size[0] / 2
                    by = btn.pos[1] + btn.size[1] / 2
                    d = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
                    if nearest is None or d < nearest_dist:
                        nearest = btn
                        nearest_dist = d
                except Exception:
                    continue
            return nearest, nearest_dist
        except Exception:
            return None, None

    def _move_to_nearest_hotspot(self):
        nearest, _dist = self._nearest_hotspot()
        if not nearest:
            return False
        try:
            bx = nearest.pos[0] + nearest.size[0] / 2
            by = nearest.pos[1] + nearest.size[1] / 2
            self._destination = (bx, by)
            self._start_moving()
            return True
        except Exception:
            return False

    def _exit_to_menu(self):
        app = App.get_running_app()
        try:
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                app.game.autosave()
        except Exception:
            pass
        try:
            if getattr(app, "hud", None):
                try:
                    app.hud.unbind_player()
                except Exception:
                    app.hud.opacity = 0
        except Exception:
            pass
        self.manager.current = "main_menu"

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action == "move_up":
            self._kb_move["up"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_down":
            self._kb_move["down"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_left":
            self._kb_move["left"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_right":
            self._kb_move["right"] = pressed
            (self._start_kb_move() if pressed else None)
            return True

        if action == "enter_location" and pressed:
            eb = getattr(self, "_enter_btn", None)
            if eb and getattr(eb, "opacity", 0) > 0.5:
                loc_id = getattr(eb, "_target_loc_id", None)
                if loc_id:
                    self.on_select_location(loc_id)
                    return True
            return bool(self._move_to_nearest_hotspot())

        if action == "open_inventory" and pressed:
            from ui.widgets.navigation_buttons import prepare_inventory_navigation
            app = App.get_running_app()
            prepare_inventory_navigation("location_select")
            if getattr(app, "inventory_screen", None):
                try:
                    app.inventory_screen.update_inventory()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "inventory"
            return True

        if action == "open_status" and pressed:
            app = App.get_running_app()
            if getattr(app, "status_screen", None):
                try:
                    app.status_screen.update_status()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "status"
            return True

        if action == "open_companions" and pressed:
            app = App.get_running_app()
            if getattr(app, "companion_management_screen", None):
                try:
                    app.companion_management_screen.update_companion()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "companion_management"
            return True

        if action == "open_quests" and pressed:
            app = App.get_running_app()
            if getattr(app, "active_quests_screen", None):
                try:
                    app.active_quests_screen.update_quests()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "active_quests"
            return True

        if action == "open_menu" and pressed:
            self._exit_to_menu()
            return True

        if action == "open_save" and pressed:
            app = App.get_running_app()
            try:
                if getattr(app, "game", None) and getattr(app.game, "player", None):
                    app.game.autosave()
            except Exception:
                pass
            return True

        if action == "exit_location" and pressed:
            self._exit_to_menu()
            return True

        return False
    
    def update_locations(self):
        """Обновление списка локаций."""
        app = App.get_running_app()
        self.game = app.game
        pass
        # Use shared LocationManager from game when available
        self.location_manager = self.game.location_manager if (self.game and getattr(self.game, 'location_manager', None)) else LocationManager()
        # Render small translucent hotspots over the map image
        # Clear previous overlay widgets
        try:
            pass
            # Clear previous widgets and hotspot markers (canvas.before instructions)
            self.map_overlay.clear_widgets()
            try:
                if getattr(self, '_hotspot_markers', None):
                    for entry in list(self._hotspot_markers):
                        try:
                            btn, col, ell = entry
                        except Exception:
                            try:
                                col, ell = entry
                                btn = None
                            except Exception:
                                continue
                        try:
                            if ell in self.map_overlay.canvas.before:
                                self.map_overlay.canvas.before.remove(ell)
                        except Exception:
                            pass
                        try:
                            if col in self.map_overlay.canvas.before:
                                self.map_overlay.canvas.before.remove(col)
                        except Exception:
                            pass
                    self._hotspot_markers = []
            except Exception:
                pass
        except Exception:
            pass
            # If map_overlay isn't present (older UI), fall back to list behavior
            try:
                self.locations_layout.clear_widgets()
            except Exception:
                pass
            for loc_id, location in self.location_manager.locations.items():
                btn_text = self._get_location_text(location)
                btn = Button(
                    text=btn_text,
                    size_hint_y=None,
                    height=dp(80),
                    font_size=dp(15),
                    background_color=(
                        (0.48, 0.35, 0.22, 1) if not location.is_locked
                        else (0.55, 0.28, 0.20, 1)
                    )
                )
                if not location.is_locked:
                    btn.bind(on_press=lambda b, lid=loc_id: self.on_select_location(lid))
                else:
                    btn.bind(on_press=lambda b, loc=location: self.on_locked_location(loc))
                self.locations_layout.add_widget(btn)
            return

        pass

        # Track visible hotspots for hover detection
        self._hotspot_buttons = []
        if not getattr(self, '_hotspot_markers', None):
            self._hotspot_markers = []

        for loc_id, location in self.location_manager.locations.items():
            pos = self._map_positions.get(loc_id)
            if not pos:
                continue
            x, y = pos
            # Invisible large hotspot button (acts like a big area to click)
            # Allow per-location adjustments: move or resize specific hotspots
            size_dp = dp(120)
            adj_x = x
            adj_y = y
            # forest: lower and twice bigger
            if loc_id == 'forest':
                size_dp = dp(120) * 2
                adj_y = max(0.05, y - 0.08)
            # swamp: twice bigger
            elif loc_id == 'swamp':
                size_dp = dp(120) * 2
            # mines: move right and twice bigger
            elif loc_id == 'mines':
                size_dp = dp(120) * 2
                adj_x = min(0.95, x + 0.06)
            # mountains: slightly left and twice bigger
            elif loc_id == 'mountains':
                size_dp = dp(120) * 2
                adj_x = max(0.05, x - 0.05)
            btn = Button(
                text='',
                size_hint=(None, None),
                size=(size_dp, size_dp),
                pos_hint={'center_x': adj_x, 'center_y': adj_y},
                background_normal='',
                background_down='',
                background_color=(0, 0, 0, 0)
            )
            # store metadata for tooltip
            btn._loc_id = loc_id
            btn._loc_name = getattr(location, 'name', loc_id)
            self._hotspot_buttons.append(btn)

            # Create a faint circular marker behind the hotspot (canvas.before)
            try:
                from kivy.graphics import Color, Ellipse
                col = Color(0.35, 0.22, 0.10, 0.16)
                ell = Ellipse(pos=(0, 0), size=(size_dp, size_dp))
                # add to canvas.before so it appears under widgets
                self.map_overlay.canvas.before.add(col)
                self.map_overlay.canvas.before.add(ell)
                self._hotspot_markers.append((btn, col, ell))

                def _update_marker(*args):
                    try:
                        ell.pos = btn.pos
                        ell.size = btn.size
                    except Exception:
                        pass

                btn.bind(pos=_update_marker, size=_update_marker)
                # trigger initial placement after layout; small delay
                Clock.schedule_once(lambda dt: _update_marker(), 0.05)
            except Exception:
                pass

            # Do NOT bind hotspot buttons to clicks — entrance should occur
            # only when the player marker reaches the hotspot and the
            # enter-button appears. Hotspots remain visible for hover
            # and proximity checks but don't handle touch events.
            # (They are still added to the overlay so hover/proximity works.)
            self.map_overlay.add_widget(btn)

        # Add an invisible hotspot for the city so player can click the city area
        try:
            city_pos = self._map_positions.get('city') 
            cx, cy = city_pos
            # city: lower and twice bigger
            size_dp = dp(120) * 2
            adj_cx = cx
            adj_cy = max(0.05, cy - 0.08)
            city_btn = Button(
                text='',
                size_hint=(None, None),
                size=(size_dp, size_dp),
                pos_hint={'center_x': adj_cx, 'center_y': adj_cy},
                background_normal='',
                background_down='',
                background_color=(0, 0, 0, 0)
            )
            city_btn._loc_id = 'city'
            city_btn._loc_name = 'Город'

            # City entry should also be triggered by the player marker
            # (showing the enter button) rather than direct clicks, so do
            # not bind a click handler here. Add the widget so proximity
            # detection and tooltip still work.
            self._hotspot_buttons.append(city_btn)
            self.map_overlay.add_widget(city_btn)
            
            # Add faint circular marker behind the city hotspot (after widget is added)
            try:
                from kivy.graphics import Color, Ellipse
                col = Color(0.35, 0.22, 0.10, 0.16)
                ell = Ellipse(pos=city_btn.pos, size=city_btn.size)
                self.map_overlay.canvas.before.add(col)
                self.map_overlay.canvas.before.add(ell)
                self._hotspot_markers.append((city_btn, col, ell))

                def _update_city_marker(btn, *args):
                    try:
                        ell.pos = btn.pos
                        ell.size = btn.size
                    except Exception:
                        pass

                # Bind with the button as first argument to avoid stale closure
                city_btn.bind(pos=lambda inst, val: _update_city_marker(city_btn),
                              size=lambda inst, val: _update_city_marker(city_btn))
                Clock.schedule_once(lambda dt: _update_city_marker(city_btn), 0.05)
            except Exception as e:
                pass
        except Exception:
            pass

        # Add a hotspot for the new village drawing (placeholder screen/text).
        try:
            v_pos = self._map_positions.get('village')
            if v_pos:
                vx, vy = v_pos
                size_dp = dp(120) * 2
                village_btn = Button(
                    text='',
                    size_hint=(None, None),
                    size=(size_dp, size_dp),
                    pos_hint={'center_x': vx, 'center_y': vy},
                    background_normal='',
                    background_down='',
                    background_color=(0, 0, 0, 0)
                )
                village_btn._loc_id = 'village'
                village_btn._loc_name = 'Деревня'
                self._hotspot_buttons.append(village_btn)
                self.map_overlay.add_widget(village_btn)

                # Add faint circular marker behind the village hotspot
                try:
                    from kivy.graphics import Color, Ellipse
                    col = Color(0.35, 0.22, 0.10, 0.16)
                    ell = Ellipse(pos=village_btn.pos, size=village_btn.size)
                    self.map_overlay.canvas.before.add(col)
                    self.map_overlay.canvas.before.add(ell)
                    self._hotspot_markers.append((village_btn, col, ell))

                    def _update_village_marker(btn, *args):
                        try:
                            ell.pos = btn.pos
                            ell.size = btn.size
                        except Exception:
                            pass

                    village_btn.bind(
                        pos=lambda inst, val: _update_village_marker(village_btn),
                        size=lambda inst, val: _update_village_marker(village_btn),
                    )
                    Clock.schedule_once(lambda dt: _update_village_marker(village_btn), 0.05)
                except Exception:
                    pass
        except Exception:
            pass

        # Create hover tooltip widget (once) and bind mouse movement
        if not hasattr(self, '_hover_widget'):
            hw = BoxLayout(size_hint=(None, None), size=(dp(180), dp(40)))
            with hw.canvas.before:
                Color(0.12, 0.07, 0.03, 0.9)
                hw._rect = Rectangle(pos=hw.pos, size=hw.size)
            lbl = Label(text='', halign='center', valign='middle', color=(1, 1, 1, 1))
            lbl.text_size = (hw.width, hw.height)
            hw.add_widget(lbl)
            hw.label = lbl
            hw.opacity = 0
            self.map_overlay.add_widget(hw)
            hw.bind(pos=lambda inst, val: setattr(hw._rect, 'pos', val))
            hw.bind(size=lambda inst, val: setattr(hw._rect, 'size', val))
            self._hover_widget = hw

        # bind mouse position for hover only once
        try:
            from kivy.core.window import Window
            if not getattr(self, '_mouse_bound', False):
                Window.bind(mouse_pos=self._on_mouse_pos)
                self._mouse_bound = True
        except Exception:
            pass
        # Bind map clicks to move player marker
        try:
            if not getattr(self, '_map_touch_bound', False):
                try:
                    self.map_overlay.bind(on_touch_down=self._on_map_touch)
                except Exception:
                    pass
                self._map_touch_bound = True
        except Exception:
            pass
        # ensure markers are refreshed when overlay resizes
        try:
            def _refresh_all_markers(*args):
                try:
                    if not getattr(self, '_hotspot_markers', None):
                        return
                    for entry in self._hotspot_markers:
                        try:
                            btn, col, ell = entry
                        except Exception:
                            continue
                        try:
                            ell.pos = btn.pos
                            ell.size = btn.size
                        except Exception:
                            pass
                except Exception:
                    pass

            self.map_overlay.bind(size=_refresh_all_markers, pos=_refresh_all_markers)
            Clock.schedule_once(lambda dt: _refresh_all_markers(), 0.1)
        except Exception:
            pass

        # Create player marker if missing: a more visible circle on the road below the city
        try:
            if not getattr(self, '_player_marker', None):
                # Make the marker 2x smaller: dp(20) instead of dp(40)
                size_px = dp(20)
                # Start on the road below the city (0.28, 0.75 instead of 0.28, 0.9)
                city_pos = (0.25, 0.60)
                cx, cy = city_pos
                adj_cx = cx
                adj_cy = cy
                pm = Widget(size_hint=(None, None), size=(size_px, size_px))
                # draw circular representation (two concentric ellipses: outline + fill)
                from kivy.graphics import Color, Ellipse
                with pm.canvas:
                    # outline (thin, semi-dark) so the marker is visible on any background
                    Color(0.12, 0.08, 0.03, 1)
                    pm._outline = Ellipse(pos=(pm.x - dp(2), pm.y - dp(2)), size=(pm.width + dp(4), pm.height + dp(4)))
                    # fill (bright yellow-green)
                    Color(1.0, 0.85, 0.05, 1)
                    pm._ell = Ellipse(pos=pm.pos, size=pm.size)
                # keep ellipses synced and place marker explicitly based on overlay size
                def _update_pm(*args):
                    try:
                        pm._ell.pos = pm.pos
                        pm._ell.size = pm.size
                        pm._outline.pos = (pm.x - dp(2), pm.y - dp(2))
                        pm._outline.size = (pm.width + dp(4), pm.height + dp(4))
                    except Exception:
                        pass
                pm.bind(pos=_update_pm, size=_update_pm)
                self.map_overlay.add_widget(pm)
                self._player_marker = pm

                # place the player marker explicitly (convert normalized coords to pixels)
                def _place_pm(dt=None):
                    try:
                        w = max(1, self.map_overlay.width)
                        h = max(1, self.map_overlay.height)
                        x = int(w * adj_cx - pm.width / 2)
                        y = int(h * adj_cy - pm.height / 2)
                        pm.pos = (x, y)
                        _update_pm()
                    except Exception:
                        pass

                # initial placement after layout and on resize
                Clock.schedule_once(_place_pm, 0.06)
                self.map_overlay.bind(size=lambda i, v: _place_pm())
        except Exception:
            pass

        # --- Danger Bar (шкала глобальной опасности) ---
        def _place_danger_bar(dt=None):
            """Позиционирование danger bar."""
            try:
                ow = self.map_overlay.width
                oh = self.map_overlay.height
                db = self._danger_bar
                if not db or db.width <= 0 or db.height <= 0:
                    return
                x = int(ow * 0.82) - db.width
                y = oh - db.height - dp(8)
                db.pos = (max(dp(4), x), max(dp(4), y))
            except Exception:
                pass

        try:
            if not getattr(self, '_danger_bar', None) or self._danger_bar.parent is None:
                if getattr(self, '_danger_bar', None):
                    self._danger_bar.cleanup()
                danger_bar = DangerBar()
                self.map_overlay.add_widget(danger_bar)
                self._danger_bar = danger_bar
                Clock.schedule_once(_place_danger_bar, 0.12)
                self.map_overlay.bind(size=lambda i, v: _place_danger_bar())
            else:
                try:
                    self.map_overlay.remove_widget(self._danger_bar)
                except Exception:
                    pass
                self.map_overlay.add_widget(self._danger_bar)
        except Exception:
            pass

        # Exit to main menu button (top-right corner)
        def _exit_to_menu(*args):
            app = App.get_running_app()
            # Save the game before exiting to menu
            try:
                if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                    app.game.autosave()
            except Exception as e:
                pass
            # Hide HUD then return to main menu
            try:
                if getattr(app, 'hud', None):
                    try:
                        app.hud.unbind_player()
                    except Exception:
                        app.hud.opacity = 0
            except Exception:
                pass
            self.manager.current = 'main_menu'

        exit_menu_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            pos_hint={'right': 0.98, 'top': 0.98},
            background_normal=os.path.join(BUTTONS_DIR, 'menu.png'),
            background_down=os.path.join(BUTTONS_DIR, 'menu.png'),
            background_color=(1, 1, 1, 1)
        )
        exit_menu_btn.bind(on_press=_exit_to_menu)
        self.map_overlay.add_widget(exit_menu_btn)

        # Inventory quick-access button on the map (bottom-right)
        def _open_inventory(*args):
            from ui.widgets.navigation_buttons import prepare_inventory_navigation

            app = App.get_running_app()
            prepare_inventory_navigation('location_select')
            if getattr(app, 'inventory_screen', None):
                try:
                    app.inventory_screen.update_inventory()
                except Exception:
                    pass
            # only open if game/player exists
            if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                try:
                    self.manager.current = 'inventory'
                except Exception:
                    pass

        # Move inventory to left-bottom (standardized size, horizontal stack)
        inv_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.01, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'inventory.png'),
            background_down=os.path.join(BUTTONS_DIR, 'inventory.png'),
            background_color=(1, 1, 1, 1)
        )
        inv_btn.bind(on_press=_open_inventory)
        self.map_overlay.add_widget(inv_btn)

        # Status button to the right of inventory (left-bottom horizontal stack)
        def _open_status(*args):
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

        status_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.12, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'status.png'),
            background_down=os.path.join(BUTTONS_DIR, 'status.png'),
            background_color=(1, 1, 1, 1)
        )
        status_btn.bind(on_press=_open_status)
        self.map_overlay.add_widget(status_btn)

        # Companions management button (left-bottom horizontal stack)
        def _open_companions(*args):
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

        comp_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.23, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'companion.png'),
            background_down=os.path.join(BUTTONS_DIR, 'companion.png'),
            background_color=(1, 1, 1, 1)
        )
        comp_btn.bind(on_press=_open_companions)
        self.map_overlay.add_widget(comp_btn)

        # Active quests button (left-bottom horizontal stack)
        def _open_active_quests(*args):
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

        quests_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.34, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'active_quests.png'),
            background_down=os.path.join(BUTTONS_DIR, 'active_quests.png'),
            background_color=(1, 1, 1, 1)
        )
        quests_btn.bind(on_press=_open_active_quests)
        self.map_overlay.add_widget(quests_btn)
        # Ensure player marker is above these controls so it's always visible
        try:
            if getattr(self, '_player_marker', None):
                try:
                    # remove and re-add to bring to top of widget stack
                    try:
                        self.map_overlay.remove_widget(self._player_marker)
                    except Exception:
                        pass
                    self.map_overlay.add_widget(self._player_marker)
                except Exception:
                    pass
        except Exception:
            pass
    
    def _get_location_text(self, location):
        """Получить текст кнопки локации."""
        lock_icon = '🔐' if location.is_locked else '🔓'
        difficulty = {
            'forest': '⭐ Лёгкая',
            'swamp': '⭐⭐ Средняя',
            'mines': '⭐⭐⭐ Сложная',
            'mountains': '⭐⭐⭐⭐ Очень сложная',
            'ancient': '⭐⭐⭐⭐⭐ Экстрем'
        }.get(location.id, 'Неизвестная')
        
        text = f"{lock_icon} {location.name}\n{difficulty}"
        
        if location.is_locked and location.unlock_condition:
            text += f"\n⚠️ {location.unlock_condition}"
        else:
            text += f"\n✅ Враги: {len(location.enemy_types)}"
        
        return text

    def _on_mouse_pos(self, window, pos):
        """Handle global mouse movement to show hover tooltip for hotspots.

        `pos` is window coordinates (x, y).
        """
        try:
            if not getattr(self, 'map_overlay', None) or not getattr(self, '_hotspot_buttons', None):
                return
            
            found = None
            mouse_x, mouse_y = pos
            
            # Debug: log first call with info about hotspot buttons
            if not getattr(self, '_debug_logged_mouse', False):
                print(f"[DEBUG _on_mouse_pos] _hotspot_buttons count: {len(self._hotspot_buttons)}")
                for i, btn in enumerate(self._hotspot_buttons):
                    print(f"  [{i}] {btn._loc_id}: pos={btn.pos}, size={btn.size}")
                self._debug_logged_mouse = True
            
            # Check collision in screen/window space directly
            for btn in self._hotspot_buttons:
                try:
                    # Get button's bounding box in window/screen coordinates
                    btn_x = btn.pos[0]
                    btn_y = btn.pos[1]
                    btn_right = btn_x + btn.size[0]
                    btn_top = btn_y + btn.size[1]
                    
                    # Check if mouse is within button bounds
                    if btn_x <= mouse_x <= btn_right and btn_y <= mouse_y <= btn_top:
                        found = btn
                        break
                except Exception as e:
                    continue

            if found and getattr(self, '_hover_widget', None):
                hw = self._hover_widget
                try:
                    pass
                    hw.label.text = found._loc_name
                except Exception:
                    hw.label.text = str(found._loc_id)
                # Position tooltip slightly above the mouse cursor (window coords)
                try:
                    from kivy.core.window import Window
                    # Use window mouse coords so tooltip can be reparented to root and remain visible
                    x = mouse_x - hw.width / 2
                    y = mouse_y + dp(10)
                    # Clamp to window/root bounds
                    try:
                        root = App.get_running_app().root
                        max_x = max(0, root.width - hw.width)
                        max_y = max(0, root.height - hw.height)
                        x = max(0, min(x, max_x))
                        y = max(0, min(y, max_y))
                        # Reparent tooltip to root so it's drawn above HUD and other overlays
                        try:
                            if hw.parent is not root:
                                try:
                                    hw.parent.remove_widget(hw)
                                except Exception:
                                    pass
                                try:
                                    root.add_widget(hw)
                                    pass
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        hw.pos = (x, y)
                    except Exception:
                        # fallback: position relative to map_overlay
                        try:
                            cx = found.pos[0] + found.size[0] / 2
                            cy = found.pos[1] + found.size[1] / 2
                            x = cx - hw.width / 2
                            y = cy + dp(10)
                            parent = self.map_overlay
                            max_x = max(0, parent.width - hw.width)
                            x = max(0, min(x, max_x))
                            max_y = max(0, parent.height - hw.height)
                            y = max(0, min(y, max_y))
                            hw.pos = (x, y)
                        except Exception:
                            pass
                except Exception:
                    pass
                hw.opacity = 1
            else:
                try:
                    if getattr(self, '_hover_widget', None):
                        self._hover_widget.opacity = 0
                except Exception:
                    pass
        except Exception as e:
            pass

    # --- Movement & map interaction for player marker ---
    def _on_map_touch(self, instance, touch):
        """Handle clicks/touches on the map overlay to set destination."""
        try:
            if not getattr(self, 'map_overlay', None):
                return False
            # Only react to left mouse button or simple touch
            tb = getattr(touch, 'button', None)
            if tb and tb != 'left':
                return False
            # Convert touch pos (window coords) to map_overlay local coordinates
            # so movement and marker positioning use the same coordinate space.
            try:
                local = self.map_overlay.to_widget(touch.x, touch.y)
                local_x, local_y = local[0], local[1]
                # If the click landed on an interactive child (buttons, hotspots, etc.),
                # don't treat it as a map-move — allow the child to handle the event.
                try:
                    for child in list(self.map_overlay.children):
                        # ignore the player marker and hover widget when checking
                        if child is getattr(self, '_player_marker', None) or child is getattr(self, '_hover_widget', None):
                            continue
                        # ignore hotspot widgets (they should not block map-move clicks)
                        # hotspot buttons carry a `_loc_id` attribute
                        try:
                            if hasattr(child, '_loc_id'):
                                continue
                        except Exception:
                            pass
                        try:
                            if child.collide_point(local_x, local_y):
                                return False
                        except Exception:
                            continue
                except Exception:
                    pass
                self._destination = (local_x, local_y)
            except Exception:
                # fallback: use raw window coords if conversion fails
                self._destination = touch.pos
            # start movement loop
            pass
            self._start_moving()
            return True
        except Exception:
            return False

    def _start_moving(self):
        try:
            if getattr(self, '_move_ev', None):
                return
            pass
            self._move_ev = Clock.schedule_interval(self._move_player, 1.0 / 60.0)
        except Exception:
            pass

    def _stop_moving(self):
        try:
            if getattr(self, '_move_ev', None):
                self._move_ev.cancel()
                self._move_ev = None
        except Exception:
            pass

    def _move_player(self, dt):
        """Move the player marker towards destination each frame."""
        try:
            if not getattr(self, '_player_marker', None) or not getattr(self, '_destination', None):
                self._stop_moving()
                return
            # --- Global Danger: update while moving ---
            try:
                app = App.get_running_app()
                if (getattr(app, 'game', None)
                        and getattr(app.game, 'danger_manager', None)):
                    ambush = app.game.danger_manager.update(
                        dt, app.game.location_manager
                    )
                    if ambush:
                        self._stop_moving()
                        self._trigger_ambush(ambush)
                        return
            except Exception:
                pass
            # current center of player marker in window coords
            pm = self._player_marker
            cur_x = pm.pos[0] + pm.size[0] / 2
            cur_y = pm.pos[1] + pm.size[1] / 2
            dest_x, dest_y = self._destination
            dx = dest_x - cur_x
            dy = dest_y - cur_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 4:
                # reached destination
                self._destination = None
                self._stop_moving()
                # update enter button state
                self._update_enter_button()
                return
            # move toward destination
            step = self._move_speed * dt
            if step >= dist:
                nx, ny = dest_x, dest_y
            else:
                nx = cur_x + dx / dist * step
                ny = cur_y + dy / dist * step
            # set marker pos such that center matches nx,ny
            pm.pos = (nx - pm.size[0] / 2, ny - pm.size[1] / 2)
            # Move label with marker - center it above the marker
            if getattr(self, '_player_label', None):
                player_label = self._player_label
                # Center label horizontally above marker center
                label_x = nx - player_label.size[0] / 2
                # Position label above marker
                label_y = ny + pm.size[1] + dp(5)
                player_label.pos = (label_x, label_y)
            # after moving, check proximity to hotspots
            self._update_enter_button()
        except Exception:
            pass

    def _update_enter_button(self):
        """Show enter button if player is near a hotspot, hide otherwise."""
        try:
            if not getattr(self, '_player_marker', None):
                return
            pm = self._player_marker
            cx = pm.pos[0] + pm.size[0] / 2
            cy = pm.pos[1] + pm.size[1] / 2
            nearest = None
            nearest_dist = 1e9
            # Find the truly nearest hotspot without duplication
            for btn in getattr(self, '_hotspot_buttons', []):
                try:
                    bx = btn.pos[0] + btn.size[0] / 2
                    by = btn.pos[1] + btn.size[1] / 2
                    d = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
                    if d < nearest_dist:
                        nearest_dist = d
                        nearest = btn
                except Exception:
                    continue
            # threshold: within 42 pixels + half hotspot smaller dimension
            show = False
            loc_id = None
            if nearest:
                radius = min(nearest.size[0], nearest.size[1]) / 2
                if nearest_dist <= max(42, radius * 0.6):
                    show = True
                    loc_id = getattr(nearest, '_loc_id', None)
            if show:
                # create or reuse enter button
                if not getattr(self, '_enter_btn', None):
                    eb = Button(text='Войти', size_hint=(None, None), size=(dp(92), dp(40)))
                    def _enter(b):
                        try:
                            # Get loc_id from button's property, not from closure
                            entered_loc = getattr(b, '_target_loc_id', 'city')
                            self.on_select_location(entered_loc)
                        except Exception:
                            pass
                    eb.bind(on_press=_enter)
                    self._enter_btn = eb
                    # add to root so it's above other UI
                    try:
                        root = App.get_running_app().root
                        root.add_widget(eb)
                    except Exception:
                        try:
                            self.map_overlay.add_widget(eb)
                        except Exception:
                            pass
                # Update button's target location and position
                try:
                    eb = self._enter_btn
                    # Store current loc_id in button so callback uses correct location
                    eb._target_loc_id = loc_id
                    win = App.get_running_app().root
                    ex = cx - eb.width / 2
                    ey = cy - pm.size[1] / 2 - eb.height - dp(6)
                    ex = max(0, min(ex, max(0, win.width - eb.width)))
                    ey = max(0, min(ey, max(0, win.height - eb.height)))
                    eb.pos = (ex, ey)
                    eb.opacity = 1
                except Exception:
                    pass
            else:
                if getattr(self, '_enter_btn', None):
                    try:
                        self._enter_btn.opacity = 0
                    except Exception:
                        pass
        except Exception:
            pass
    
    def on_select_location(self, loc_id):
        """Выбор локации для входа."""
        app = App.get_running_app()
        # only allow entering if game/player initialized
        if not getattr(app, 'game', None) or not getattr(app.game, 'player', None):
            popup = Popup(
                title='Ошибка',
                content=Label(text='Игра не инициализирована!'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return

        # Check if location is available (not locked)
        try:
            location_mgr = app.game.location_manager
            if not location_mgr.is_location_available(loc_id):
                location = location_mgr.get_location(loc_id)
                unlock_msg = location.unlock_description() if location else "Локация заблокирована"
                popup = Popup(
                    title='Локация закрыта',
                    content=Label(text=unlock_msg),
                    size_hint=(0.7, 0.3)
                )
                popup.open()
                return
        except Exception as e:
            print(f"[DEBUG] Error checking location availability: {e}")
            pass

        # Проходимые локальные карты: бой, город и подлокации
        if loc_id in COMBAT_SCENES or loc_id == 'city':
            screen = getattr(app, 'local_location_screen', None)
            if not screen:
                return
            if loc_id in COMBAT_SCENES:
                screen._defeated_enemies = set()
                screen._returning_from_battle = False
            if enter_local_scene(app, loc_id):
                return
            popup = Popup(
                title='Ошибка',
                content=Label(text='Не удалось открыть локацию.'),
                size_hint=(0.6, 0.3),
            )
            popup.open()
            return

        if loc_id == 'ancient_cave':
            popup = Popup(
                title='Пещера Древних',
                content=Label(
                    text='Боссы теперь обитают в своих локациях:\n'
                         'лес, болота, шахты и горы.',
                    halign='center',
                ),
                size_hint=(0.7, 0.35),
            )
            popup.open()
            return

        if loc_id == 'village':
            popup = Popup(
                title='Деревня',
                content=Label(text='в разработке', halign='center'),
                size_hint=(0.6, 0.28),
            )
            popup.open()
            return
    
    def on_status(self, instance):
        """Открыть статус."""
        self.manager.current = 'status'

    def on_enter(self):
        """Обновить карту при входе на экран."""
        # Ensure hotspots are up-to-date when entering the screen
        try:
            self.update_locations()
        except Exception:
            pass
        
        # Update/create player name label when entering the map screen
        try:
            if hasattr(self, 'map_overlay') and hasattr(self, '_player_marker'):
                app = App.get_running_app()
                if app.game and app.game.player:
                    # Remove old label if exists
                    if hasattr(self, '_player_label') and self._player_label:
                        try:
                            self.map_overlay.remove_widget(self._player_label)
                        except Exception:
                            pass
                    
                    # Create new label with player name
                    player_name = app.game.player.name
                    player_label = Label(
                        text=player_name,
                        size_hint=(None, None),
                        size=(dp(100), dp(25)),
                        font_size=dp(14),
                        color=COLORS['gold'],
                        bold=True
                    )
                    self.map_overlay.add_widget(player_label)
                    self._player_label = player_label
                    
                    # Position it above the player marker, centered horizontally
                    pm = self._player_marker
                    # Get marker center coordinates
                    marker_center_x = pm.x + pm.width / 2
                    marker_top_y = pm.y + pm.height
                    # Position label centered above marker
                    label_x = marker_center_x - player_label.width / 2
                    label_y = marker_top_y + dp(5)
                    player_label.pos = (label_x, label_y)
        except Exception as e:
            print(f"[ERROR] Failed to create player label: {e}")
        
        # Re-bind mouse_pos to our handler (safe to unbind first)
        try:
            from kivy.core.window import Window
            try:
                Window.unbind(mouse_pos=self._on_mouse_pos)
            except Exception:
                pass
            try:
                Window.bind(mouse_pos=self._on_mouse_pos)
            except Exception:
                pass
        except Exception:
            pass

    def on_leave(self):
        """Cleanup when leaving screen: hide tooltip, unbind mouse handler, remove enter button."""
        # Clean up danger bar
        try:
            if getattr(self, '_danger_bar', None):
                self._danger_bar.cleanup()
                try:
                    self.map_overlay.remove_widget(self._danger_bar)
                except Exception:
                    pass
                self._danger_bar = None
        except Exception:
            pass
        try:
            if getattr(self, '_hover_widget', None):
                try:
                    self._hover_widget.opacity = 0
                except Exception:
                    pass
        except Exception:
            pass
        try:
            from kivy.core.window import Window
            try:
                Window.unbind(mouse_pos=self._on_mouse_pos)
            except Exception:
                pass
        except Exception:
            pass
        # Remove enter button from root so it doesn't appear on other screens
        try:
            if getattr(self, '_enter_btn', None):
                root = App.get_running_app().root
                if self._enter_btn in root.children:
                    root.remove_widget(self._enter_btn)
                self._enter_btn = None
        except Exception:
            pass

    def _trigger_ambush(self, enemy_id):
        """Начать бой при засаде (danger = 100%) с предупреждением."""
        try:
            app = App.get_running_app()
            if not app.game or not app.game.player:
                return
            # Создать врага из EnemyDatabase
            from data.enemies import EnemyDatabase
            enemy = EnemyDatabase.create(enemy_id)
            if not enemy:
                return

            enemy_name = getattr(enemy, 'name', enemy_id)

            def _start_ambush_battle(*args):
                try:
                    battlefield, battle_service = app.game.create_battle([enemy])
                    if hasattr(app, 'battle_screen'):
                        app.battle_screen.start_battle(battlefield, battle_service)
                        app.root.current = 'battle'
                except Exception as e:
                    print(f"[AMBUSH] Battle start error: {e}")

            # Показать предупреждение перед боем
            popup = Popup(
                title='⚠️ ЗАСАДА!',
                content=Label(
                    text=(
                        f'Опасность достигла максимума!\n\n'
                        f'На вас нападает: {enemy_name}!\n\n'
                        f'🔴 Глобальная опасность: '
                        f'{app.game.danger_manager.danger_level:.0f}%'
                    ),
                    text_size=(None, None),
                    halign='center',
                    valign='middle',
                    font_size=dp(18),
                    color=(0.9, 0.3, 0.2, 1),
                ),
                size_hint=(0.7, 0.4),
            )
            popup.open()
            Clock.schedule_once(
                lambda dt: (popup.dismiss(), _start_ambush_battle()),
                1.8,
            )
        except Exception as e:
            print(f"[AMBUSH] Error: {e}")

    def on_locked_location(self, location):
        """Показать требования для разблокировки локации."""
        if not location.unlock_condition:
            condition_text = "Эта локация пока недоступна."
        else:
            condition_text = f"Требования для разблокировки:\n{location.unlock_condition}"

        popup = Popup(
            title=f'🔒 {location.name}',
            content=Label(
                text=condition_text,
                text_size=(None, None),
                halign='center',
                valign='middle',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4)
        )
        popup.open()
