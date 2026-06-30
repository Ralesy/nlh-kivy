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
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Translate, Scale, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.logger import Logger

from ui.ui_styles import COLORS, BUTTONS_DIR
from data.locations import LocationManager
from data.local_scenes import enter_local_scene, resolve_global_map_background
from ui.widgets.cover_background import cover_background_image
from ui.widgets.danger_bar import DangerBar
from ui.bindings.keyboard_handler import KeyboardHandler
from systems.roaming_entity_manager import RoamingEntityManager
from systems.stealth_controller import StealthController, StealthMode, DetectionLevel
from ui.widgets.encounter_dialog import EncounterDialog

from core.config import (
    GLOBAL_CAMERA_ZOOM,
    GLOBAL_CAMERA_LERP_SPEED,
    GLOBAL_MAP_SPEED_MULTIPLIER,
    GLOBAL_PLAYER_MARKER_SIZE,
    GLOBAL_PLAYER_MOVE_SPEED,
    ENEMY_BARKS,
    ENEMY_ALERT_BARKS,
    BARK_CHANCE_PER_CHECK,
    BARK_CHECK_INTERVAL,
    BARK_DURATION,
)


class LocationSelectScreen(Screen, KeyboardHandler):
    """Экран выбора локации с информацией."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location = None
        self.location_manager = None
        self.game = None

        # --- Camera constants ---
        # --- Camera constants ---
        self.CAMERA_ZOOM = GLOBAL_CAMERA_ZOOM
        self.CAMERA_LERP_SPEED = GLOBAL_CAMERA_LERP_SPEED
        self.GLOBAL_MAP_SPEED_MULTIPLIER = GLOBAL_MAP_SPEED_MULTIPLIER
        self.PLAYER_MARKER_SIZE = dp(GLOBAL_PLAYER_MARKER_SIZE)


        # --- Camera state (world pixel coords) ---
        self._cam_x = 0.0
        self._cam_y = 0.0
        self._cam_target_x = 0.0
        self._cam_target_y = 0.0

        # Player world position (pixels within map_overlay)
        self._player_world_x = 0.0
        self._player_world_y = 0.0

        # Player marker on the global map (widget that moves)
        self._player_marker = None
        self._destination = None
        self._move_ev = None
        self._move_speed = dp(GLOBAL_PLAYER_MOVE_SPEED)
        self._enter_btn = None
        self._kb_move = {"up": False, "down": False, "left": False, "right": False}
        self._kb_move_ev = None

        self.roaming_manager = RoamingEntityManager()
        self.stealth_controller = StealthController()
        self._token_update_ev = None
        self._token_graphics_inited = False
        self._stealth_indicator = None
        self._noise_circle = None
        self._encounter_active = False
        self._encounter_cooldown = 0.0

        self.bind_keyboard()

        # positions on the map (normalized 0..1) for location hotspots
        self._map_positions = {
            'city': (0.19, 0.85),
            'village': (0.73, 0.52),
        }

        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(8),
            spacing=dp(8)
        )

        with main_layout.canvas.before:
            Color(0.12, 0.14, 0.16, 1)
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )

        title_label = Label(
            text='🗺️ Карта региона',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(48),
            color=(0.95, 0.85, 0.6, 1),
            bold=True
        )
        main_layout.add_widget(title_label)

        # --- Map container (viewport) ---
        self.map_container = FloatLayout(size_hint=(1, 0.82))

        # World layer zoomed/panned via canvas transform
        self.map_world = FloatLayout(size_hint=(1, 1))
        with self.map_world.canvas.before:
            PushMatrix()
            self._cam_translate = Translate()
            self._cam_scale = Scale()
        with self.map_world.canvas.after:
            PopMatrix()

        map_src = resolve_global_map_background() or ""
        self.map_image = cover_background_image(map_src) if map_src else Widget(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.map_world.add_widget(self.map_image)

        self.map_overlay = FloatLayout(size_hint=(1, 1))
        self.map_world.add_widget(self.map_overlay)

        self.map_container.add_widget(self.map_world)

        main_layout.add_widget(self.map_container)

        self.add_widget(main_layout)

        # Start camera update loop
        self._cam_ev = Clock.schedule_interval(self._camera_update, 1.0 / 60.0)

    # --- Camera ---

    def _screen_to_world(self, sx, sy):
        """Convert screen coordinates (relative to map_container) to world coordinates."""
        cw = max(1, self.map_container.width)
        ch = max(1, self.map_container.height)
        wx = (sx - cw / 2) / self.CAMERA_ZOOM + self._cam_x
        wy = (sy - ch / 2) / self.CAMERA_ZOOM + self._cam_y
        return wx, wy

    def _world_to_screen(self, wx, wy):
        """Convert world coordinates to screen coordinates (relative to map_container)."""
        cw = max(1, self.map_container.width)
        ch = max(1, self.map_container.height)
        sx = (wx - self._cam_x) * self.CAMERA_ZOOM + cw / 2
        sy = (wy - self._cam_y) * self.CAMERA_ZOOM + ch / 2
        return sx, sy

    def _camera_update(self, dt):
        """LERP camera toward target, update canvas transform."""
        lerp_factor = 1.0 - 2.71828 ** (-self.CAMERA_LERP_SPEED * dt)
        self._cam_x += (self._cam_target_x - self._cam_x) * lerp_factor
        self._cam_y += (self._cam_target_y - self._cam_y) * lerp_factor

        cw = max(1, self.map_container.width)
        ch = max(1, self.map_container.height)

        self._cam_scale.x = self.CAMERA_ZOOM
        self._cam_scale.y = self.CAMERA_ZOOM
        self._cam_translate.x = cw / 2 - self._cam_x * self.CAMERA_ZOOM
        self._cam_translate.y = ch / 2 - self._cam_y * self.CAMERA_ZOOM

    # --- Keyboard movement ---

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
        if self._encounter_active:
            self._stop_kb_move()
            return
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
        except Exception as e:
            Logger.error(f"GlobalMap: DangerManager update failed. Error: {e}")

        length = (mx * mx + my * my) ** 0.5
        if not length:
            return

        ow = max(1, self.map_overlay.width)
        oh = max(1, self.map_overlay.height)
        speed = self._move_speed * self.GLOBAL_MAP_SPEED_MULTIPLIER * dt * self.stealth_controller.speed_multiplier
        pm_size = self.PLAYER_MARKER_SIZE

        nx = self._player_world_x + (mx / length) * speed
        ny = self._player_world_y + (my / length) * speed
        nx = max(pm_size / 2, min(nx, ow - pm_size / 2))
        ny = max(pm_size / 2, min(ny, oh - pm_size / 2))
        self._player_world_x = nx
        self._player_world_y = ny

        self._cam_target_x = nx
        self._cam_target_y = ny

        self._sync_marker_screen_pos()
        self._update_enter_button()

    # --- Hotspot helpers ---

    def _nearest_hotspot(self):
        try:
            if not getattr(self, "_player_marker", None):
                return None, None
            cx = self._player_world_x
            cy = self._player_world_y
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
            if self._encounter_active:
                return True
            self._kb_move["up"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_down":
            if self._encounter_active:
                return True
            self._kb_move["down"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_left":
            if self._encounter_active:
                return True
            self._kb_move["left"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_right":
            if self._encounter_active:
                return True
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
            from ui.inventory_popup import InventoryPopup
            app = App.get_running_app()
            player = app.game.player if app.game else None
            if not player:
                return True
            def on_close():
                popup.dismiss()
            inv_content = InventoryPopup(player, on_done=on_close)
            popup = Popup(
                title='',
                content=inv_content,
                size_hint=(0.35, 0.85),
                pos_hint={'x': 0.02, 'y': 0.07},
                auto_dismiss=True,
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
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

        if action == "toggle_sneak" and pressed:
            if self.stealth_controller.mode == StealthMode.STEALTH:
                self.stealth_controller.set_mode(StealthMode.NORMAL)
            else:
                self.stealth_controller.set_mode(StealthMode.STEALTH)
            self._update_camera_zoom()
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
        self.location_manager = self.game.location_manager if (self.game and getattr(self.game, 'location_manager', None)) else LocationManager()
        self.roaming_manager._location_manager = self.location_manager

        try:
            pass
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
                            except Exception as e:
                                Logger.debug(f"GlobalMap: Unpacking hotspot tuple failed (expected fallback): {e}")
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

        self._hotspot_buttons = []
        if not getattr(self, '_hotspot_markers', None):
            self._hotspot_markers = []

        for loc_id, location in self.location_manager.locations.items():
            pos = self._map_positions.get(loc_id)
            if not pos:
                continue
            x, y = pos
            size_dp = dp(120)
            btn = Button(
                text='',
                size_hint=(None, None),
                size=(size_dp, size_dp),
                pos_hint={'center_x': x, 'center_y': y},
                background_normal='',
                background_down='',
                background_color=(0, 0, 0, 0)
            )
            btn._loc_id = loc_id
            btn._loc_name = getattr(location, 'name', loc_id)
            self._hotspot_buttons.append(btn)

            try:
                from kivy.graphics import Color, Ellipse
                col = Color(0.35, 0.22, 0.10, 0.02)
                ell = Ellipse(pos=(0, 0), size=(size_dp, size_dp))
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
                Clock.schedule_once(lambda dt: _update_marker(), 0.05)
            except Exception:
                pass

            self.map_overlay.add_widget(btn)

        try:
            city_pos = self._map_positions.get('city')
            cx, cy = city_pos
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

            self._hotspot_buttons.append(city_btn)
            self.map_overlay.add_widget(city_btn)

            try:
                from kivy.graphics import Color, Ellipse
                col = Color(0.35, 0.22, 0.10, 0.02)
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

                city_btn.bind(pos=lambda inst, val: _update_city_marker(city_btn),
                              size=lambda inst, val: _update_city_marker(city_btn))
                Clock.schedule_once(lambda dt: _update_city_marker(city_btn), 0.05)
            except Exception as e:
                pass
        except Exception:
            pass

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

                try:
                    from kivy.graphics import Color, Ellipse
                    col = Color(0.35, 0.22, 0.10, 0.02)
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

        # Hover tooltip widget
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

        try:
            from kivy.core.window import Window
            if not getattr(self, '_mouse_bound', False):
                Window.bind(mouse_pos=self._on_mouse_pos)
                self._mouse_bound = True
        except Exception:
            pass

        try:
            if not getattr(self, '_map_touch_bound', False):
                try:
                    self.map_overlay.bind(on_touch_down=self._on_map_touch)
                except Exception:
                    pass
                self._map_touch_bound = True
        except Exception:
            pass

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

        # Create player marker
        try:
            if not getattr(self, '_player_marker', None):
                size_px = self.PLAYER_MARKER_SIZE
                start_world_x = 0.25
                start_world_y = 0.60
                adj_cx = start_world_x
                adj_cy = start_world_y
                pm = Widget(size_hint=(None, None), size=(size_px, size_px))
                from kivy.graphics import Color, Ellipse
                with pm.canvas:
                    Color(0.12, 0.08, 0.03, 1)
                    pm._outline = Ellipse(pos=(pm.x - dp(2), pm.y - dp(2)), size=(pm.width + dp(4), pm.height + dp(4)))
                    Color(1.0, 0.85, 0.05, 1)
                    pm._ell = Ellipse(pos=pm.pos, size=pm.size)

                def _update_pm(*args):
                    try:
                        pm._ell.pos = pm.pos
                        pm._ell.size = pm.size
                        pm._outline.pos = (pm.x - dp(2), pm.y - dp(2))
                        pm._outline.size = (pm.width + dp(4), pm.height + dp(4))
                    except Exception:
                        pass
                pm.bind(pos=_update_pm, size=_update_pm)

                # Add player marker to map_container (screen-space, outside camera transform)
                self.map_container.add_widget(pm)
                self._player_marker = pm

                def _place_pm(dt=None):
                    try:
                        if getattr(self, '_position_set', False):
                            return
                        w = max(1, self.map_overlay.width)
                        h = max(1, self.map_overlay.height)
                        self._player_world_x = float(w * 0.25)
                        self._player_world_y = float(h * 0.60)
                        self._cam_target_x = self._player_world_x
                        self._cam_target_y = self._player_world_y
                        self._cam_x = self._player_world_x
                        self._cam_y = self._player_world_y
                        sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
                        pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
                        _update_pm()
                        self._position_set = True
                    except Exception:
                        pass

                Clock.schedule_once(_place_pm, 0.06)
                self.map_overlay.bind(size=self._reposition_marker_on_resize)
        except Exception:
            pass

        # Danger Bar
# Danger Bar (Индикатор опасности)
        def _place_danger_bar(dt=None):
            try:
                # Теперь считаем размеры от стабильного ЭКРАНА (self), а не от карты
                ow = self.width
                oh = self.height
                db = self._danger_bar
                if not db:
                    return
                
                # Принудительно отключаем автоматическое растягивание Kivy
                db.size_hint = (None, None)
                
                # Если размеры сбросились до дефолтных 100x100, задаем пропорции HUD
                if db.width == 100 or db.width <= 0:
                    db.width = dp(240)
                if db.height == 100 or db.height <= 0:
                    db.height = dp(42)
                
                # ИДЕАЛЬНОЕ ПОЗИЦИОНИРОВАНИЕ В СТАТИЧНЫХ КООРДИНАТАХ:
                # x: Прижимаем вправо с отступом dp(12) — симметрично левому GameHUD
                x = ow - db.width - dp(12)
                
                # y: Выравниваем верхнюю линию полоски тютелька в тютельку с GameHUD.
                # Математически это: Высота_Экрана - Высота_Виджета - Отступ_Сверху(14dp)
                y = oh - db.height - dp(14)
                
                db.pos = (max(dp(12), x), max(dp(12), y))
            except Exception:
                pass

        try:
            if not getattr(self, '_danger_bar', None) or self._danger_bar.parent is None:
                if getattr(self, '_danger_bar', None):
                    self._danger_bar.cleanup()
                danger_bar = DangerBar()
                
                # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Добавляем прямо на экран (self), а не в map_container!
                # Это полностью изолирует HUD от зума, перетаскивания и сдвигов карты.
                self.add_widget(danger_bar)
                self._danger_bar = danger_bar
                
                Clock.schedule_once(_place_danger_bar, 0.12)
                # Перепривязываем отслеживание к изменению размеров самого экрана
                self.bind(size=lambda i, v: _place_danger_bar())
            else:
                try:
                    if self._danger_bar.parent:
                        self._danger_bar.parent.remove_widget(self._danger_bar)
                except Exception:
                    pass
                # Перевыводим на передний план поверх карты
                self.add_widget(self._danger_bar)
                Clock.schedule_once(_place_danger_bar, 0.05)
        except Exception:
            pass

        # Exit to main menu button
        def _exit_to_menu(*args):
            app = App.get_running_app()
            try:
                if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                    app.game.autosave()
            except Exception as e:
                pass
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
        self.map_container.add_widget(exit_menu_btn)

        # Inventory quick-access button
        def _open_inventory(*args):
            from ui.inventory_popup import InventoryPopup

            app = App.get_running_app()
            player = app.game.player if app.game else None
            if not player:
                return

            def on_close():
                popup.dismiss()

            inv_content = InventoryPopup(player, on_done=on_close)
            popup = Popup(
                title='',
                content=inv_content,
                size_hint=(0.35, 0.85),
                pos_hint={'x': 0.02, 'y': 0.07},
                auto_dismiss=True,
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()

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
        self.map_container.add_widget(inv_btn)

        # Status button
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
        self.map_container.add_widget(status_btn)

        # Companions button
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
        self.map_container.add_widget(comp_btn)

        # Quests button
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
        self.map_container.add_widget(quests_btn)

        # Token spawning + graphics deferred to _start_token_updates (called from on_enter)
        # when map_overlay has its final layout size

    def _update_tokens(self, dt):
        try:
            if self._encounter_active:
                self.roaming_manager.update_graphics()
                return

            if self._encounter_cooldown > 0:
                self._encounter_cooldown = max(0.0, self._encounter_cooldown - dt)
                px = self._player_world_x
                py = self._player_world_y
                prev_states = {t.id: t.is_chasing for t in self.roaming_manager.tokens}
                moved = abs(px - self._prev_player_world_x) > 0.5 or abs(py - self._prev_player_world_y) > 0.5 if hasattr(self, '_prev_player_world_x') else False
                is_sneaking = (self.stealth_controller.mode == StealthMode.STEALTH)
                self.roaming_manager.update(dt, px, py, player_is_noisy=(moved and not is_sneaking), is_sneaking=is_sneaking)
                self._detect_new_chasers(prev_states)
                self._update_barks(dt)
                self.roaming_manager.update_graphics()
                self._prev_player_world_x = px
                self._prev_player_world_y = py
                return

            px = self._player_world_x
            py = self._player_world_y

            moved = False
            if hasattr(self, '_prev_player_world_x'):
                dx = abs(px - self._prev_player_world_x)
                dy = abs(py - self._prev_player_world_y)
                moved = dx > 0.5 or dy > 0.5

            is_sneaking = (self.stealth_controller.mode == StealthMode.STEALTH)
            player_is_noisy = moved and not is_sneaking

            prev_states = {t.id: t.is_chasing for t in self.roaming_manager.tokens}

            encounter = self.roaming_manager.update(
                dt,
                px,
                py,
                player_is_noisy=player_is_noisy,
                is_sneaking=is_sneaking,
            )
            if encounter:
                self._encounter_active = True
                self._stop_moving()
                self._stop_kb_move()
                self._show_encounter(encounter)

            self._detect_new_chasers(prev_states)
            self._update_barks(dt)
            self.roaming_manager.update_graphics()

            self._prev_player_world_x = px
            self._prev_player_world_y = py
        except Exception:
            pass

    def _detect_new_chasers(self, prev_states):
        for token in self.roaming_manager.tokens:
            if token.id in self.roaming_manager._lockout_ids:
                continue
            if token.is_chasing and not prev_states.get(token.id, False):
                self._spawn_bark(token, is_alert=True)

    def _destroy_all_token_canvas(self):
        try:
            self.roaming_manager.destroy_graphics()
            self._token_graphics_inited = False
        except Exception:
            pass

    def _get_location_text(self, location):
        """Получить текст кнопки локации."""
        lock_icon = '🔐' if location.is_locked else '🔓'
        text = f"{lock_icon} {location.name}"

        if location.is_locked and location.unlock_condition:
            text += f"\n⚠️ {location.unlock_condition}"
        else:
            text += f"\n✅ Доступна"

        return text

    def _on_mouse_pos(self, window, pos):
        """Handle global mouse movement to show hover tooltip for hotspots."""
        try:
            if not getattr(self, 'map_overlay', None) or not getattr(self, '_hotspot_buttons', None):
                return

            found = None
            mouse_x, mouse_y = pos

            # Convert mouse screen coords to world coords relative to map_container
            try:
                local = self.map_container.to_widget(mouse_x, mouse_y)
                world_x, world_y = self._screen_to_world(local[0], local[1])
            except Exception:
                world_x, world_y = mouse_x, mouse_y

            if not getattr(self, '_debug_logged_mouse', False):
                print(f"[DEBUG _on_mouse_pos] _hotspot_buttons count: {len(self._hotspot_buttons)}")
                self._debug_logged_mouse = True

            # CHECK TOKENS FIRST (priority over hotspots)
            for token in self.roaming_manager.tokens:
                if token.id in self.roaming_manager._lockout_ids:
                    continue
                try:
                    d = ((world_x - token.x) ** 2 + (world_y - token.y) ** 2) ** 0.5
                    if d < 16.0:
                        found = token
                        break
                except Exception:
                    continue

            # Only check hotspots if no token found
            if not found:
                for btn in self._hotspot_buttons:
                    try:
                        btn_x = btn.pos[0]
                        btn_y = btn.pos[1]
                        btn_right = btn_x + btn.size[0]
                        btn_top = btn_y + btn.size[1]

                        if btn_x <= world_x <= btn_right and btn_y <= world_y <= btn_top:
                            found = btn
                            break
                    except Exception:
                        continue

            if found and getattr(self, '_hover_widget', None):
                hw = self._hover_widget
                try:
                    if hasattr(found, '_loc_name'):
                        hw.label.text = found._loc_name
                        hw.label.text_size = (hw.width, hw.height)
                    elif hasattr(found, 'name'):
                        # Show enemy squad/group info instead of location name
                        squad_members = []
                        if hasattr(found, 'squad_id') and found.squad_id:
                            squad_members = [
                                t for t in self.roaming_manager.tokens
                                if t.squad_id == found.squad_id
                                and t.id not in self.roaming_manager._lockout_ids
                            ]

                        if len(squad_members) > 1:
                            # Show squad composition with levels
                            member_lines = [f"  {m.name}" for m in squad_members]
                            lines = "\n".join(member_lines)
                            hw.label.text = f"Отряд ({len(squad_members)}):\n{lines}"
                            hw.label.text_size = (hw.width, None)
                            hw.label.texture_update()
                            new_h = max(dp(40), hw.label.texture_size[1] + dp(16))
                            hw.size = (dp(200), new_h)
                            hw.label.text_size = (hw.width, hw.height)
                        else:
                            # Single token - show only name, no location
                            hw.label.text = found.name
                            hw.label.text_size = (hw.width, hw.height)
                            hw.size = (dp(180), dp(40))
                    else:
                        hw.label.text = str(found._loc_id)
                        hw.label.text_size = (hw.width, hw.height)
                        hw.size = (dp(180), dp(40))
                except Exception:
                    hw.label.text = str(found)
                    hw.label.text_size = (hw.width, hw.height)
                    hw.size = (dp(180), dp(40))
                try:
                    from kivy.core.window import Window
                    x = mouse_x - hw.width / 2
                    y = mouse_y + dp(10)
                    try:
                        root = App.get_running_app().root
                        max_x = max(0, root.width - hw.width)
                        max_y = max(0, root.height - hw.height)
                        x = max(0, min(x, max_x))
                        y = max(0, min(y, max_y))
                        try:
                            if hw.parent is not root:
                                try:
                                    hw.parent.remove_widget(hw)
                                except Exception:
                                    pass
                                try:
                                    root.add_widget(hw)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        hw.pos = (x, y)
                    except Exception:
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
        except Exception:
            pass

    # --- Movement & map interaction for player marker ---

    def _on_map_touch(self, instance, touch):
        """Handle clicks/touches on the map overlay to set destination."""
        try:
            if self._encounter_active:
                return False
            if not getattr(self, 'map_overlay', None):
                return False
            tb = getattr(touch, 'button', None)
            if tb and tb != 'left':
                return False
            try:
                # Convert touch screen coords to world coords
                local = self.map_container.to_widget(touch.x, touch.y)
                world_x, world_y = self._screen_to_world(local[0], local[1])

                try:
                    for child in list(self.map_overlay.children):
                        if child is getattr(self, '_player_marker', None) or child is getattr(self, '_hover_widget', None):
                            continue
                        try:
                            if hasattr(child, '_loc_id'):
                                continue
                        except Exception:
                            pass
                        try:
                            if child.collide_point(world_x, world_y):
                                return False
                        except Exception:
                            continue
                except Exception:
                    pass

                self._destination = (world_x, world_y)
            except Exception:
                self._destination = touch.pos
            self._start_moving()
            return True
        except Exception:
            return False

    def _sync_marker_screen_pos(self):
        """Update player marker's screen position based on world coords and camera."""
        try:
            pm = self._player_marker
            if not pm:
                return
            sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
            pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
            # Update label
            if getattr(self, '_player_label', None):
                player_label = self._player_label
                label_x = sx - player_label.width / 2
                label_y = sy + pm.size[1] + dp(5)
                player_label.pos = (label_x, label_y)
        except Exception:
            pass

    def _reposition_marker_on_resize(self, instance, new_size):
        """Безопасный обработчик ресайза: не меняет мировые координаты,
        только пересчитывает экранную позицию маркера."""
        try:
            pm = self._player_marker
            if not pm:
                return
            sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
            pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
            if getattr(self, '_player_label', None):
                player_label = self._player_label
                label_x = sx - player_label.width / 2
                label_y = sy + pm.size[1] + dp(5)
                player_label.pos = (label_x, label_y)
        except Exception:
            pass

    def _start_moving(self):
        try:
            if getattr(self, '_move_ev', None):
                return
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
            if self._encounter_active:
                self._stop_moving()
                return
            if not getattr(self, '_player_marker', None) or not getattr(self, '_destination', None):
                self._stop_moving()
                return
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

            ow = max(1, self.map_overlay.width)
            oh = max(1, self.map_overlay.height)
            pm_size = self.PLAYER_MARKER_SIZE
            cur_x = self._player_world_x
            cur_y = self._player_world_y
            dest_x, dest_y = self._destination
            dx = dest_x - cur_x
            dy = dest_y - cur_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 4:
                self._destination = None
                self._stop_moving()
                self._update_enter_button()
                return
            step = self._move_speed * self.GLOBAL_MAP_SPEED_MULTIPLIER * dt * self.stealth_controller.speed_multiplier
            if step >= dist:
                self._player_world_x = dest_x
                self._player_world_y = dest_y
            else:
                self._player_world_x = cur_x + dx / dist * step
                self._player_world_y = cur_y + dy / dist * step

            self._player_world_x = max(pm_size / 2, min(self._player_world_x, ow - pm_size / 2))
            self._player_world_y = max(pm_size / 2, min(self._player_world_y, oh - pm_size / 2))

            self._cam_target_x = self._player_world_x
            self._cam_target_y = self._player_world_y

            self._sync_marker_screen_pos()
            self._update_enter_button()
        except Exception:
            pass

    def _check_roaming_collision(self):
        pass

    def _show_encounter(self, encounter_data: dict):
        try:
            dialog = EncounterDialog(encounter_data)
            dialog.set_result_handler(self._on_encounter_result)
            dialog.open()
        except Exception:
            self._encounter_active = False

    def _on_encounter_result(self, action_id: str, encounter_data: dict):
        self._encounter_active = False
        self._encounter_cooldown = 2.0

        group = encounter_data.get("group", [])
        main_token_id = encounter_data.get("token_id", "")

        if action_id == "boss_fight":
            self._start_boss_battle(encounter_data)
        elif action_id == "fight":
            app = App.get_running_app()
            app._pending_ambush_group = list(group)
            self._start_ambush_scene(encounter_data)
        else:
            for member in group:
                self.roaming_manager.reset_token(member.get("token_id", main_token_id), cooldown=10.0)

    def _start_boss_battle(self, encounter_data: dict):
        """Запустить turn-based битву с боссом прямо с глобальной карты."""
        try:
            app = App.get_running_app()
            if not app.game or not app.game.player:
                return

            token_id = encounter_data.get("token_id", "")
            enemy_type = encounter_data.get("enemy_type", "")
            boss_name = encounter_data.get("name", "Босс")

            # Определяем номер босса из token_id (boss_001 → 1)
            boss_num = None
            if token_id.startswith("boss_"):
                try:
                    boss_num = int(token_id.split("_")[1])
                except (IndexError, ValueError):
                    pass

            if not boss_num:
                Logger.error(f"GlobalMap: Unknown boss token: {token_id}")
                return

            from systems.battle import EnemyGenerator
            boss_creature = EnemyGenerator.generate_boss(enemy_type)
            if not boss_creature:
                Logger.error(f"GlobalMap: Failed to generate boss: {enemy_type}")
                return

            # Запоминаем данные босса для обработки после битвы
            app._boss_battle_boss_num = boss_num
            app._boss_battle_token_id = token_id
            app._boss_battle_active = True

            battlefield, _ = app.game.create_battle([boss_creature])
            if hasattr(app, 'battle_screen'):
                app.battle_screen.start_battle(battlefield, f"👑 {boss_name}")
                app.root.current = 'battle'
        except Exception as e:
            import traceback
            traceback.print_exc()
            Logger.error(f"GlobalMap: Boss battle start error: {e}")
            self._encounter_active = False

    def _handle_ambush_return(self):
        """Обработать возврат из засады на глобальной карте.

        Для каждого токена из группы засады:
        - Если соответствующее существо было убито (индекс в _ambush_defeated_set)
          → удаляем токен с глобальной карты навсегда.
        - Если существо выжило → сбрасываем погоню токена (он теряет интерес и уходит).
        """
        app = App.get_running_app()
        pending = getattr(app, "_pending_ambush_group", None)
        if not pending:
            return
        player = app.game.player if app.game else None
        if not player:
            return
        defeated = set(getattr(player, "_ambush_defeated_set", set()))

        for idx, member in enumerate(pending):
            token_id = member.get("token_id", "")
            if not token_id:
                continue
            if idx in defeated:
                self.roaming_manager.remove_token(token_id)
            else:
                self.roaming_manager.reset_token(token_id, cooldown=10.0)

        app._pending_ambush_group = None
        player._ambush_defeated_set = set()

    def _handle_boss_battle_return(self):
        """Обработать возврат из битвы с боссом на глобальной карте.
        
        После победы: токен босса удаляется навсегда (уже отмечен как побеждённый
        в battle.py через location_manager.mark_boss_defeated).
        После поражения: токен босса сбрасывается, игрок телепортируется в город.
        """
        app = App.get_running_app()
        boss_num = getattr(app, "_boss_battle_boss_num", None)
        token_id = getattr(app, "_boss_battle_token_id", None)
        if not boss_num or not token_id:
            return

        lm = self.location_manager
        try:
            if lm and lm.is_boss_defeated(boss_num):
                # Победа: удаляем токен навсегда
                self.roaming_manager.remove_boss_permanently(boss_num)
            else:
                # Поражение: сбрасываем токен, чтобы можно было встретить снова,
                # и телепортируем игрока в город
                self.roaming_manager.reset_token(token_id, cooldown=5.0)
                player = app.game.player if app.game else None
                if player:
                    player.last_global_pos = (0.19, 0.85)
                    if getattr(app, "_defeat_event", -1) < 0:
                        app._defeat_event = -1  # defeat already handled by battle.py
        except Exception as e:
            Logger.error(f"GlobalMap: Boss battle return error: {e}")

        app._boss_battle_boss_num = None
        app._boss_battle_token_id = None
        app._boss_battle_active = False

    def _show_defeat_narrative_if_needed(self):
        """Показать нарративное окно поражения, если игрок только что умер."""
        from systems.defeat_events import DEFEAT_EVENTS
        app = App.get_running_app()
        idx = getattr(app, "_defeat_event", -1)
        if idx < 0 or idx >= len(DEFEAT_EVENTS):
            return
        app._defeat_event = -1
        text = DEFEAT_EVENTS[idx]["text"]

        from kivy.uix.boxlayout import BoxLayout as BL
        from kivy.uix.button import Button as Btn
        from kivy.uix.label import Label as Lbl
        from kivy.uix.scrollview import ScrollView as SV
        from kivy.uix.popup import Popup as P

        content = BL(orientation='vertical', spacing=15, padding=20)
        scroll = SV()
        label = Lbl(
            text=text,
            font_size=16,
            size_hint_y=None,
            text_size=(500, None),
            halign='center',
            valign='middle',
            color=(0.9, 0.85, 0.8, 1),
        )
        label.bind(texture_size=label.setter('size'))
        scroll.add_widget(label)
        content.add_widget(scroll)

        btn_ok = Btn(
            text='☠️ Я помню…',
            size_hint_y=None,
            height=50,
            font_size=18,
            background_color=(0.25, 0.2, 0.15, 1),
        )
        content.add_widget(btn_ok)

        popup = P(
            title='💀 Поражение',
            content=content,
            size_hint=(0.7, 0.75),
            auto_dismiss=False,
        )
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()

    def _start_ambush_scene(self, encounter_data: dict):
        try:
            app = App.get_running_app()
            if not app.game or not app.game.player:
                return
            group = encounter_data.get("group", [])
            if not group:
                return

            zone_name = encounter_data.get("zone_name", "forest")
            ambush_enemies = []
            for member in group:
                ambush_enemies.append({
                    "enemy_type": member.get("enemy_type", ""),
                    "name": member.get("name", "Враг"),
                })
            if not ambush_enemies:
                return

            screen = app.local_location_screen
            if not screen:
                return

            screen.setup_ambush_scene(
                enemies_data=ambush_enemies,
                zone_id=zone_name,
            )
            mgr = screen.manager
            if mgr:
                mgr.current = "local_location"
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _update_camera_zoom(self):
        self.CAMERA_ZOOM = self.stealth_controller.camera_zoom

    def _start_token_updates(self):
        if self._token_update_ev:
            return
        if not self._token_graphics_inited:
            try:
                ow = max(1, self.map_overlay.width)
                oh = max(1, self.map_overlay.height)
                self.roaming_manager.set_map_size(ow, oh)
                self.roaming_manager.init_graphics(self.map_overlay.canvas.before)
                self._token_graphics_inited = True
            except Exception:
                pass
        self._token_update_ev = Clock.schedule_interval(self._update_tokens, 0.1)

    def _stop_token_updates(self):
        if self._token_update_ev:
            self._token_update_ev.cancel()
            self._token_update_ev = None
        self._destroy_all_token_canvas()

    # ──────────────────────────────────────────────
    #  Bark system (реплики над головами токенов)
    # ──────────────────────────────────────────────

    def _init_bark_system(self):
        self._bark_timer = 0.0

    def _update_barks(self, dt):
        for token in self.roaming_manager.tokens:
            if token.id in self.roaming_manager._lockout_ids:
                if token.bark_label:
                    self._remove_bark(token)
                continue
            if not token.bark_label:
                continue
            sx, sy = self._world_to_screen(token.x, token.y)
            token.bark_label.center_x = sx
            token.bark_label.y = sy + dp(12)

        self._bark_timer += dt
        if self._bark_timer >= BARK_CHECK_INTERVAL:
            self._bark_timer = 0.0
            silent_tokens = [
                t for t in self.roaming_manager.tokens
                if t.id not in self.roaming_manager._lockout_ids
                and not t.is_chasing
                and not t.bark_label
            ]
            if silent_tokens and random.random() < BARK_CHANCE_PER_CHECK:
                lucky = random.choice(silent_tokens)
                self._spawn_bark(lucky)

    def _spawn_bark(self, token, is_alert=False):
        if token.bark_label:
            self._remove_bark(token)

        e_type = token.enemy_type.lower()
        if "shaman" in e_type:
            creature_type = "shaman"
        elif "goblin" in e_type or "bog" in e_type:
            creature_type = "goblin"
        elif "toad" in e_type:
            creature_type = "toad"
        elif "orc" in e_type:
            creature_type = "orc"
        elif "draugr" in e_type:
            creature_type = "draugr"
        elif "golem" in e_type:
            creature_type = "golem"
        elif "skeleton" in e_type:
            creature_type = "skeleton"
        elif "greyling" in e_type or "gremlyn" in e_type:
            creature_type = "greyling"
        elif "specter" in e_type or "ice" in e_type:
            creature_type = "specter"
        elif "dragon" in e_type:
            creature_type = "dragon"
        elif "troll" in e_type:
            creature_type = "troll"
        elif "giant" in e_type:
            creature_type = "giant"
        elif "wolf" in e_type or "волк" in token.name.lower():
            creature_type = "wolf"
        elif "marauder" in e_type or "разведчик" in token.name.lower() or "дезертир" in token.name.lower():
            creature_type = "marauder"
        else:
            creature_type = "bandit"

        if is_alert:
            barks = ENEMY_ALERT_BARKS.get(creature_type, ["Ага! Кто тут?!"])
            duration = 2.0
        else:
            barks = ENEMY_BARKS.get(creature_type, ["..."])
            duration = BARK_DURATION

        text = random.choice(barks)

        bark_label = Label(
            text=text,
            font_size=dp(11),
            color=(1, 0.2, 0.2, 1) if is_alert else (1, 1, 1, 1),
            bold=is_alert,
            size_hint=(None, None),
            halign='center',
            valign='middle'
        )
        bark_label.texture_update()
        bark_label.size = (bark_label.texture_size[0] + dp(16), bark_label.texture_size[1] + dp(8))

        with bark_label.canvas.before:
            if is_alert:
                Color(0.4, 0.0, 0.0, 0.75)
            else:
                Color(0.1, 0.1, 0.1, 0.6)
            bark_label.bg_rect = RoundedRectangle(size=bark_label.size, pos=bark_label.pos, radius=[dp(6)])

        bark_label.bind(pos=lambda inst, val: setattr(inst.bg_rect, 'pos', val))

        self.add_widget(bark_label)
        token.bark_label = bark_label

        sx, sy = self._world_to_screen(token.x, token.y)
        bark_label.center_x = sx
        bark_label.y = sy + dp(12)

        old_timer = token._bark_timer_event
        if old_timer:
            old_timer.cancel()

        token._bark_timer_event = Clock.schedule_once(lambda dt: self._remove_bark(token), duration)

    def _remove_bark(self, token):
        timer = token._bark_timer_event
        if timer:
            timer.cancel()
        token._bark_timer_event = None
        bark_label = token.bark_label
        token.bark_label = None
        if bark_label:
            try:
                self.remove_widget(bark_label)
            except Exception:
                pass

    def _clear_all_barks(self):
        for token in self.roaming_manager.tokens:
            self._remove_bark(token)

    def _update_enter_button(self):
        """Show enter button if player is near a hotspot, hide otherwise."""
        try:
            if not getattr(self, '_player_marker', None):
                return
            cx = self._player_world_x
            cy = self._player_world_y
            nearest = None
            nearest_dist = 1e9
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
            show = False
            loc_id = None
            if nearest:
                radius = min(nearest.size[0], nearest.size[1]) / 2
                if nearest_dist <= max(42, radius * 0.6):
                    show = True
                    loc_id = getattr(nearest, '_loc_id', None)
            if show:
                if not getattr(self, '_enter_btn', None):
                    eb = Button(text='Войти', size_hint=(None, None), size=(dp(92), dp(40)))
                    def _enter(b):
                        try:
                            entered_loc = getattr(b, '_target_loc_id', 'city')
                            self.on_select_location(entered_loc)
                        except Exception:
                            pass
                    eb.bind(on_press=_enter)
                    self._enter_btn = eb
                    try:
                        root = App.get_running_app().root
                        root.add_widget(eb)
                    except Exception:
                        try:
                            self.map_container.add_widget(eb)
                        except Exception:
                            pass
                try:
                    eb = self._enter_btn
                    eb._target_loc_id = loc_id
                    # Position enter button in screen space, near player's screen position
                    sx, sy = self._world_to_screen(cx, cy)
                    win = App.get_running_app().root
                    ex = sx - eb.width / 2
                    ey = sy - self.PLAYER_MARKER_SIZE / 2 - eb.height - dp(6)
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
        if not getattr(app, 'game', None) or not getattr(app.game, 'player', None):
            popup = Popup(
                title='Ошибка',
                content=Label(text='Игра не инициализирована!'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return

        player = app.game.player
        player.last_global_pos = (
            self._player_world_x / max(1, self.map_overlay.width),
            self._player_world_y / max(1, self.map_overlay.height),
        )
        player.is_sneaking = (self.stealth_controller.mode == StealthMode.STEALTH)

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

        if loc_id == 'city':
            screen = getattr(app, 'local_location_screen', None)
            if not screen:
                return
            if enter_local_scene(app, loc_id):
                return
            popup = Popup(
                title='Ошибка',
                content=Label(text='Не удалось открыть локацию.'),
                size_hint=(0.6, 0.3),
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
        try:
            app = App.get_running_app()
            player = app.game.player if app.game else None
            gp = player.last_global_pos if player else None
            if gp and hasattr(self, 'map_overlay') and hasattr(self, '_player_marker'):
                w = max(1, self.map_overlay.width)
                h = max(1, self.map_overlay.height)
                self._player_world_x = float(w * gp[0])
                self._player_world_y = float(h * gp[1])
                self._cam_target_x = self._player_world_x
                self._cam_target_y = self._player_world_y
                self._cam_x = self._player_world_x
                self._cam_y = self._player_world_y
                pm = self._player_marker
                sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
                pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
                player.last_global_pos = None
                self._position_set = True
        except Exception:
            pass

        try:
            app = App.get_running_app()
            if app.game and app.game.player and app.game.player.is_sneaking:
                self.stealth_controller.set_mode(StealthMode.STEALTH)
                self._update_camera_zoom()
        except Exception:
            pass

        try:
            self.update_locations()
        except Exception:
            pass

        self._encounter_active = False
        self._encounter_cooldown = 0.0

        # Обработать возврат из засады: определить какие токены удалить, какие восстановить
        self._handle_ambush_return()

        # Обработать возврат из битвы с боссом
        self._handle_boss_battle_return()

        self.roaming_manager._lockout_ids.clear()

        self._prev_player_world_x = self._player_world_x
        self._prev_player_world_y = self._player_world_y
        self._init_bark_system()
        self._start_token_updates()

        # Авто-вход в город после поражения (enter_local_scene вызываем на
        # следующем кадре, чтобы не ломать текущий lifecycle ScreenManager'а)
        try:
            _app = App.get_running_app()
            if getattr(_app, "_defeat_event", -1) >= 0:
                Clock.schedule_once(lambda dt: enter_local_scene(_app, "city"), 0.1)
        except Exception:
            pass

        try:
            if hasattr(self, 'map_overlay') and hasattr(self, '_player_marker'):
                app = App.get_running_app()
                if app.game and app.game.player:
                    if hasattr(self, '_player_label') and self._player_label:
                        try:
                            self.map_container.remove_widget(self._player_label)
                        except Exception:
                            pass

                    player_name = app.game.player.name
                    player_label = Label(
                        text=player_name,
                        size_hint=(None, None),
                        size=(dp(100), dp(25)),
                        font_size=dp(14),
                        color=COLORS['gold'],
                        bold=True
                    )
                    # Add label to map_container (screen space), not map_overlay
                    self.map_container.add_widget(player_label)
                    self._player_label = player_label

                    # Position it above the player marker, using screen coords
                    sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
                    label_x = sx - player_label.width / 2
                    label_y = sy + self.PLAYER_MARKER_SIZE / 2 + dp(5)
                    player_label.pos = (label_x, label_y)
        except Exception as e:
            print(f"[ERROR] Failed to create player label: {e}")

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
        try:
            if getattr(self, '_danger_bar', None):
                self._danger_bar.cleanup()
                try:
                    self.map_container.remove_widget(self._danger_bar)
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
        try:
            if getattr(self, '_enter_btn', None):
                root = App.get_running_app().root
                if self._enter_btn in root.children:
                    root.remove_widget(self._enter_btn)
                self._enter_btn = None
        except Exception:
            pass

        self._clear_all_barks()
        self._stop_token_updates()

    def _trigger_ambush(self, enemy_id):
        """Начать бой при засаде (danger = 100%) с предупреждением."""
        try:
            app = App.get_running_app()
            if not app.game or not app.game.player:
                return
            from data.enemies import EnemyDatabase
            template = EnemyDatabase.get(enemy_id)
            if not template:
                return
            from core.creatures import Creature
            player = app.game.player
            enemy = Creature(
                template.name,
                template.base_health,
                template.base_damage,
                template.base_coins,
                level=max(1, player.level),
            )
            enemy_name = template.name

            def _start_ambush_battle(*args):
                try:
                    battlefield, _ = app.game.create_battle([enemy])
                    if hasattr(app, 'battle_screen'):
                        app.battle_screen.start_battle(battlefield, f"⚔️ Засада! {enemy_name}")
                        app.root.current = 'battle'
                except Exception as e:
                    print(f"[AMBUSH] Battle start error: {e}")

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