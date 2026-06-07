#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Базовый экран проходимой локальной карты.

Поддерживает боевые локации (враги + боссы), город (зоны входа),
таверну (NPC) и магазин (торговец).
"""

import math
import os
import random
from typing import Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    Mesh,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Scale,
    Translate,
)
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from data.local_scenes import (
    COMBAT_SCENES,
    LOCATION_BOSSES,
    build_scene_config,
)
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.ui_styles import BUTTONS_DIR, COLORS
from ui.widgets.cover_background import cover_background_image


SOCIAL_AGGRO_RADIUS = 120
DE_AGGRO_RADIUS = 250
PATROL_RADIUS = 150
CONE_ANGLE = 120
CONE_LENGTH = 200
HEARING_RADIUS = 95
PLAYER_BASE_RADIUS = 12
ENEMY_BASE_RADIUS = 12
BOSS_BASE_RADIUS = 18
NPC_BASE_RADIUS = 14
LOCAL_CAMERA_ZOOM = 1.3
LOCAL_CAMERA_LERP_SPEED = 8.0
ENTRY_POINT_X = 0.5
ENTRY_POINT_Y = 0.1
STUN_DURATION = 5.0
INVINCIBILITY_DURATION = 3.0


class LocalLocationScreen(Screen, KeyboardHandler):
    """Проходимая локальная карта с сущностями и зонами перехода."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scene_id = None
        self.location_id = None
        self.location_name = None
        self.scene_config = None
        self.parent_scene_id = None

        self._defeated_enemies = set()
        self._player_pos = [0, 0]
        self._target_pos = None
        self._entities = []
        self._current_entity = None
        self._current_battle_group = None
        self._pending_boss_entity = None
        self._update_event = None
        self._returning_from_battle = False
        self._active_zone = None
        self._move = {"up": False, "down": False, "left": False, "right": False}
        self._player_invincible_timer = 0.0
        self._paused = False
        self._chasing_active = False
        self._active_interact = None
        self._alert_source_id = None
        self._btn_sneak = None
        self._world_widget = None
        self._cam_x = 0.0
        self._cam_y = 0.0
        self._cam_target_x = 0.0
        self._cam_target_y = 0.0
        self._player_moved_this_frame = False
        self._saved_enemy_dirs = {}
        self.bind_keyboard()

        self.btn_zone_action = Button(
            text="Войти",
            size_hint=(None, None),
            size=(dp(150), dp(50)),
            background_color=COLORS["stone_light"],
            opacity=0,
        )
        self.btn_zone_action.bind(on_press=self._on_zone_action)

        self._hover_widget = Label(
            text="",
            size_hint=(None, None),
            size=(dp(220), dp(40)),
            color=COLORS.get("text_light", (1, 1, 1, 1)),
            opacity=0,
            halign="center",
            valign="middle",
        )

        self.layout = FloatLayout()
        self.add_widget(self.layout)
        self._drawing_widget = None
        self._btn_exit = None
        self._player_label = None
        self._btn_inventory = None
        self._btn_status = None
        self._btn_companions = None
        self._btn_quests = None

    def setup_scene(self, scene_id: str, parent_scene: str = None) -> None:
        """Настроить сцену перед переходом на экран."""
        self.scene_id = scene_id
        self.location_id = scene_id
        self.scene_config = build_scene_config(scene_id)
        self.parent_scene_id = parent_scene
        if self.scene_config:
            self.location_name = self.scene_config.title
        else:
            self.location_name = scene_id

    def on_enter(self):
        """Инициализация сцены при входе."""
        app = App.get_running_app()
        app.return_to_local_location = True
        app.local_scene_id = self.scene_id

        self.layout.clear_widgets()
        self._world_widget = FloatLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        with self._world_widget.canvas.before:
            PushMatrix()
            self._cam_translate = Translate()
            self._cam_scale = Scale()
        with self._world_widget.canvas.after:
            PopMatrix()
        self.layout.add_widget(self._world_widget)
        self._load_background()

        self._target_pos = None
        self._move = {"up": False, "down": False, "left": False, "right": False}
        self._entities = []
        self._current_entity = None
        self._pending_boss_entity = None
        self._active_zone = None
        self._active_interact = None
        self._alert_source_id = None
        self._chasing_active = False
        self.btn_zone_action.opacity = 0
        self.btn_zone_action.text = "Войти"
        self._chase_block_label = None

        is_combat = self.scene_config and self.scene_config.scene_type == "combat"

        if self._returning_from_battle and is_combat:
            pass
        elif is_combat:
            player = app.game.player if app.game else None
            pos_key = self.scene_id
            if (player and pos_key in getattr(player, "last_location_pos", {})
                    and getattr(player, "last_location_visited", None) == self.scene_id):
                x_norm, y_norm = player.last_location_pos[pos_key]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * ENTRY_POINT_X, self.height * ENTRY_POINT_Y]
        else:
            player = app.game.player if app.game else None
            pos_key = self.scene_id
            if player and pos_key in getattr(player, "last_location_pos", {}):
                x_norm, y_norm = player.last_location_pos[pos_key]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * 0.5, self.height * 0.5]

        self._drawing_widget = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self._world_widget.add_widget(self._drawing_widget)

        player = app.game.player if app.game else None
        if (
            self.scene_config
            and self.scene_config.scene_type == "combat"
            and player
            and getattr(player, "last_location_visited", None) == self.scene_id
        ):
            self._init_entities(use_saved=True)
        else:
            self._init_entities(use_saved=False)
            if player and self.scene_config and self.scene_config.scene_type == "combat":
                player.last_location_visited = self.scene_id

        self._ensure_safe_spawn()
        self._restore_enemy_dirs()
        self._sync_camera(immediate=True)
        self._init_ui()
        self.layout.add_widget(self.btn_zone_action)
        self.layout.add_widget(self._hover_widget)

        if app.game and app.game.player:
            self._player_label = Label(
                text=app.game.player.name,
                size_hint=(None, None),
                size=(dp(100), dp(25)),
                font_size=dp(14),
                color=COLORS["gold"],
                bold=True,
            )
            self.layout.add_widget(self._player_label)

        from kivy.core.window import Window

        try:
            Window.bind(mouse_pos=self._on_mouse_pos)
        except Exception:
            pass

        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1 / 60)

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action == "move_up":
            self._move["up"] = pressed
            return True
        if action == "move_down":
            self._move["down"] = pressed
            return True
        if action == "move_left":
            self._move["left"] = pressed
            return True
        if action == "move_right":
            self._move["right"] = pressed
            return True
        if action == "enter_location" and pressed:
            self._on_zone_action()
            return True
        if action == "exit_location" and pressed:
            self._on_exit_location()
            return True
        if action == "open_inventory" and pressed:
            self._open_inventory()
            return True
        if action == "open_status" and pressed:
            self._open_status()
            return True
        if action == "open_companions" and pressed:
            self._open_companions()
            return True
        if action == "open_quests" and pressed:
            self._open_quests()
            return True
        if action == "toggle_sneak" and pressed:
            self._toggle_sneak_mode()
            return True
        if action == "open_locations" and pressed:
            self._on_exit_location()
            return True
        return False

    def _resolve_scene_background(self) -> Optional[str]:
        """Найти фон только среди путей из конфига сцены (без fallback на другие локации)."""
        if not self.scene_config:
            return None
        for path in self.scene_config.background_candidates:
            if path and os.path.isfile(path):
                return path
        return None

    def _solid_background_color(self) -> tuple:
        """Цвет однотонной заливки, если у сцены нет фонового изображения."""
        if self.scene_config and self.scene_config.scene_type == "city":
            return (0.14, 0.14, 0.16, 1)
        return (0.12, 0.18, 0.14, 1)

    def _load_background(self) -> None:
        """Загрузить фон из конфига сцены или залить однотонным цветом."""
        bg_path = self._resolve_scene_background()
        if bg_path:
            self._world_widget.add_widget(cover_background_image(bg_path))
        else:
            filler = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
            with filler.canvas.before:
                Color(*self._solid_background_color())
                filler._bg = Rectangle(pos=filler.pos, size=filler.size)
            filler.bind(
                pos=lambda w, v: setattr(filler._bg, "pos", w.pos),
                size=lambda w, v: setattr(filler._bg, "size", w.size),
            )
            self._world_widget.add_widget(filler)

    def _init_entities(self, use_saved=False) -> None:
        """Создать сущности сцены: враги, боссы, NPC, зоны."""
        if not self.scene_config:
            return

        stype = self.scene_config.scene_type
        if stype == "combat":
            self._init_combat_entities(use_saved)
        elif stype == "city":
            self._init_city_zones()
        elif stype in ("tavern", "shop"):
            self._init_npc_entities()

    def _init_combat_entities(self, use_saved=False) -> None:
        """Враги и босс на боевой карте."""
        from systems.battle import EnemyGenerator

        app = App.get_running_app()
        player = app.game.player if app.game else None
        loc_id = self.scene_config.enemy_location_id or self.scene_id

        saved_positions = []
        saved_creatures = []
        if (
            use_saved
            and player
            and hasattr(player, "last_enemy_positions")
            and self.scene_id in player.last_enemy_positions
        ):
            saved_positions = player.last_enemy_positions[self.scene_id]
            if hasattr(player, "last_enemy_creatures") and self.scene_id in player.last_enemy_creatures:
                saved_creatures = player.last_enemy_creatures[self.scene_id]
        else:
            count = self.scene_config.enemy_count or 3
            saved_positions = self._generate_random_positions(count)
            saved_creatures = []
            for _ in range(count):
                generated = (
                    EnemyGenerator.generate_for_location(loc_id, player.level, count=1)[0]
                    if player
                    else None
                )
                saved_creatures.append(generated)
            if player:
                player.last_enemy_positions[self.scene_id] = saved_positions
                player.last_enemy_creatures[self.scene_id] = saved_creatures

        count = self.scene_config.enemy_count or 3
        for i in range(count):
            if i in self._defeated_enemies:
                continue
            if i < len(saved_positions):
                x_norm, y_norm = saved_positions[i]
            else:
                x_norm, y_norm = random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)

            creature = (
                saved_creatures[i]
                if i < len(saved_creatures) and saved_creatures[i]
                else (
                    EnemyGenerator.generate_for_location(loc_id, player.level, count=1)[0]
                    if player
                    else None
                )
            )
            self._entities.append(
                {
                    "type": "enemy",
                    "id": i,
                    "x_norm": x_norm,
                    "y_norm": y_norm,
                    "x": self.width * x_norm,
                    "y": self.height * y_norm,
                    "spawn_x_norm": x_norm,
                    "spawn_y_norm": y_norm,
                    "radius": self._enemy_radius(),
                    "defeated": False,
                    "creature": creature,
                    "name": creature.name if creature else "Неизвестный",
                    "level": creature.level if creature else 1,
                    "stun_timer": 0,
                    "ai_state": "patrol",
                    "aggro_reason": None,
                    "alert_source_id": None,
                    "patrol_target_x_norm": x_norm,
                    "patrol_target_y_norm": y_norm,
                    "patrol_pause_timer": random.uniform(0, 2),
                    "dir_x": 0,
                    "dir_y": -1,
                    "patrol_speed": dp(20),
                    "chase_speed": dp(170),
                }
            )

        self._maybe_add_boss(player)

    def _maybe_add_boss(self, player) -> None:
        """Добавить босса на карту, если он доступен и не побеждён."""
        boss_cfg = LOCATION_BOSSES.get(self.scene_id)
        if not boss_cfg or not player:
            return

        app = App.get_running_app()
        lm = app.game.location_manager if app.game else None
        if lm and not lm.is_boss_unlocked(boss_cfg.boss_num):
            return
        if lm and lm.is_boss_defeated(boss_cfg.boss_num):
            return

        from systems.battle import EnemyGenerator

        boss_creature = EnemyGenerator.generate_boss(boss_cfg.enemy_id)
        if not boss_creature:
            return

        self._entities.append(
            {
                "type": "boss",
                "id": f"boss_{boss_cfg.boss_num}",
                "boss_num": boss_cfg.boss_num,
                "x_norm": boss_cfg.x_norm,
                "y_norm": boss_cfg.y_norm,
                "x": self.width * boss_cfg.x_norm,
                "y": self.height * boss_cfg.y_norm,
                "radius": self._boss_radius(),
                "defeated": False,
                "creature": boss_creature,
                "name": boss_cfg.name,
                "level": boss_creature.level,
                "stun_timer": 0,
            }
        )

    def _init_city_zones(self) -> None:
        """Зоны входа в таверну и магазин."""
        for zone in self.scene_config.zones:
            r = dp(zone.radius_norm * 800)
            self._entities.append(
                {
                    "type": "zone",
                    "id": zone.zone_id,
                    "target_scene": zone.target_scene,
                    "label": zone.label,
                    "x_norm": zone.x_norm,
                    "y_norm": zone.y_norm,
                    "x": self.width * zone.x_norm,
                    "y": self.height * zone.y_norm,
                    "radius": max(dp(40), r),
                    "defeated": False,
                    "description": zone.label,
                }
            )

    def _init_npc_entities(self) -> None:
        """Серые круги NPC на карте таверны или магазина."""
        app = App.get_running_app()
        for npc_cfg in self.scene_config.npcs:
            if npc_cfg.npc_id == "npc_dragonslayer":
                lm = app.game.location_manager if app.game else None
                if lm and lm.locations.get("mountains", None) and lm.locations["mountains"].is_locked:
                    continue
            if npc_cfg.npc_id != "shopkeeper" and npc_cfg.action == "dialogue":
                npc = app.npc_manager.get_npc(npc_cfg.npc_id) if getattr(app, "npc_manager", None) else None
                if not npc:
                    continue
                display_name = npc.name
            else:
                display_name = npc_cfg.name

            self._entities.append(
                {
                    "type": "npc",
                    "id": npc_cfg.npc_id,
                    "action": npc_cfg.action,
                    "x_norm": npc_cfg.x_norm,
                    "y_norm": npc_cfg.y_norm,
                    "x": self.width * npc_cfg.x_norm,
                    "y": self.height * npc_cfg.y_norm,
                    "radius": self._npc_radius(),
                    "defeated": False,
                    "name": display_name,
                    "level": 0,
                }
            )

    def _scene_value(self, attr_name: str, fallback: float) -> float:
        if not self.scene_config:
            return fallback
        value = getattr(self.scene_config, attr_name, fallback)
        return float(value if value is not None else fallback)

    def _player_radius(self) -> float:
        return dp(PLAYER_BASE_RADIUS * self._scene_value("player_scale", 1.0))

    def _enemy_radius(self) -> float:
        return dp(ENEMY_BASE_RADIUS * self._scene_value("enemy_scale", 1.0))

    def _boss_radius(self) -> float:
        return dp(BOSS_BASE_RADIUS * self._scene_value("boss_scale", 1.0))

    def _npc_radius(self) -> float:
        return dp(NPC_BASE_RADIUS * self._scene_value("npc_scale", 1.0))

    def _camera_zoom(self) -> float:
        return max(1.0, self._scene_value("camera_zoom", LOCAL_CAMERA_ZOOM))

    def _is_player_sneaking(self) -> bool:
        app = App.get_running_app()
        player = app.game.player if app.game else None
        return bool(getattr(player, "is_sneaking", False))

    def _refresh_sneak_button(self) -> None:
        if not self._btn_sneak:
            return
        if self._is_player_sneaking():
            self._btn_sneak.text = "Красться: ВКЛ"
            self._btn_sneak.background_color = (0.25, 0.45, 0.30, 0.95)
        else:
            self._btn_sneak.text = "Красться: ВЫКЛ"
            self._btn_sneak.background_color = COLORS["stone_light"]

    def _toggle_sneak_mode(self, *_args) -> None:
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if not player:
            return
        player.is_sneaking = not bool(getattr(player, "is_sneaking", False))
        self._refresh_sneak_button()

    def _generate_random_positions(self, count=3):
        """Случайные позиции с минимальной дистанцией."""
        positions = []
        for _ in range(count):
            for _attempt in range(50):
                x_norm = random.uniform(0.15, 0.85)
                y_norm = random.uniform(0.15, 0.85)
                too_close = any(
                    ((x_norm - sx) ** 2 + (y_norm - sy) ** 2) ** 0.5 < 0.2
                    for sx, sy in positions
                )
                if not too_close:
                    positions.append((x_norm, y_norm))
                    break
            else:
                positions.append((random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)))
        return positions

    def _init_ui(self) -> None:
        """Кнопки выхода и сервисные панели."""
        exit_icon = (
            os.path.join(BUTTONS_DIR, "city.png")
            if self.scene_config and self.scene_config.exit_target == "parent"
            else os.path.join(BUTTONS_DIR, "global_map.png")
        )
        btn_exit = Image(
            source=exit_icon,
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={"right": 0.98, "top": 0.98},
        )
        self.layout.add_widget(btn_exit)
        self._btn_exit = btn_exit

        lbl_name = Label(
            text=self.location_name or "Локация",
            size_hint=(None, None),
            size=(dp(280), dp(40)),
            pos_hint={"x": 0.02, "top": 0.98},
            font_size="18sp",
        )
        self.layout.add_widget(lbl_name)

        for attr, icon, pos_x in (
            ("_btn_inventory", "inventory.png", 0.01),
            ("_btn_status", "status.png", 0.12),
            ("_btn_companions", "companion.png", 0.23),
            ("_btn_quests", "active_quests.png", 0.34),
        ):
            btn = Image(
                source=os.path.join(BUTTONS_DIR, icon),
                size_hint=(None, None),
                size=(dp(72), dp(72)),
                pos_hint={"x": pos_x, "y": 0.01},
            )
            self.layout.add_widget(btn)
            setattr(self, attr, btn)

        self._btn_sneak = Button(
            text="",
            size_hint=(None, None),
            size=(dp(170), dp(44)),
            pos_hint={"right": 0.98, "y": 0.12},
        )
        self._btn_sneak.bind(on_press=self._toggle_sneak_mode)
        self.layout.add_widget(self._btn_sneak)
        self._refresh_sneak_button()

    def on_touch_down(self, touch):
        """Движение игрока и клики по UI."""
        if self._btn_exit and self._hit_widget(self._btn_exit, touch):
            self._on_exit_location()
            return True
        if self._btn_sneak and self._hit_widget(self._btn_sneak, touch):
            self._toggle_sneak_mode()
            return True
        for btn, handler in (
            (self._btn_inventory, self._open_inventory),
            (self._btn_status, self._open_status),
            (self._btn_companions, self._open_companions),
            (self._btn_quests, self._open_quests),
        ):
            if btn and self._hit_widget(btn, touch):
                handler()
                return True
        if self.btn_zone_action.opacity > 0 and self._hit_widget(self.btn_zone_action, touch):
            self._on_zone_action()
            return True
        local_x, local_y = self.to_local(touch.x, touch.y)
        world_x, world_y = self._screen_to_world(local_x, local_y)
        self._target_pos = [world_x, world_y]
        return True

    @staticmethod
    def _hit_widget(widget, touch) -> bool:
        if not widget:
            return False
        x, y = widget.pos
        w, h = widget.size
        return x <= touch.x <= x + w and y <= touch.y <= y + h

    def _open_inventory(self, *args):
        from ui.widgets.navigation_buttons import prepare_inventory_navigation

        prepare_inventory_navigation("local_location")
        app = App.get_running_app()
        if getattr(app, "inventory_screen", None):
            try:
                app.inventory_screen.update_inventory()
            except Exception:
                pass
        if getattr(app, "game", None) and getattr(app.game, "player", None):
            self.manager.current = "inventory"

    def _open_status(self, *args):
        app = App.get_running_app()
        if getattr(app, "status_screen", None):
            try:
                app.status_screen.update_status()
            except Exception:
                pass
        if getattr(app, "game", None) and getattr(app.game, "player", None):
            self.manager.current = "status"

    def _open_companions(self, *args):
        app = App.get_running_app()
        if getattr(app, "companion_management_screen", None):
            try:
                app.companion_management_screen.update_companion()
            except Exception:
                pass
        if getattr(app, "game", None) and getattr(app.game, "player", None):
            self.manager.current = "companion_management"

    def _open_quests(self, *args):
        app = App.get_running_app()
        if getattr(app, "active_quests_screen", None):
            try:
                app.active_quests_screen.update_quests()
            except Exception:
                pass
        if getattr(app, "game", None) and getattr(app.game, "player", None):
            self.manager.current = "active_quests"

    def _sync_entity_positions(self) -> None:
        """Пересчитать экранные координаты сущностей по нормализованным."""
        w = max(1, self.width)
        h = max(1, self.height)
        for ent in self._entities:
            ent["x"] = ent["x_norm"] * w
            ent["y"] = ent["y_norm"] * h

    def _screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        zoom = self._camera_zoom()
        world_x = (screen_x - self.width / 2) / zoom + self._cam_x
        world_y = (screen_y - self.height / 2) / zoom + self._cam_y
        return world_x, world_y

    def _world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        zoom = self._camera_zoom()
        screen_x = (world_x - self._cam_x) * zoom + self.width / 2
        screen_y = (world_y - self._cam_y) * zoom + self.height / 2
        return screen_x, screen_y

    def _clamp_camera_target(self, target_x: float, target_y: float) -> tuple[float, float]:
        zoom = self._camera_zoom()
        half_view_w = self.width / max(2.0, 2.0 * zoom)
        half_view_h = self.height / max(2.0, 2.0 * zoom)

        if half_view_w >= self.width / 2:
            cam_x = self.width / 2
        else:
            cam_x = max(half_view_w, min(self.width - half_view_w, target_x))

        if half_view_h >= self.height / 2:
            cam_y = self.height / 2
        else:
            cam_y = max(half_view_h, min(self.height - half_view_h, target_y))

        return cam_x, cam_y

    def _sync_camera(self, dt: float = 0.0, immediate: bool = False) -> None:
        if not self._world_widget:
            return

        self._cam_target_x, self._cam_target_y = self._clamp_camera_target(
            self._player_pos[0],
            self._player_pos[1],
        )

        if immediate:
            self._cam_x = self._cam_target_x
            self._cam_y = self._cam_target_y
        else:
            lerp_factor = 1.0 - 2.71828 ** (-LOCAL_CAMERA_LERP_SPEED * dt)
            self._cam_x += (self._cam_target_x - self._cam_x) * lerp_factor
            self._cam_y += (self._cam_target_y - self._cam_y) * lerp_factor

        zoom = self._camera_zoom()
        self._cam_scale.x = zoom
        self._cam_scale.y = zoom
        self._cam_translate.x = self.width / 2 - self._cam_x * zoom
        self._cam_translate.y = self.height / 2 - self._cam_y * zoom

    def _on_game_update(self, dt):
        """Игровой цикл: движение, столкновения, отрисовка."""
        if not self.scene_id or self._paused:
            return

        self._sync_entity_positions()

        app = App.get_running_app()
        player = app.game.player if app.game else None
        base_speed = player.move_speed if player else 200
        if self._is_player_sneaking():
            base_speed = int(base_speed * 0.4)
        prev_x, prev_y = self._player_pos[0], self._player_pos[1]

        mx = (1 if self._move["right"] else 0) - (1 if self._move["left"] else 0)
        my = (1 if self._move["up"] else 0) - (1 if self._move["down"] else 0)
        if mx or my:
            self._target_pos = None
            length = (mx * mx + my * my) ** 0.5
            if length:
                speed = dp(base_speed) * dt
                self._player_pos[0] += (mx / length) * speed
                self._player_pos[1] += (my / length) * speed
        elif self._target_pos:
            dx = self._target_pos[0] - self._player_pos[0]
            dy = self._target_pos[1] - self._player_pos[1]
            distance = (dx**2 + dy**2) ** 0.5
            if distance < dp(8):
                self._target_pos = None
            else:
                speed = dp(base_speed) * dt
                move_dist = min(speed, distance)
                self._player_pos[0] += (dx / distance) * move_dist
                self._player_pos[1] += (dy / distance) * move_dist

        self._player_pos[0] = max(dp(10), min(self.width - dp(10), self._player_pos[0]))
        self._player_pos[1] = max(dp(10), min(self.height - dp(10), self._player_pos[1]))
        self._player_moved_this_frame = (
            ((self._player_pos[0] - prev_x) ** 2 + (self._player_pos[1] - prev_y) ** 2) ** 0.5
            > 0.1
        )

        if self._player_invincible_timer > 0:
            self._player_invincible_timer = max(0, self._player_invincible_timer - dt)

        for ent in self._entities:
            if ent.get("stun_timer", 0) > 0:
                ent["stun_timer"] = max(0, ent["stun_timer"] - dt)

        player_is_noisy = self._player_moved_this_frame and not self._is_player_sneaking()
        self._update_enemy_ai(dt, player_is_noisy=player_is_noisy)
        self._sync_camera(dt)
        self._check_collisions()
        self._draw_game()

    def _enemy_sees_player(self, ent, px: float, py: float) -> bool:
        if not ent or ent.get("type") != "enemy":
            return False
        dx_player = px - ent["x"]
        dy_player = py - ent["y"]
        dist_to_player = (dx_player**2 + dy_player**2) ** 0.5
        if dist_to_player <= 0 or dist_to_player > CONE_LENGTH:
            return False

        edx = ent.get("dir_x", 0)
        edy = ent.get("dir_y", -1)
        norm = (edx * edx + edy * edy) ** 0.5
        if norm <= 0:
            return False

        cone_angle_rad = math.radians(CONE_ANGLE / 2)
        dot = (dx_player / dist_to_player * edx / norm) + (
            dy_player / dist_to_player * edy / norm
        )
        return dot >= math.cos(cone_angle_rad)

    def _reset_enemy_aggro(self, ent) -> None:
        ent["ai_state"] = "patrol"
        ent["aggro_reason"] = None
        ent["alert_source_id"] = None
        ent["patrol_target_x_norm"] = ent.get("spawn_x_norm", ent["x_norm"])
        ent["patrol_target_y_norm"] = ent.get("spawn_y_norm", ent["y_norm"])
        ent["patrol_pause_timer"] = 0

    def _get_enemy_by_id(self, enemy_id):
        if enemy_id is None:
            return None
        for ent in self._entities:
            if ent.get("type") == "enemy" and ent.get("id") == enemy_id and not ent["defeated"]:
                return ent
        return None

    def _restore_enemy_dirs(self) -> None:
        if not self._saved_enemy_dirs:
            return
        for ent in self._entities:
            if ent.get("type") != "enemy" or ent["defeated"]:
                continue
            eid = ent.get("id")
            if eid in self._saved_enemy_dirs:
                dx, dy = self._saved_enemy_dirs[eid]
                ent["dir_x"] = dx
                ent["dir_y"] = dy

    def _trigger_hearing_aggro(self, ent) -> None:
        ent["ai_state"] = "chase"
        ent["aggro_reason"] = "hearing"
        ent["alert_source_id"] = None

    def _clear_social_aggro(self, source_id=None) -> None:
        for ent in self._entities:
            if ent.get("type") != "enemy" or ent["defeated"]:
                continue
            if ent.get("aggro_reason") not in ("sight_source", "social"):
                continue
            if source_id is not None and ent.get("alert_source_id") != source_id:
                continue
            self._reset_enemy_aggro(ent)

        if source_id is None or self._alert_source_id == source_id:
            self._alert_source_id = None

    def _trigger_social_aggro(self, spotter) -> None:
        source_id = spotter.get("id")
        if source_id is None:
            return
        if self._alert_source_id is not None and self._alert_source_id != source_id:
            self._clear_social_aggro(self._alert_source_id)

        sx, sy = spotter["x"], spotter["y"]
        self._alert_source_id = source_id
        for ent in self._entities:
            if ent.get("type") != "enemy" or ent["defeated"]:
                continue
            if ent.get("stun_timer", 0) > 0:
                continue
            dist = ((ent["x"] - sx) ** 2 + (ent["y"] - sy) ** 2) ** 0.5
            if ent is spotter or dist <= SOCIAL_AGGRO_RADIUS:
                ent["ai_state"] = "chase"
                ent["alert_source_id"] = source_id
                ent["aggro_reason"] = "sight_source" if ent is spotter else "social"

    def _update_enemy_ai(self, dt, player_is_noisy=False):
        """AI врагов: патрулирование, преследование, возврат."""
        px, py = self._player_pos
        w = max(1, self.width)
        h = max(1, self.height)
        player_chasing = False

        active_source = self._get_enemy_by_id(self._alert_source_id)
        if active_source and (
            active_source["defeated"] or active_source.get("stun_timer", 0) > 0
        ):
            self._clear_social_aggro(self._alert_source_id)
            active_source = None
        if active_source and not self._enemy_sees_player(active_source, px, py):
            self._clear_social_aggro(active_source.get("id"))
            active_source = None

        for ent in self._entities:
            if ent["defeated"] or ent.get("type") not in ("enemy",):
                continue
            if ent.get("stun_timer", 0) > 0:
                continue

            dx_player = px - ent["x"]
            dy_player = py - ent["y"]
            dist_to_player = (dx_player**2 + dy_player**2) ** 0.5

            state = ent.get("ai_state", "patrol")
            sees_player = self._enemy_sees_player(ent, px, py)
            hears_player = player_is_noisy and dist_to_player <= HEARING_RADIUS

            if sees_player and self._alert_source_id != ent.get("id"):
                self._trigger_social_aggro(ent)
                active_source = ent
                state = ent.get("ai_state", "chase")
            elif state == "patrol" and hears_player:
                self._trigger_hearing_aggro(ent)
                state = "chase"

            if state == "patrol":
                pause = ent.get("patrol_pause_timer", 0)
                if pause > 0:
                    ent["patrol_pause_timer"] = max(0, pause - dt)
                    continue

                tx_norm = ent.get("patrol_target_x_norm", ent["x_norm"])
                ty_norm = ent.get("patrol_target_y_norm", ent["y_norm"])
                tx = tx_norm * w
                ty = ty_norm * h
                dx = tx - ent["x"]
                dy = ty - ent["y"]
                dist_to_target = (dx * dx + dy * dy) ** 0.5

                if dist_to_target < dp(5):
                    ent["patrol_pause_timer"] = random.uniform(1.0, 3.0)
                    spawn_x = ent.get("spawn_x_norm", ent["x_norm"])
                    spawn_y = ent.get("spawn_y_norm", ent["y_norm"])
                    angle = random.uniform(0, 6.2832)
                    radius_norm = PATROL_RADIUS / max(w, h)
                    ent["patrol_target_x_norm"] = max(
                        0.05, min(0.95, spawn_x + radius_norm * math.cos(angle))
                    )
                    ent["patrol_target_y_norm"] = max(
                        0.05, min(0.95, spawn_y + radius_norm * math.sin(angle))
                    )
                else:
                    speed = ent.get("patrol_speed", dp(20)) * dt
                    step = min(speed, dist_to_target)
                    target_dir_x = dx / dist_to_target
                    target_dir_y = dy / dist_to_target
                    rot_factor = min(1.0, dt * 4.0)
                    ent["dir_x"] += (target_dir_x - ent["dir_x"]) * rot_factor
                    ent["dir_y"] += (target_dir_y - ent["dir_y"]) * rot_factor
                    dir_norm = (ent["dir_x"] ** 2 + ent["dir_y"] ** 2) ** 0.5
                    if dir_norm > 0:
                        ent["dir_x"] /= dir_norm
                        ent["dir_y"] /= dir_norm
                    ent["x"] += (dx / dist_to_target) * step
                    ent["y"] += (dy / dist_to_target) * step
                    ent["x_norm"] = ent["x"] / w
                    ent["y_norm"] = ent["y"] / h

            elif state == "chase":
                aggro_reason = ent.get("aggro_reason")
                if aggro_reason in ("sight_source", "social"):
                    source = self._get_enemy_by_id(ent.get("alert_source_id"))
                    if not source or not self._enemy_sees_player(source, px, py):
                        self._clear_social_aggro(ent.get("alert_source_id"))
                        continue
                elif aggro_reason == "hearing":
                    if sees_player:
                        self._trigger_social_aggro(ent)
                    elif dist_to_player > DE_AGGRO_RADIUS:
                        self._reset_enemy_aggro(ent)
                        continue

                player_chasing = True
                if dist_to_player > 0:
                    speed = ent.get("chase_speed", dp(170)) * dt
                    step = min(speed, dist_to_player)
                    ent["dir_x"] = dx_player / dist_to_player
                    ent["dir_y"] = dy_player / dist_to_player
                    ent["x"] += (dx_player / dist_to_player) * step
                    ent["y"] += (dy_player / dist_to_player) * step
                    ent["x_norm"] = ent["x"] / w
                    ent["y_norm"] = ent["y"] / h

        self._chasing_active = player_chasing

    def _check_collisions(self):
        """Столкновения игрока с сущностями."""
        player_r = self._player_radius()
        zone_near = None
        self.btn_zone_action.opacity = 0
        self._active_zone = None
        self._active_interact = None

        for ent in self._entities:
            if ent["defeated"]:
                continue
            dx = self._player_pos[0] - ent["x"]
            dy = self._player_pos[1] - ent["y"]
            dist = (dx**2 + dy**2) ** 0.5
            etype = ent.get("type")

            if etype == "zone":
                if dist < ent["radius"]:
                    zone_near = ent
            elif etype == "npc":
                if dist < player_r + ent["radius"] + dp(8):
                    self._active_interact = ent
            elif dist < player_r + ent["radius"]:
                if etype in ("enemy", "boss"):
                    if ent.get("stun_timer", 0) > 0:
                        continue
                    if self._player_invincible_timer > 0:
                        continue
                    if etype == "boss":
                        if self._pending_boss_entity is not None:
                            continue
                        self._pending_boss_entity = ent
                        self._show_boss_confirmation(ent)
                        return
                    self._start_battle(ent)
                    return

        if self._active_interact:
            ent = self._active_interact
            label = "Поговорить" if ent.get("action") == "dialogue" else "Открыть"
            sx, sy = self._world_to_screen(ent["x"], ent["y"])
            screen_radius = ent["radius"] * self._camera_zoom()
            self.btn_zone_action.text = f"{label}: {ent.get('name', '')}"
            self.btn_zone_action.opacity = 1
            self.btn_zone_action.pos = (
                sx - self.btn_zone_action.width / 2,
                sy + screen_radius + dp(10),
            )
        elif zone_near:
            self._active_zone = zone_near
            sx, sy = self._world_to_screen(zone_near["x"], zone_near["y"])
            screen_radius = zone_near["radius"] * self._camera_zoom()
            self.btn_zone_action.text = f"Войти: {zone_near.get('label', '...')}"
            self.btn_zone_action.opacity = 1
            self.btn_zone_action.pos = (
                sx - self.btn_zone_action.width / 2,
                sy + screen_radius + dp(10),
            )

    def _interact_npc(self, ent) -> None:
        """Взаимодействие с NPC (диалог, магазин, меню таверны)."""
        action = ent.get("action", "dialogue")
        app = App.get_running_app()

        if action == "shop":
            if getattr(app, "shop_screen", None):
                app.shop_screen.update_shop()
            self.manager.current = "shop"
            return

        if action == "tavern_menu":
            if getattr(app, "tavern_screen", None):
                app.tavern_screen.update_tavern()
            self.manager.current = "tavern"
            return

        npc_id = ent.get("id")
        npc = app.npc_manager.get_npc(npc_id) if getattr(app, "npc_manager", None) else None
        if npc and getattr(app, "npc_dialogue_screen", None):
            app.npc_dialogue_screen.show_npc_dialogue(npc)
            self.manager.current = "npc_dialogue"

    def _on_zone_action(self, *_args):
        """Переход в подлокацию или взаимодействие с NPC."""
        if self._active_interact:
            self._interact_npc(self._active_interact)
            self._active_interact = None
            return
        if not self._active_zone:
            return
        target = self._active_zone.get("target_scene")
        if not target:
            return
        app = App.get_running_app()
        self._returning_from_battle = False
        self._save_player_state()
        self._stop_loop()
        from data.local_scenes import enter_local_scene

        enter_local_scene(app, target, parent_scene=self.scene_id)

    def _collect_nearby_enemies(self, center_entity):
        """Собрать всех непобеждённых врагов в радиусе социального агра."""
        cx, cy = center_entity["x"], center_entity["y"]
        group = [center_entity]
        for ent in self._entities:
            if ent is center_entity:
                continue
            if ent["defeated"] or ent.get("type") != "enemy":
                continue
            dx = ent["x"] - cx
            dy = ent["y"] - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= SOCIAL_AGGRO_RADIUS:
                group.append(ent)
        return group

    def _can_trigger_surprise_attack(self, battle_group) -> bool:
        if not battle_group:
            return False
        if any(ent.get("type") != "enemy" for ent in battle_group):
            return False
        if self._alert_source_id is not None:
            return False
        return not any(ent.get("ai_state") == "chase" for ent in battle_group)

    def _show_boss_confirmation(self, entity):
        """Показать диалог подтверждения перед боем с боссом."""
        self._paused = True
        boss_name = entity.get("name", "босс")
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        content.add_widget(Label(
            text=f"Вы встретили {boss_name}.\nНачать битву?",
            text_size=(dp(280), None),
            halign='center',
            valign='middle',
            font_size=dp(18),
        ))
        btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        btn_yes = Button(text='Да, в бой!')
        btn_no = Button(text='Нет, отойти')
        btn_yes.bind(on_press=lambda _: self._confirm_boss_battle(entity, popup))
        btn_no.bind(on_press=lambda _: self._cancel_boss_battle(popup))
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        content.add_widget(btn_layout)
        popup = Popup(
            title='👑 Босс!',
            content=content,
            size_hint=(0.7, 0.45),
            auto_dismiss=False,
        )
        popup.open()

    def _confirm_boss_battle(self, entity, popup):
        popup.dismiss()
        self._pending_boss_entity = None
        self._start_battle(entity)

    def _cancel_boss_battle(self, popup):
        popup.dismiss()
        self._pending_boss_entity = None
        self._player_invincible_timer = 1.5
        self._paused = False

    def _start_battle(self, entity):
        """Начать бой с врагом или боссом. Втягивает соседних врагов в радиус аггро."""
        self._returning_from_battle = True
        app = App.get_running_app()
        player = app.game.player if app.game else None

        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = []
            creatures = []
            for e in self._entities:
                if e.get("type") == "enemy" and not e["defeated"]:
                    positions.append((e["x_norm"], e["y_norm"]))
                    creatures.append(e.get("creature"))
            if positions:
                player.last_enemy_positions[self.scene_id] = positions
                player.last_enemy_creatures[self.scene_id] = creatures

        self._stop_loop()

        etype = entity.get("type")
        if etype == "boss":
            battle_group = [entity]
        else:
            battle_group = self._collect_nearby_enemies(entity)
        surprise_attack = self._can_trigger_surprise_attack(battle_group)

        self._current_battle_group = battle_group
        self._current_entity = battle_group[0]

        creatures = [e.get("creature") for e in battle_group if e.get("creature")]
        if not creatures or not app.game or not player:
            return

        try:
            from systems.battle import Battlefield

            battlefield = Battlefield(player, creatures, surprise_attack=surprise_attack)
            app._battle_from_local_location = True
            app.battle_screen.from_local_location = True
            if etype == "boss":
                title = f"👑 {entity.get('name', creatures[0].name)}"
            else:
                names = ", ".join(e.get("name", "?") for e in battle_group)
                title = f"⚔️ {names}"
            app.battle_screen.start_battle(battlefield, title)
            self.manager.current = "battle"
        except Exception:
            import traceback

            traceback.print_exc()

    def prepare_defeat_state(self):
        """Подготовить карту после поражения: стан врагам, бессмертие игроку, без возобновления цикла."""
        if self._current_battle_group:
            for ent in self._current_battle_group:
                if ent.get("type") == "enemy":
                    ent["stun_timer"] = STUN_DURATION
            self._player_invincible_timer = INVINCIBILITY_DURATION

        self._current_entity = None
        self._current_battle_group = None

        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = [
                (e["x_norm"], e["y_norm"])
                for e in self._entities
                if e.get("type") == "enemy" and not e["defeated"]
            ]
            if positions:
                player.last_enemy_positions[self.scene_id] = positions

    def pause_game(self):
        """Приостановить игровой цикл (пока открыт popup)."""
        self._paused = True

    def resume_game(self):
        """Возобновить игровой цикл после закрытия popup."""
        self._paused = False

    def on_return_from_battle(self):
        """Возврат после боя: при победе очищает врагов, при поражении — стан."""
        app = App.get_running_app()
        player = app.game.player if app.game else None
        victory = (
            getattr(app, "battle_result", None) and app.battle_result.victory
        )

        if victory and self._current_battle_group:
            has_boss = False
            for ent in self._current_battle_group:
                etype = ent.get("type")
                if etype == "boss":
                    ent["defeated"] = True
                    has_boss = True
                elif etype == "enemy":
                    ent["defeated"] = True
                    self._defeated_enemies.add(ent["id"])
            if has_boss and player and app.game:
                try:
                    app.game.autosave()
                except Exception:
                    pass
        elif self._current_battle_group:
            for ent in self._current_battle_group:
                if ent.get("type") == "enemy" and ent.get("stun_timer", 0) < 2.0:
                    ent["stun_timer"] = 2.0
            if self._player_invincible_timer < 2.0:
                self._player_invincible_timer = 2.0

        self._current_entity = None
        self._current_battle_group = None
        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = [
                (e["x_norm"], e["y_norm"])
                for e in self._entities
                if e.get("type") == "enemy" and not e["defeated"]
            ]
            if positions:
                player.last_enemy_positions[self.scene_id] = positions

        if self._update_event:
            self._update_event.cancel()
        if not self._paused:
            self._update_event = Clock.schedule_interval(self._on_game_update, 1 / 60)

    def _on_mouse_pos(self, window, pos):
        local_pos = self.to_local(*pos)
        world_pos = self._screen_to_world(local_pos[0], local_pos[1])
        for ent in self._entities:
            if ent["defeated"]:
                continue
            dx = world_pos[0] - ent["x"]
            dy = world_pos[1] - ent["y"]
            if (dx**2 + dy**2) ** 0.5 <= ent["radius"]:
                etype = ent.get("type")
                if etype == "enemy":
                    tip = f"{ent['name']} (Lv.{ent['level']})"
                elif etype == "boss":
                    tip = f"👑 {ent['name']} (босс)"
                elif etype == "zone":
                    tip = ent.get("description", "Зона")
                elif etype == "npc":
                    tip = ent.get("name", "NPC")
                else:
                    tip = ent.get("name", "")
                self._hover_widget.text = tip
                self._hover_widget.opacity = 1
                self._hover_widget.pos = (local_pos[0] + dp(10), local_pos[1] + dp(10))
                return
        self._hover_widget.opacity = 0

    def _draw_game(self):
        if not self._drawing_widget:
            return

        self._drawing_widget.canvas.clear()
        with self._drawing_widget.canvas:
            for ent in self._entities:
                if ent["defeated"]:
                    continue
                etype = ent.get("type")
                r = ent["radius"]

                if etype == "enemy":
                    ex, ey = ent["x"], ent["y"]
                    edx = ent.get("dir_x", 0)
                    edy = ent.get("dir_y", -1)
                    dir_norm = (edx * edx + edy * edy) ** 0.5

                    # --- Hearing radius ---
                    Color(0.35, 0.65, 1, 0.06)
                    Ellipse(
                        pos=(ex - HEARING_RADIUS, ey - HEARING_RADIUS),
                        size=(HEARING_RADIUS * 2, HEARING_RADIUS * 2),
                    )
                    Color(0.35, 0.65, 1, 0.22)
                    Line(
                        circle=(ex, ey, HEARING_RADIUS),
                        width=1,
                    )

                    # --- Directional cone ---
                    if dir_norm > 0.01:
                        cone_length = CONE_LENGTH
                        half_a = math.radians(CONE_ANGLE / 2)
                        base_angle = math.atan2(edy / dir_norm, edx / dir_norm)
                        segments = 14
                        verts = [ex, ey, 0, 0]
                        indices = [0]
                        for i in range(segments + 1):
                            t = i / segments
                            theta = base_angle - half_a + t * 2 * half_a
                            px = ex + math.cos(theta) * cone_length
                            py = ey + math.sin(theta) * cone_length
                            verts.extend([px, py, 0, 0])
                            indices.append(i + 1)
                        Color(1, 0.6, 0, 0.06)
                        Mesh(vertices=verts, indices=indices, mode='triangle_fan')

                        arc_points = []
                        for i in range(segments + 1):
                            t = i / segments
                            theta = base_angle - half_a + t * 2 * half_a
                            px = ex + math.cos(theta) * cone_length
                            py = ey + math.sin(theta) * cone_length
                            arc_points.extend([px, py])
                        Color(1, 0.6, 0, 0.2)
                        Line(points=[ex, ey, arc_points[0], arc_points[1]], width=1)
                        Line(points=[ex, ey, arc_points[-2], arc_points[-1]], width=1)
                        Line(points=arc_points, width=1)

                if etype == "zone":
                    Color(0.2, 0.5, 0.9, 0.35)
                    Ellipse(pos=(ent["x"] - r, ent["y"] - r), size=(r * 2, r * 2))
                    Color(0.1, 0.3, 0.8, 1)
                    Line(circle=(ent["x"], ent["y"], r), width=2)
                elif etype == "npc":
                    Color(0.55, 0.55, 0.55, 0.85)
                    Ellipse(pos=(ent["x"] - r, ent["y"] - r), size=(r * 2, r * 2))
                    Color(0.35, 0.35, 0.35, 1)
                    Line(circle=(ent["x"], ent["y"], r), width=2)
                elif etype == "boss":
                    Color(0.85, 0.45, 0.1, 0.9)
                    Ellipse(pos=(ent["x"] - r, ent["y"] - r), size=(r * 2, r * 2))
                    Color(0.7, 0.2, 0.05, 1)
                    Line(circle=(ent["x"], ent["y"], r), width=3)
                elif ent.get("stun_timer", 0) > 0:
                    Color(0.3, 0.5, 0.8, 0.6)
                    Ellipse(pos=(ent["x"] - r, ent["y"] - r), size=(r * 2, r * 2))
                    Color(0.2, 0.4, 0.7, 1)
                    Line(circle=(ent["x"], ent["y"], r), width=2)
                else:
                    Color(1, 0, 0, 0.7)
                    Ellipse(pos=(ent["x"] - r, ent["y"] - r), size=(r * 2, r * 2))
                    Color(0.8, 0, 0, 1)
                    Line(circle=(ent["x"], ent["y"], r), width=2)

            pr = self._player_radius()
            if self._is_player_sneaking():
                Color(0.45, 0.95, 0.65, 0.85)
            else:
                Color(1, 1, 0, 0.8)
            Ellipse(
                pos=(self._player_pos[0] - pr, self._player_pos[1] - pr),
                size=(pr * 2, pr * 2),
            )
            if self._is_player_sneaking():
                Color(0.2, 0.7, 0.35, 1)
            else:
                Color(1, 0.8, 0, 1)
            Line(circle=(self._player_pos[0], self._player_pos[1], pr), width=2)

            if self._player_label:
                label_x, label_y = self._world_to_screen(self._player_pos[0], self._player_pos[1])
                screen_radius = pr * self._camera_zoom()
                self._player_label.pos = (
                    label_x - self._player_label.width / 2,
                    label_y + screen_radius + dp(5),
                )

    def _ensure_safe_spawn(self) -> None:
        """Сместить врагов, чья зона аггра перекрывает точку спавна игрока."""
        if not self.scene_config or self.scene_config.scene_type != "combat":
            return
        spawn_x = self.width * ENTRY_POINT_X
        spawn_y = self.height * ENTRY_POINT_Y
        safe_margin = HEARING_RADIUS + dp(30)
        for ent in self._entities:
            if ent.get("type") != "enemy" or ent["defeated"]:
                continue
            ex, ey = ent["x"], ent["y"]
            dx = spawn_x - ex
            dy = spawn_y - ey
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < safe_margin:
                angle = random.uniform(0, 6.2832)
                shift = safe_margin + dp(60)
                ent["x"] = spawn_x + math.cos(angle) * shift
                ent["y"] = spawn_y + math.sin(angle) * shift
                ent["x_norm"] = max(0.05, min(0.95, ent["x"] / max(1, self.width)))
                ent["y_norm"] = max(0.05, min(0.95, ent["y"] / max(1, self.height)))
                ent["spawn_x_norm"] = ent["x_norm"]
                ent["spawn_y_norm"] = ent["y_norm"]
                ent["patrol_target_x_norm"] = ent["x_norm"]
                ent["patrol_target_y_norm"] = ent["y_norm"]

    def _save_player_state(self) -> None:
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and self.scene_id:
            player.last_location_pos[self.scene_id] = (
                self._player_pos[0] / max(1, self.width),
                self._player_pos[1] / max(1, self.height),
            )

    def _stop_loop(self) -> None:
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    def on_leave(self):
        self._save_player_state()
        self._saved_enemy_dirs = {}
        for ent in self._entities:
            if ent.get("type") == "enemy" and not ent["defeated"]:
                eid = ent.get("id")
                if eid is not None:
                    self._saved_enemy_dirs[eid] = (
                        ent.get("dir_x", 0),
                        ent.get("dir_y", -1),
                    )
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = [
                (e["x_norm"], e["y_norm"])
                for e in self._entities
                if e.get("type") == "enemy" and not e["defeated"]
            ]
            if positions:
                player.last_enemy_positions[self.scene_id] = positions

        self.btn_zone_action.opacity = 0
        self._hover_widget.opacity = 0
        if self._player_label:
            try:
                self.layout.remove_widget(self._player_label)
            except Exception:
                pass
            self._player_label = None
        from kivy.core.window import Window

        try:
            Window.unbind(mouse_pos=self._on_mouse_pos)
        except Exception:
            pass
        self._stop_loop()

    def _is_anyone_chasing(self):
        """Проверить, есть ли враги в состоянии погони."""
        if self._chasing_active:
            return True
        for ent in self._entities:
            if ent.get("ai_state") == "chase" and not ent["defeated"]:
                return True
        return False

    def _show_chase_block_notification(self) -> None:
        """Показать компактное уведомление о блокировке выхода в углу экрана."""
        if self._chase_block_label:
            return
        self._chase_block_label = Label(
            text='⚠️ Вас преследуют! Сначала разберитесь с врагами.',
            size_hint=(None, None),
            size=(dp(300), dp(30)),
            pos_hint={'right': 0.98, 'y': 0.02},
            font_size=dp(13),
            color=COLORS.get("warning", (1, 0.6, 0, 1)),
            halign='right',
            valign='middle',
        )
        self.layout.add_widget(self._chase_block_label)
        Clock.schedule_once(lambda dt: self._hide_chase_block_notification(), 3.0)

    def _hide_chase_block_notification(self) -> None:
        if self._chase_block_label:
            try:
                self.layout.remove_widget(self._chase_block_label)
            except Exception:
                pass
            self._chase_block_label = None

    def _on_exit_location(self, *_args):
        """Выход: на карту региона или в родительскую сцену."""
        if self._is_anyone_chasing():
            self._show_chase_block_notification()
            return
        app = App.get_running_app()
        self._save_player_state()
        self._stop_loop()
        self._returning_from_battle = False
        self._player_invincible_timer = 0
        self._paused = False

        if self.scene_config and self.scene_config.exit_target == "parent":
            parent = self.parent_scene_id or "city"
            from data.local_scenes import enter_local_scene
            self._saved_enemy_dirs = {}
            enter_local_scene(app, parent)
            return

        app.return_to_local_location = False
        player = app.game.player if app.game else None
        if player:
            player.last_location_visited = None
            if hasattr(player, "last_enemy_positions"):
                player.last_enemy_positions.pop(self.scene_id, None)
            if hasattr(player, "last_enemy_creatures"):
                player.last_enemy_creatures.pop(self.scene_id, None)
            if hasattr(player, "last_location_pos"):
                player.last_location_pos.pop(self.scene_id, None)

        self.scene_id = None
        self.location_id = None
        self._entities = []
        self._current_entity = None
        self._current_battle_group = None
        self._pending_boss_entity = None
        self._target_pos = None
        self._saved_enemy_dirs = {}

        try:
            if player:
                app.game.autosave()
        except Exception:
            pass

        self.manager.current = "location_select"
