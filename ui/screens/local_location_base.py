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
    scene_background_path,
)
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.ui_styles import BUTTONS_DIR, COLORS
from ui.widgets.cover_background import cover_background_image
from kivy.graphics import RoundedRectangle # Нужен для красивой плашки текста

from core.config import (
    SOCIAL_AGGRO_RADIUS,
    DE_AGGRO_RADIUS,
    PATROL_RADIUS,
    CONE_ANGLE,
    CONE_LENGTH,
    HEARING_RADIUS,
    PLAYER_BASE_RADIUS,
    ENEMY_BASE_RADIUS,
    BOSS_BASE_RADIUS,
    NPC_BASE_RADIUS,
    LOCAL_CAMERA_ZOOM,
    LOCAL_CAMERA_LERP_SPEED,
    ENTRY_POINT_X,
    ENTRY_POINT_Y,
    STUN_DURATION,
    INVINCIBILITY_DURATION,
    LOCAL_ENEMY_PATROL_SPEED,
    LOCAL_ENEMY_CHASE_SPEED,
    ENEMY_BARKS,
    ENEMY_ALERT_BARKS,
    AMBUSH_SEARCH_BARKS,
    BARK_CHANCE_PER_CHECK,
    BARK_CHECK_INTERVAL,
    BARK_DURATION,
)


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
        self._btn_stance = None
        self._combat_status_label = None
        self._damage_labels = []  # список активных Label с уроном
        self._world_widget = None
        self._cam_x = 0.0
        self._cam_y = 0.0
        self._cam_target_x = 0.0
        self._cam_target_y = 0.0
        self._player_moved_this_frame = False
        self._saved_enemy_dirs = {}
        self._is_ambush = False
        self._ambush_total_enemies = 0
        self._player_entity = None  # entity-словарь игрока для real-time combat
        self._ambush_zone_id = None
        self._ambush_exit_block_label = None
        self._ambush_enemies_data = None
        self._total_time = 0.0
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
        self._is_ambush = False
        self._ambush_total_enemies = 0
        self._ambush_zone_id = None
        self._ambush_enemies_data = None
        self.scene_id = scene_id
        self.location_id = scene_id
        self.scene_config = build_scene_config(scene_id)
        self.parent_scene_id = parent_scene
        if self.scene_config:
            self.location_name = self.scene_config.title
        else:
            self.location_name = scene_id

    def setup_ambush_scene(self, enemies_data: list, zone_id: str) -> None:
        self._is_ambush = True
        self._ambush_enemies_data = list(enemies_data)
        self._ambush_zone_id = zone_id
        self._ambush_total_enemies = len(enemies_data)
        self._defeated_enemies.clear()
        self.scene_id = f"ambush_{zone_id}"
        self.location_id = zone_id
        self.scene_config = build_scene_config(zone_id)
        self.parent_scene_id = None
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player:
            player._ambush_defeated_set = set()
            if hasattr(player, "last_enemy_positions"):
                player.last_enemy_positions.pop(self.scene_id, None)
            if hasattr(player, "last_enemy_creatures"):
                player.last_enemy_creatures.pop(self.scene_id, None)
        zone_titles = {
            "forest": "🌲 Засада в лесу",
            "swamp": "🏞️ Засада на болотах",
            "mines": "⛏️ Засада в шахтах",
            "mountains": "⛰️ Засада в горах",
        }
        self.location_name = zone_titles.get(zone_id, f"Засада в {zone_id}")

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
        self._current_entity = None
        self._pending_boss_entity = None
        self._active_zone = None
        self._active_interact = None
        self._alert_source_id = None
        self._chasing_active = False
        self.btn_zone_action.opacity = 0
        self.btn_zone_action.text = "Войти"
        self._chase_block_label = None
        self._ambush_exit_block_label = None

        is_combat = self.scene_config and self.scene_config.scene_type == "combat"

        player = app.game.player if app.game else None

        # -- Position --
        if self._returning_from_battle and is_combat:
            pass
        elif self._is_ambush:
            pos_key = self.scene_id
            if (player and pos_key in getattr(player, "last_location_pos", {})):
                x_norm, y_norm = player.last_location_pos[pos_key]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * ENTRY_POINT_X, self.height * ENTRY_POINT_Y]
        elif is_combat:
            pos_key = self.scene_id
            if (player and pos_key in getattr(player, "last_location_pos", {})
                    and getattr(player, "last_location_visited", None) == self.scene_id):
                x_norm, y_norm = player.last_location_pos[pos_key]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * ENTRY_POINT_X, self.height * ENTRY_POINT_Y]
        else:
            pos_key = self.scene_id
            if player and pos_key in getattr(player, "last_location_pos", {}):
                x_norm, y_norm = player.last_location_pos[pos_key]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * 0.5, self.height * 0.5]

        # -- Entities --
        skip_init = self._returning_from_battle and is_combat

        if not skip_init:
            self._entities = []
            if self._is_ambush:
                self._defeated_enemies.clear()
                if player and hasattr(player, "_ambush_defeated_set") and player._ambush_defeated_set:
                    self._defeated_enemies = set(player._ambush_defeated_set)
                    player._ambush_defeated_set = set()
                self._init_ambush_entities()
            elif (
                self.scene_config
                and self.scene_config.scene_type == "combat"
                and player
                and getattr(player, "last_location_visited", None) == self.scene_id
            ):
                self._defeated_enemies.clear()
                self._init_entities(use_saved=True)
            else:
                self._init_entities(use_saved=False)
                if player and self.scene_config and self.scene_config.scene_type == "combat":
                    player.last_location_visited = self.scene_id

        self._drawing_widget = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self._world_widget.add_widget(self._drawing_widget)

        self._returning_from_battle = False
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
        except Exception as e:
            Logger.warning(f"LocalLocation: Could not bind mouse_pos inside {self.scene_id}. Error: {e}")

        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1 / 60)

        self._init_bark_system()

        if self._is_ambush and not self._returning_from_battle:
            Clock.schedule_once(lambda dt: self._trigger_ambush_starting_barks(), 0.3)

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
        if self._is_ambush and self._ambush_zone_id:
            bg_path = scene_background_path(self._ambush_zone_id)
            if bg_path and os.path.isfile(bg_path):
                self._world_widget.add_widget(cover_background_image(bg_path))
                return
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

    def _init_ambush_entities(self) -> None:
        if not self._ambush_enemies_data:
            return
        from systems.battle import EnemyGenerator
        from data.enemies import EnemyDatabase

        app = App.get_running_app()
        player = app.game.player if app.game else None
        player_level = player.level if player else 1

        saved_positions = []
        saved_creatures = []
        if (
            player
            and hasattr(player, "last_enemy_positions")
            and self.scene_id in player.last_enemy_positions
        ):
            saved_positions = player.last_enemy_positions[self.scene_id]
            if hasattr(player, "last_enemy_creatures") and self.scene_id in player.last_enemy_creatures:
                saved_creatures = player.last_enemy_creatures[self.scene_id]
        else:
            saved_positions = self._generate_random_positions(len(self._ambush_enemies_data))
            saved_creatures = []
            for i in range(len(self._ambush_enemies_data)):
                if i in self._defeated_enemies:
                    saved_creatures.append(None)
                    continue
                member = self._ambush_enemies_data[i]
                enemy_type = member.get("enemy_type", "")
                template = EnemyDatabase.get(enemy_type)
                if template:
                    from core.creatures import Creature
                    creature = Creature(
                        template.name,
                        template.base_health,
                        template.base_damage,
                        template.base_coins,
                        level=max(1, player_level),
                    )
                    creature._template = template
                    EnemyGenerator._equip_from_loot_table(creature)
                    saved_creatures.append(creature)
                else:
                    saved_creatures.append(None)
            if player:
                player.last_enemy_positions[self.scene_id] = saved_positions
                player.last_enemy_creatures[self.scene_id] = saved_creatures

        for i, member in enumerate(self._ambush_enemies_data):
            if i in self._defeated_enemies:
                continue

            enemy_type = member.get("enemy_type", "")
            enemy_name = member.get("name", "Враг")
            template = EnemyDatabase.get(enemy_type)

            if i < len(saved_positions):
                x_norm, y_norm = saved_positions[i]
            else:
                x_norm = random.uniform(0.15, 0.85)
                y_norm = random.uniform(0.15, 0.85)

            creature = None
            if i < len(saved_creatures) and saved_creatures[i]:
                creature = saved_creatures[i]
                display_name = creature.name
            elif template:
                from core.creatures import Creature
                creature = Creature(
                    template.name,
                    template.base_health,
                    template.base_damage,
                    template.base_coins,
                    level=max(1, player_level),
                )
                creature._template = template
                EnemyGenerator._equip_from_loot_table(creature)
                display_name = template.name
            else:
                from core.creatures import Creature
                creature = Creature(
                    enemy_name,
                    base_health=30,
                    base_damage=8,
                    base_coins=5,
                    level=max(1, player_level),
                )
                display_name = enemy_name

            self._entities.append({
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
                "name": display_name,
                "level": creature.level,
                "stun_timer": 0,
                "ai_state": "patrol",
                "aggro_reason": None,
                "alert_source_id": None,
                "patrol_target_x_norm": x_norm,
                "patrol_target_y_norm": y_norm,
                "patrol_pause_timer": random.uniform(0, 2),
                "dir_x": 0,
                "dir_y": -1,
                "patrol_speed": dp(LOCAL_ENEMY_PATROL_SPEED),
                "chase_speed": dp(LOCAL_ENEMY_CHASE_SPEED),
                "in_combat": False,
                "combat_target": None,
                "readiness": 0.0,
                "attack_phase": "idle",
                "phase_timer": 0.0,
                "phase_duration": 0.0,
                "origin_x": 0.0,
                "origin_y": 0.0,
                "rest_x": self.width * x_norm,
                "rest_y": self.height * y_norm,
                "blocked": False,
                "block_flash_timer": 0.0,
                "staggered": False,
                "stagger_timer": 0.0,
                "damage_numbers": [],
                "death_timer": 0.0,
            })

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
            is_defeated = i in self._defeated_enemies
            if i < len(saved_positions):
                x_norm, y_norm = saved_positions[i]
            else:
                x_norm, y_norm = random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)

            creature = None
            if i < len(saved_creatures) and saved_creatures[i]:
                creature = saved_creatures[i]
            elif player:
                try:
                    creature = EnemyGenerator.generate_for_location(loc_id, player.level, count=1)[0]
                except Exception as e:
                    Logger.error(f"LocalLocation: Enemy generator failed for loc {loc_id}. Error: {e}")
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
                    "defeated": is_defeated,
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
                    "patrol_speed": dp(LOCAL_ENEMY_PATROL_SPEED),
                    "chase_speed": dp(LOCAL_ENEMY_CHASE_SPEED),
                    "in_combat": False,
                    "combat_target": None,
                    "readiness": 0.0,
                    "attack_phase": "idle",
                    "phase_timer": 0.0,
                    "phase_duration": 0.0,
                    "origin_x": 0.0,
                    "origin_y": 0.0,
                    "rest_x": self.width * x_norm,
                    "rest_y": self.height * y_norm,
                    "blocked": False,
                    "block_flash_timer": 0.0,
                    "staggered": False,
                    "stagger_timer": 0.0,
                    "damage_numbers": [],
                    "death_timer": 0.0,
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
                "in_combat": False,
                "combat_target": None,
                "readiness": 0.0,
                "attack_phase": "idle",
                "phase_timer": 0.0,
                "phase_duration": 0.0,
                "origin_x": 0.0,
                "origin_y": 0.0,
                "rest_x": self.width * boss_cfg.x_norm,
                "rest_y": self.height * boss_cfg.y_norm,
                "blocked": False,
                "block_flash_timer": 0.0,
                "staggered": False,
                "stagger_timer": 0.0,
                "damage_numbers": [],
                "death_timer": 0.0,
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

    def _toggle_stance(self, *_args) -> None:
        """Переключить стойку игрока."""
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if not player:
            return
        current = getattr(player, "stance", "aggressive")
        stances = ["aggressive", "passive", "defensive"]
        labels = {"aggressive": "\u2694 Ст: Агр", "passive": "\U0001f6e1 Ст: Пасс", "defensive": "\u2697 Ст: Защ"}
        idx = (stances.index(current) + 1) % len(stances) if current in stances else 0
        player.stance = stances[idx]
        self._btn_stance.text = labels.get(player.stance, f"Ст: {player.stance}")
        # Обновить player entity
        if self._player_entity:
            self._player_entity["stance"] = player.stance

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

        self._btn_stance = Button(
            text="\u2694 Ст: Агр",
            size_hint=(None, None),
            size=(dp(160), dp(44)),
            background_color=COLORS["hp_green"],
            color=(1, 1, 1, 1),
            bold=True,
            pos_hint={"right": 0.98, "y": 0.06},
        )
        self._btn_stance.bind(on_press=self._toggle_stance)
        self.layout.add_widget(self._btn_stance)

        self._refresh_sneak_button()

    def on_touch_down(self, touch):
        """Движение игрока и клики по UI."""
        if self._btn_exit and self._hit_widget(self._btn_exit, touch):
            self._on_exit_location()
            return True
        if self._btn_sneak and self._hit_widget(self._btn_sneak, touch):
            self._toggle_sneak_mode()
            return True
        if self._btn_stance and self._hit_widget(self._btn_stance, touch):
            self._toggle_stance()
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
        """Пересчитать экранные координаты сущностей по нормализованным.
        НЕ затираем позиции тех, кто в real-time бою — ими управляет _update_rt_combat.
        """
        w = max(1, self.width)
        h = max(1, self.height)
        for ent in self._entities:
            if ent.get("in_combat"):
                # Combat-система сама двигает ent["x"]/ent["y"] через close_speed и анимации
                continue
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
        """Игровой цикл: движение, real-time бой, столкновения, отрисовка."""
        if not self.scene_id or self._paused:
            return
        self._total_time += dt
        self._update_barks(dt)
        self._sync_entity_positions()

        # -- движение игрока --
        app = App.get_running_app()
        player = app.game.player if app.game else None
        base_speed = player.move_speed if player else 200
        if self._is_player_sneaking():
            base_speed = int(base_speed * 0.4)
        # В бою скорость игрока снижена вдвое — напряжение и готовность к защите
        if self._player_entity and self._player_entity.get("in_combat"):
            base_speed = int(base_speed * 0.5)
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

        # Синхронизация player entity
        self._sync_player_entity()

        # Проверка смерти игрока в RT combat
        player_ent = self._player_entity
        if player_ent and player_ent.get("in_combat"):
            player_ref = player_ent.get("_player_ref")
            if player_ref and not player_ref.is_alive:
                # Смерть в RT combat
                self._end_rt_combat(victory=False)
                self.prepare_defeat_state(from_rt=True)
                # Показываем popup
                from kivy.uix.popup import Popup
                from kivy.uix.label import Label
                popup = Popup(title="Поражение",
                              content=Label(text="Вы пали в бою..."),
                              size_hint=(0.6, 0.4))
                popup.open()
                return

        if self._player_invincible_timer > 0:
            self._player_invincible_timer = max(0, self._player_invincible_timer - dt)

        for ent in self._entities:
            if ent.get("stun_timer", 0) > 0:
                ent["stun_timer"] = max(0, ent["stun_timer"] - dt)

        player_is_noisy = self._player_moved_this_frame and not self._is_player_sneaking()
        self._update_enemy_ai(dt, player_is_noisy=player_is_noisy)

        # Real-time combat
        any_combat = self._is_any_combat_active()
        if any_combat:
            # Обновляем entity игрока до актуальной позиции
            self._sync_combat_to_player_pos()
            self._update_combat_targeting()
            self._update_rt_combat(dt)
            self._update_combat_facing()  # поворот к цели
            self._check_combat_end()
            # Ещё раз синхронизируем — анимации могли изменить позицию
            self._sync_combat_to_player_pos()

        self._sync_camera(dt)
        self._check_collisions()
        # Раздвигаем накладывающиеся сущности
        self._push_entities_apart()
        # Обновить плавающие damage number label'ы
        self._update_damage_labels()
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
                # ТРИГГЕР ТРЕВОГИ: Если этот конкретный враг ещё не гнался за игроком, он кричит
                if ent.get("ai_state") != "chase":
                    self._spawn_bark(ent, is_alert=True)

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
            
        # Теперь мы сбрасываем общий агр только если источник потерял игрока 
        # И при этом НИКТО другой из врагов в состоянии "chase" больше не видит игрока
        if active_source and not self._enemy_sees_player(active_source, px, py):
            any_other_sees = any(
                e for e in self._entities 
                if e.get("type") == "enemy" and not e["defeated"] and e.get("ai_state") == "chase" and self._enemy_sees_player(e, px, py)
            )
            if not any_other_sees:
                self._clear_social_aggro(active_source.get("id"))
                active_source = None

        for ent in self._entities:
            if ent["defeated"] or ent.get("type") not in ("enemy",):
                continue
            if ent.get("stun_timer", 0) > 0:
                continue
            # В real-time бою AI не двигает врага — combat система управляет позицией
            if ent.get("in_combat"):
                continue

            dx_player = px - ent["x"]
            dy_player = py - ent["y"]
            dist_to_player = (dx_player**2 + dy_player**2) ** 0.5

            state = ent.get("ai_state", "patrol")
            sees_player = self._enemy_sees_player(ent, px, py)
            hears_player = player_is_noisy and dist_to_player <= HEARING_RADIUS

            # Если другой враг уже в chase и пробегает рядом → присоединяемся
            if state != "chase" and player_chasing and dist_to_player <= dp(200):
                ent["ai_state"] = "chase"
                ent["aggro_reason"] = "social"
                ent["alert_source_id"] = self._alert_source_id
                state = "chase"

            if sees_player and self._alert_source_id != ent.get("id"):
                # Если погоня уже идёт от другого источника — не переключаем его,
                # а просто присоединяем этого врага к текущей тревоге.
                # Это предотвращает множественный сброс/создание реплик,
                # когда несколько врагов видят игрока одновременно.
                if self._alert_source_id is not None:
                    if state != "chase":
                        ent["ai_state"] = "chase"
                        ent["alert_source_id"] = self._alert_source_id
                        ent["aggro_reason"] = "social"
                elif state != "chase":
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
                # Близко к игроку → вступаем в бой
                if dist_to_player <= dp(300):
                    ent["in_combat"] = True
                    ent["attack_phase"] = "idle"
                    ent["combat_target"] = self._get_player_entity()
                    ent["rest_x"] = ent["x"]
                    ent["rest_y"] = ent["y"]
                    continue  # combat система управляет дальше

                # Слишком далеко → выходим из погони
                if dist_to_player > DE_AGGRO_RADIUS:
                    if ent.get("aggro_reason") in ("sight_source", "social"):
                        self._clear_social_aggro(ent.get("alert_source_id"))
                    else:
                        self._reset_enemy_aggro(ent)
                    continue

                # Бежим к игроку
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

    def _push_entities_apart(self):
        """Раздвинуть накладывающиеся друг на друга entity.
        Все живые entity не должны перекрываться — ни в бою, ни вне боя.
        Для участников боя дополнительно синхронизируем rest_x/rest_y,
        чтобы combat-фазы (recovery/attack) не возвращали в старое место.
        """
        all_ents = []
        if self._player_entity and not self._player_entity.get("defeated"):
            all_ents.append(self._player_entity)
        for ent in self._entities:
            if not ent.get("defeated") and ent.get("type") in ("enemy", "boss"):
                all_ents.append(ent)
        w = max(1, self.width)
        h = max(1, self.height)
        for i, a in enumerate(all_ents):
            for b in all_ents[i + 1:]:
                dx = b["x"] - a["x"]
                dy = b["y"] - a["y"]
                dist = (dx * dx + dy * dy) ** 0.5
                min_dist = a["radius"] + b["radius"]
                if dist < min_dist and dist > 0.1:
                    overlap = min_dist - dist
                    push = overlap * 0.5
                    nx = dx / dist
                    ny = dy / dist
                    a["x"] -= nx * push
                    a["y"] -= ny * push
                    b["x"] += nx * push
                    b["y"] += ny * push
                    # Если раздвинули участника боя — синхронизируем
                    # rest (чтоб recovery не утащил обратно) и норм-координаты
                    for ent in (a, b):
                        if ent.get("in_combat"):
                            ent["rest_x"] = ent["x"]
                            ent["rest_y"] = ent["y"]
                            ent["x_norm"] = ent["x"] / w
                            ent["y_norm"] = ent["y"] / h

    def _check_collisions(self):
        """Столкновения игрока с сущностями."""
        player_r = self._player_radius()
        zone_near = None
        self.btn_zone_action.opacity = 0
        self._active_zone = None
        self._active_interact = None

        for ent in self._entities:
            if ent["defeated"]:
                if ent.get("type") not in ("enemy", "boss"):
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
            elif etype in ("enemy", "boss") and ent["defeated"]:
                if dist < player_r + ent["radius"] + dp(15):
                    label = "Осмотреть" if ent.get("_looted") else "Обобрать"
                    self._active_interact = ent
                    self.btn_zone_action.text = f"{label}: {ent.get('name', 'Труп')}"
            elif dist < player_r + ent["radius"]:
                if etype in ("enemy", "boss"):
                    if ent.get("stun_timer", 0) > 0:
                        continue
                    if self._player_invincible_timer > 0:
                        continue
                    if ent.get("in_combat"):
                        continue  # этот конкретный враг уже в бою — не переинициируем
                    # Если уже идёт бой — новый враг присоединяется
                    if self._is_any_combat_active():
                        self._join_rt_combat(ent)
                        return
                    if etype == "boss":
                        if self._pending_boss_entity is not None:
                            continue
                        self._pending_boss_entity = ent
                        self._show_boss_confirmation(ent)
                        return
                    # RT COMBAT: инициируем real-time бой вместо текстового
                    self._initiate_rt_combat(ent)
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

    def _is_any_combat_active(self) -> bool:
        """Проверить, идёт ли сейчас real-time бой в локации."""
        for ent in self._entities:
            if ent.get("in_combat") and not ent.get("defeated"):
                if ent.get("type") in ("enemy", "boss"):
                    return True
        return False

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
        """Переход в подлокацию, взаимодействие с NPC или обобрать труп."""
        if self._active_interact and self._active_interact.get("defeated"):
            self._loot_corpse(self._active_interact)
            self._active_interact = None
            return
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

    def _loot_corpse(self, corpse_ent):
        """Обобрать труп: показать окно выбора лута."""
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if not player:
            return

        creature = corpse_ent.get("creature")
        loot_drops = []
        gold = 0
        xp = 0

        # Если труп ещё не лутали — генерируем лут и награды
        if not corpse_ent.get("_looted"):
            if creature:
                gold = creature.coins
                xp = creature.base_xp
                raw_loot = creature.generate_loot()
                if raw_loot:
                    from data.items import ItemDatabase
                    ItemDatabase.initialize()
                    from core.combat.loot import LootDrop
                    for item_id, qty in raw_loot:
                        loot_drops.append(LootDrop(item_id, qty))
            corpse_ent["_loot_gold"] = gold
            corpse_ent["_loot_xp"] = xp
            corpse_ent.setdefault("_loot_items", [])
            for ld in loot_drops:
                corpse_ent["_loot_items"].append({
                    "item_id": ld.item_id,
                    "qty": ld.quantity,
                })
            corpse_ent.setdefault("_player_items", [])
        else:
            # Восстанавливаем лут из сохранённых данных трупа
            from data.items import ItemDatabase
            ItemDatabase.initialize()
            from core.combat.loot import LootDrop
            for ld_data in corpse_ent.get("_loot_items", []):
                loot_drops.append(LootDrop(ld_data["item_id"], ld_data["qty"]))
            gold = corpse_ent.get("_loot_gold", 0)
            xp = corpse_ent.get("_loot_xp", 0)

        from ui.loot_window import LootWindow

        # Определяем имена для заголовков
        corpse_name = corpse_ent.get('name', 'Труп')
        player_name = player.name if player else "Игрок"

        def on_loot_done(selected=None):
            """Закрыть окно и начислить золото/опыт (только при первом лутании)."""
            if not corpse_ent.get("_looted"):
                if gold > 0:
                    player.coins += gold
                if xp > 0:
                    player.add_experience(xp)
                corpse_ent["_looted"] = True
                corpse_ent["defeated"] = True
            # Сохраняем ТО, ЧТО ОСТАЛОСЬ в окне лута (взятые предметы удалены)
            if loot_window:
                corpse_ent["_loot_items"] = [
                    {"item_id": ld.item_id, "qty": ld.quantity}
                    for ld in loot_window.loot_items
                ]
            if popup:
                try:
                    popup.dismiss()
                except Exception:
                    pass

        loot_window = LootWindow(
            loot_drops, player.inventory, on_loot_done,
            gold=gold, xp=xp,
            left_title=corpse_name,
            right_title=player_name,
        )

        from kivy.core.window import Window as KivyWindow
        # Показываем системный курсор поверх Popup
        KivyWindow.show_cursor = True
        from kivy.uix.popup import Popup
        popup = Popup(
            title="",
            content=loot_window,
            size_hint=(0.55, 0.45),
            pos_hint={"x": 0.02, "y": 0.38},
            auto_dismiss=False,
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
            on_dismiss=lambda *_: setattr(KivyWindow, 'show_cursor', False),
        )
        popup.open()

    def _init_player_entity(self) -> dict:
        """Создать entity-словарь для игрока (для real-time combat)."""
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if not player:
            return None
        ent = {
            "type": "player",
            "id": "player",
            "x": self._player_pos[0],
            "y": self._player_pos[1],
            "radius": self._player_radius(),
            "defeated": False,
            "creature": player,
            "_player_ref": player,
            "_is_player": True,
            "name": player.name,
            "stance": getattr(player, "stance", "aggressive"),
            "in_combat": False,
            "combat_target": None,
            "readiness": 0.0,
            "attack_phase": "idle",
            "phase_timer": 0.0,
            "phase_duration": 0.0,
            "origin_x": 0.0,
            "origin_y": 0.0,
            "rest_x": self._player_pos[0],
            "rest_y": self._player_pos[1],
            "blocked": False,
            "block_flash_timer": 0.0,
            "staggered": False,
            "stagger_timer": 0.0,
            "damage_numbers": [],
            "death_timer": 0.0,
            "stun_timer": 0,
        }
        self._player_entity = ent
        return ent

    def _get_player_entity(self) -> dict:
        """Вернуть entity-словарь игрока, создать если нет."""
        if self._player_entity is None:
            self._init_player_entity()
        return self._player_entity

    def _sync_player_entity(self) -> None:
        """Синхронизировать player entity: позицию только если не в combat-фазе."""
        ent = self._get_player_entity()
        if not ent:
            return
        player = ent.get("_player_ref")
        if player:
            ent["stance"] = getattr(player, "stance", "aggressive")

        # В combat-фазах windup/strike/knockback НЕ затираем позицию — пусть combat управляет
        combat_phase = ent.get("attack_phase", "idle")
        if combat_phase in ("windup", "strike", "knockback"):
            # Но обновляем rest для recovery, чтобы возвращаться к месту где игрок
            if ent.get("in_combat") and combat_phase != "knockback":
                ent["rest_x"] = self._player_pos[0]
                ent["rest_y"] = self._player_pos[1]
            return

        # idle / recovery: синхронизируем из _player_pos
        ent["x"] = self._player_pos[0]
        ent["y"] = self._player_pos[1]
        if combat_phase == "idle":
            ent["rest_x"] = self._player_pos[0]
            ent["rest_y"] = self._player_pos[1]

    def _sync_combat_to_player_pos(self) -> None:
        """Синхронизировать игрока между entity и _player_pos."""
        ent = self._player_entity
        if not ent:
            return
        phase = ent.get("attack_phase", "idle")
        # Во время анимации атаки/отбрасывания entity диктует позицию
        if ent.get("in_combat") and phase in ("windup", "strike", "knockback", "recovery"):
            self._player_pos[0] = ent["x"]
            self._player_pos[1] = ent["y"]
        else:
            # Обычно игрок управляет, entity следует
            ent["x"] = self._player_pos[0]
            ent["y"] = self._player_pos[1]
            if ent.get("in_combat"):
                ent["rest_x"] = ent["x"]
                ent["rest_y"] = ent["y"]

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
            # Сохраняем позиции и суще указ ТОЛЬКО обычных врагов (не боссов!)
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

    def _initiate_rt_combat(self, center_entity) -> None:
        """Начать real-time бой вокруг центрального врага."""
        # Уже в бою — не переинициируем
        if self._is_any_combat_active():
            return

        app = App.get_running_app()
        player = app.game.player if app.game else None
        if not player:
            return

        # Собираем врагов в радиусе
        battle_group = self._collect_nearby_enemies(center_entity)

        # Отмечаем всех бойцов как in_combat
        for ent in battle_group:
            ent["in_combat"] = True
            ent["readiness"] = random.uniform(0.0, 0.5)
            ent["attack_phase"] = "idle"
            # Фиксируем текущую позицию как rest (чтоб не телепортировались на spawn)
            ent["rest_x"] = ent["x"]
            ent["rest_y"] = ent["y"]

        # Отмечаем игрока
        player_ent = self._get_player_entity()
        if player_ent:
            player_ent["in_combat"] = True
            player_ent["readiness"] = random.uniform(0.0, 0.5)
            player_ent["rest_x"] = self._player_pos[0]
            player_ent["rest_y"] = self._player_pos[1]

        # Показываем комбат-индикатор
        self._show_combat_indicator()

        self._update_combat_targeting()

    def _join_rt_combat(self, new_enemy) -> None:
        """Присоединить нового врага к уже идущему бою."""
        new_enemy["in_combat"] = True
        new_enemy["readiness"] = random.uniform(0.2, 0.6)
        new_enemy["attack_phase"] = "idle"
        new_enemy["rest_x"] = new_enemy["x"]
        new_enemy["rest_y"] = new_enemy["y"]
        # Назначаем цель — игрок
        player_ent = self._get_player_entity()
        if player_ent:
            new_enemy["combat_target"] = player_ent
        self._update_combat_targeting()

    def _update_combat_targeting(self) -> None:
        """Подтвердить/обновить цели бойцов (только когда бой активен)."""
        alive_enemies = [e for e in self._entities
                         if e.get("type") in ("enemy", "boss") and not e["defeated"]]
        player_ent = self._get_player_entity()
        max_combat_range = dp(350)

        # --- Игрок вступает в бой если хоть один враг бьёт его ---
        if player_ent and not player_ent.get("in_combat"):
            for ent in alive_enemies:
                if ent.get("in_combat") and ent.get("combat_target") is player_ent:
                    player_ent["in_combat"] = True
                    player_ent["attack_phase"] = "idle"
                    player_ent["rest_x"] = player_ent["x"]
                    player_ent["rest_y"] = player_ent["y"]
                    break

        # --- Враги: валидировать/сбросить цель ---
        for ent in alive_enemies:
            if not ent.get("in_combat"):
                continue  # только те, кто уже в бою
            target = ent.get("combat_target")
            # Цель defeated или слишком далеко → выходим из боя
            target_ok = (target and not target.get("defeated") and
                         not target.get("_looted"))
            if target_ok:
                dx = target["x"] - ent["x"]
                dy = target["y"] - ent["y"]
                target_ok = (dx * dx + dy * dy) ** 0.5 <= max_combat_range
            if not target_ok:
                ent["in_combat"] = False
                ent["combat_target"] = None
                ent["ai_state"] = "chase"
                ent["aggro_reason"] = "social"

        # --- Игрок: выбрать ближайшего врага или выйти из боя ---
        if player_ent and player_ent.get("in_combat") and not player_ent.get("defeated"):
            stance = player_ent.get("stance", "aggressive")
            current_target = player_ent.get("combat_target")
            target_ok = False
            if current_target and not current_target.get("defeated"):
                dx = current_target["x"] - player_ent["x"]
                dy = current_target["y"] - player_ent["y"]
                target_ok = (dx * dx + dy * dy) ** 0.5 <= max_combat_range
            if not target_ok and stance != "passive":
                alive = [e for e in alive_enemies
                         if e.get("in_combat") and e.get("creature") and e["creature"].is_alive]
                if alive:
                    closest = min(alive, key=lambda e:
                        ((e["x"] - player_ent["x"])**2 + (e["y"] - player_ent["y"])**2)**0.5)
                    current_target = closest
                    target_ok = True
                else:
                    current_target = None
                    target_ok = False
            if target_ok:
                player_ent["combat_target"] = current_target
            else:
                player_ent["in_combat"] = False
                player_ent["combat_target"] = None

    def _update_combat_facing(self):
        """Повернуть всех бойцов лицом к их цели."""
        for ent in self._entities:
            if ent.get("type") not in ("enemy", "boss") or ent.get("defeated"):
                continue
            target = ent.get("combat_target")
            if not target or target.get("defeated"):
                continue
            dx = target["x"] - ent["x"]
            dy = target["y"] - ent["y"]
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 1:
                ent["dir_x"] = dx / dist
                ent["dir_y"] = dy / dist

    def _show_combat_indicator(self) -> None:
        """Показать/обновить индикатор боя на экране."""
        if not self._combat_status_label:
            from kivy.uix.label import Label
            self._combat_status_label = Label(
                text="⚔ БОЙ",
                size_hint=(None, None),
                size=(dp(100), dp(30)),
                font_size=dp(18),
                bold=True,
                color=(1, 0.3, 0.1, 1),
                pos=(dp(20), self.height - dp(80)),
            )
            self.layout.add_widget(self._combat_status_label)
        else:
            self._combat_status_label.opacity = 1

    def _hide_combat_indicator(self) -> None:
        """Скрыть индикатор боя."""
        if self._combat_status_label:
            self._combat_status_label.opacity = 0

    def _add_damage_label(self, world_x, world_y, text, color, is_crit=False):
        """Создать плавающий Label с текстом урона в screen-координатах."""
        from kivy.uix.label import Label
        from kivy.clock import Clock

        sx, sy = self._world_to_screen(world_x, world_y)
        font_sz = dp(18) if is_crit else dp(14)
        label = Label(
            text=text,
            size_hint=(None, None),
            font_size=font_sz,
            bold=True,
            color=color,
            halign="center",
            valign="middle",
        )
        label.texture_update()
        label.size = (label.texture.width, label.texture.height)
        label.pos = (sx - label.width / 2, sy - label.height / 2)
        label.opacity = 1.0
        self.layout.add_widget(label)
        self._damage_labels.append({
            "widget": label,
            "timer": 1.2,
            "float_y": 0.0,
            "initial_y": sy,
        })

    def _update_damage_labels(self):
        """Обновить позицию/прозрачность плавающих Label урона, удалить истёкшие."""
        dt = 1.0 / 60.0
        to_remove = []
        for dl in self._damage_labels:
            dl["timer"] -= dt
            dl["float_y"] += dt * dp(60)
            label = dl["widget"]
            # Плывём вверх
            label.pos = (
                label.pos[0],
                dl["initial_y"] + dl["float_y"],
            )
            # Затухание
            if dl["timer"] < 0.3:
                label.opacity = max(0, dl["timer"] / 0.3)
            if dl["timer"] <= 0:
                to_remove.append(dl)

        for dl in to_remove:
            if dl["widget"] in self.layout.children:
                self.layout.remove_widget(dl["widget"])
            self._damage_labels.remove(dl)

        # Обработать damage_numbers из entity
        all_ents = list(self._entities) + \
            ([self._player_entity] if self._player_entity else [])
        for ent in all_ents:
            dns = ent.get("damage_numbers", [])
            for dn in dns:
                if dn.get("_spawned"):
                    continue
                dn["_spawned"] = True
                self._add_damage_label(
                    dn["x"], dn["y"],
                    dn["text"],
                    dn["color"],
                    is_crit="⨯" in dn.get("text", ""),
                )

    def _update_rt_combat(self, dt):
        """Real-time combat tick: readiness, атаки, блоки, урон."""
        # Собираем всех combatants
        combatants = []
        player_ent = self._get_player_entity()
        if player_ent and player_ent.get("in_combat") and not player_ent.get("defeated"):
            combatants.append(player_ent)
        for ent in self._entities:
            if ent.get("in_combat") and not ent.get("defeated") and ent.get("type") in ("enemy", "boss"):
                combatants.append(ent)

        for ent in combatants:
            if ent.get("stun_timer", 0) > 0 or ent.get("defeated"):
                continue

            phase = ent.get("attack_phase", "idle")
            creature = ent.get("creature") or ent.get("_player_ref")
            target = ent.get("combat_target")
            if not creature or not creature.is_alive:
                continue

            # Timer decays
            if ent.get("block_flash_timer", 0) > 0:
                ent["block_flash_timer"] = max(0, ent["block_flash_timer"] - dt)
            if ent.get("stagger_timer", 0) > 0:
                ent["stagger_timer"] = max(0, ent["stagger_timer"] - dt)
                if ent["stagger_timer"] <= 0:
                    ent["staggered"] = False

            # Clean up damage numbers
            if "damage_numbers" in ent:
                for dn in ent["damage_numbers"]:
                    dn["timer"] -= dt
                    dn["float_y"] += dt * dp(40)
                ent["damage_numbers"] = [dn for dn in ent["damage_numbers"] if dn["timer"] > 0]

            # ---- IDLE: копим readiness + постоянное сближение с целью ----
            if phase == "idle":
                # Anti-freeze: если слишком долго в idle без атаки — форсируем
                idle_time = ent.setdefault("_idle_time", 0.0) + dt
                ent["_idle_time"] = idle_time

                # Постоянное сближение с целью (враги всегда пытаются подойти вплотную)
                min_melee_dist = dp(5)  # минимальная дистанция "вплотную"
                if target and not target.get("defeated"):
                    dx = target["x"] - ent["x"]
                    dy = target["y"] - ent["y"]
                    dist_to_target = (dx * dx + dy * dy) ** 0.5
                    # Только враги двигаются к цели, игрок ходит сам
                    if ent.get("type") != "player" and dist_to_target > min_melee_dist:
                        close_speed = dp(90) * dt  # ×0.5 — в бою враги медленнее (напряжение)
                        step = min(close_speed, dist_to_target - min_melee_dist)
                        ent["x"] += (dx / max(1, dist_to_target)) * step
                        ent["y"] += (dy / max(1, dist_to_target)) * step
                        ent["rest_x"] = ent["x"]
                        ent["rest_y"] = ent["y"]
                        # Синхронизируем нормализованные координаты, чтобы
                        # при возврате из боя перехода не было рывка
                        w = max(1, self.width)
                        h = max(1, self.height)
                        ent["x_norm"] = ent["x"] / w
                        ent["y_norm"] = ent["y"] / h

                # Readiness заряжается всегда
                self._tick_readiness(ent, creature, dt)

                # Готовность атаковать — только если есть цель и достаточно близко
                if ent["readiness"] >= 1.0:
                    if target and not target.get("defeated"):
                        dx2 = target["x"] - ent["x"]
                        dy2 = target["y"] - ent["y"]
                        max_attack_range = ent.get("radius", dp(12)) + (target["radius"] if target else dp(12)) + dp(30)
                        if (dx2 * dx2 + dy2 * dy2) ** 0.5 <= max_attack_range * 1.5:
                            ent["_idle_time"] = 0.0
                            self._start_attack_windup(ent, creature, target)
                        else:
                            ent["readiness"] = 0.8  # слишком далеко — ждём сближения

            # ---- WINDUP: оттягивание назад ----
            elif phase == "windup":
                ent["phase_timer"] += dt
                progress = min(1.0, ent["phase_timer"] / ent.get("phase_duration", 0.3))
                # Ease-out: оттягиваемся назад от цели
                tween_back = 1.0 - math.cos(progress * math.pi / 2)
                pull_distance = dp(15) * tween_back
                if target:
                    dx = ent["origin_x"] - target["x"]
                    dy = ent["origin_y"] - target["y"]
                    dist = max(1, (dx * dx + dy * dy) ** 0.5)
                    ent["x"] = ent["origin_x"] + (dx / dist) * pull_distance
                    ent["y"] = ent["origin_y"] + (dy / dist) * pull_distance
                if progress >= 1.0:
                    self._resolve_attack(ent, creature, target)
                    ent["attack_phase"] = "strike"
                    ent["phase_timer"] = 0.0
                    ent["origin_x"] = ent["x"]
                    ent["origin_y"] = ent["y"]

            # ---- STRIKE: рывок вперёд ----
            elif phase == "strike":
                ent["phase_timer"] += dt
                progress = min(1.0, ent["phase_timer"] / ent.get("phase_duration", 0.15))
                tween_forward = 1.0 - (1.0 - progress) ** 2  # ease-in
                lunge_distance = dp(25) * tween_forward
                if target:
                    dx = target["x"] - ent["origin_x"]
                    dy = target["y"] - ent["origin_y"]
                    dist = max(1, (dx * dx + dy * dy) ** 0.5)
                    ent["x"] = ent["origin_x"] + (dx / dist) * lunge_distance
                    ent["y"] = ent["origin_y"] + (dy / dist) * lunge_distance
                if progress >= 1.0:
                    ent["attack_phase"] = "recovery"
                    ent["phase_timer"] = 0.0
                    ent["origin_x"] = ent["x"]
                    ent["origin_y"] = ent["y"]

            # ---- RECOVERY: возврат в нейтраль ----
            elif phase == "recovery":
                ent["phase_timer"] += dt
                progress = min(1.0, ent["phase_timer"] / ent.get("phase_duration", 0.25))
                rest_x = ent.get("rest_x", ent["origin_x"])
                rest_y = ent.get("rest_y", ent["origin_y"])
                ent["x"] = ent["origin_x"] + (rest_x - ent["origin_x"]) * progress
                ent["y"] = ent["origin_y"] + (rest_y - ent["origin_y"]) * progress
                if progress >= 1.0:
                    ent["attack_phase"] = "idle"
                    ent["readiness"] = 0.0
                    ent["blocked"] = False

            # ---- KNOCKBACK: отлетание после удара (только у цели) ----
            elif phase == "knockback":
                ent["phase_timer"] += dt
                progress = min(1.0, ent["phase_timer"] / ent.get("phase_duration", 0.25))
                tween = 1.0 - (1.0 - progress) ** 3  # ease-out: быстро в начале, замедление к концу
                if target:
                    dx = ent["x"] - target["x"]
                    dy = ent["y"] - target["y"]
                    dist = max(1, (dx * dx + dy * dy) ** 0.5)
                    kb_distance = dp(20) * tween
                    ent["x"] = ent["origin_x"] + (dx / dist) * kb_distance
                    ent["y"] = ent["origin_y"] + (dy / dist) * kb_distance
                if progress >= 1.0:
                    ent["attack_phase"] = "idle"
                    ent["readiness"] = 0.0

    def _tick_readiness(self, ent, creature, dt):
        """Тикает readiness (0→1) в зависимости от ловкости и веса оружия."""
        dex = getattr(creature, "dexterity", 5)
        weapon_weight = 0.0
        weapon = getattr(creature, "weapon", None)
        if weapon and hasattr(weapon, "weight"):
            weapon_weight = weapon.weight

        # Базовая скорость: ~1.5 сек при dex=5 без оружия
        base_recovery = 1.5
        dex_bonus = max(0, dex - 5) * 0.04        # -0.04 сек за единицу dex сверх 5
        weight_penalty = weapon_weight * 0.15      # +0.15 сек за единицу веса

        recovery_time = max(0.4, base_recovery - dex_bonus + weight_penalty)
        ent["readiness"] = min(1.0, ent["readiness"] + dt / recovery_time)
        ent["readiness_visual"] = ent["readiness"]

    def _start_attack_windup(self, ent, creature, target):
        """Начать фазу замаха."""
        dex = getattr(creature, "dexterity", 5)
        weapon_weight = 0.0
        weapon = getattr(creature, "weapon", None)
        if weapon and hasattr(weapon, "weight"):
            weapon_weight = weapon.weight

        # Длительность замаха: лёгкое оружие = быстрый замах
        windup_time = max(0.15, 0.4 - (dex - 5) * 0.015 + weapon_weight * 0.04)
        strike_time = max(0.08, 0.15)
        recovery_time = max(0.15, 0.3 - (dex - 5) * 0.01)

        ent["attack_phase"] = "windup"
        ent["phase_timer"] = 0.0
        ent["phase_duration"] = windup_time
        ent["origin_x"] = ent["x"]
        ent["origin_y"] = ent["y"]
        ent["rest_x"] = ent["x"]
        ent["rest_y"] = ent["y"]
        # Сохраняем длительности следующих фаз
        ent["_strike_duration"] = strike_time
        ent["_recovery_duration"] = recovery_time

    def _resolve_attack(self, attacker_ent, attacker_creature, target_ent):
        """Момент удара: защитник кидает кубик на блок."""
        if not target_ent or target_ent.get("defeated"):
            attacker_ent["blocked"] = True
            return

        target_creature = target_ent.get("creature") or target_ent.get("_player_ref")
        if not target_creature or not target_creature.is_alive:
            attacker_ent["blocked"] = True
            return

        # Кубик защиты: шанс блока от защиты
        block_chance = target_creature.defense / (target_creature.defense + 30)
        blocked = random.random() < block_chance

        # Проверка пассивной стойки: если игрок в passive и враг его атакует
        player_ent = self._get_player_entity()
        if target_ent.get("_is_player") and target_ent.get("stance") == "passive":
            # В пассивной стойке игрок получает +15% к блоку
            block_chance = min(0.9, block_chance + 0.15)
            blocked = random.random() < block_chance

        if blocked:
            attacker_ent["blocked"] = True
            target_ent["block_flash_timer"] = 0.3
            # Буст readiness защитнику (инициатива переходит)
            target_ent["readiness"] = min(1.0, target_ent["readiness"] + 0.3)
            # Текст "БЛОК!" над защитником
            target_ent.setdefault("damage_numbers", []).append({
                "x": target_ent["x"],
                "y": target_ent["y"] + target_ent["radius"],
                "text": "БЛОК!",
                "timer": 0.8,
                "float_y": 0.0,
                "color": (0.4, 0.8, 1, 1),
            })
        else:
            from core.combat.damage import apply_critical, roll_raw_damage
            raw = roll_raw_damage(attacker_creature.damage, variance=(-2, 3))
            crit_chance = getattr(attacker_creature, "critical_chance", 0.04)
            raw, is_crit = apply_critical(raw, crit_chance)
            actual_damage = target_creature.take_damage(raw)

            # Knockback
            target_ent["attack_phase"] = "knockback"
            target_ent["phase_timer"] = 0.0
            target_ent["phase_duration"] = 0.3
            target_ent["origin_x"] = target_ent["x"]
            target_ent["origin_y"] = target_ent["y"]
            target_ent["staggered"] = True
            target_ent["stagger_timer"] = 0.3

            # Floating damage number
            crit_mark = "⨯" if is_crit else ""
            target_ent.setdefault("damage_numbers", []).append({
                "x": target_ent["x"],
                "y": target_ent["y"] + target_ent["radius"],
                "text": f"-{actual_damage}{crit_mark}",
                "timer": 1.0,
                "float_y": 0.0,
                "color": (1, 0.2, 0.1, 1) if is_crit else (1, 0.8, 0.2, 1),
            })

            # Смерть
            if not target_creature.is_alive:
                target_ent["defeated"] = True
                target_ent["death_timer"] = 0.5
                if target_ent.get("type") in ("enemy", "boss"):
                    self._defeated_enemies.add(target_ent["id"])

        # После удара устанавливаем длительности следующих фаз
        attacker_ent["phase_duration"] = attacker_ent.get("_strike_duration", 0.15)

    def _check_combat_end(self):
        """Проверить, закончился ли бой."""
        alive_enemies = [e for e in self._entities
                         if e.get("type") in ("enemy", "boss") and not e["defeated"]]

        if not alive_enemies:
            # Все враги мертвы → победа
            self._end_rt_combat(victory=True)
            return

        # Проверка: игрок убежал слишком далеко
        max_combat_range = dp(350)
        player_ent = self._get_player_entity()
        if player_ent:
            far_enemies = all(
                ((e["x"] - player_ent["x"])**2 + (e["y"] - player_ent["y"])**2)**0.5 > max_combat_range
                for e in alive_enemies
            )
            if far_enemies:
                self._end_rt_combat(victory=False, escaped=True)

    def _end_rt_combat(self, victory=False, escaped=False):
        """Завершить real-time бой: очистка, дроп, XP."""
        # Скрываем индикатор боя
        self._hide_combat_indicator()

        # Сброс состояния у всех
        for ent in self._entities:
            if ent.get("in_combat"):
                ent["in_combat"] = False
                ent["combat_target"] = None
                ent["attack_phase"] = "idle"
                ent["readiness"] = 0.0

        player_ent = self._get_player_entity()
        if player_ent:
            player_ent["in_combat"] = False
            player_ent["combat_target"] = None
            player_ent["attack_phase"] = "idle"
            player_ent["readiness"] = 0.0

        if victory:
            # Собираем XP и лут с убитых врагов
            app = App.get_running_app()
            player = app.game.player if app.game else None
            if player:
                total_xp = 0
                total_coins = 0
                for ent in self._entities:
                    creature = ent.get("creature")
                    if creature and ent.get("defeated") and ent.get("type") in ("enemy", "boss"):
                        total_xp += creature.base_xp
                        total_coins += creature.coins
                        # Лут генерируется через существующую систему
                if total_xp > 0:
                    player.add_experience(total_xp)
                if total_coins > 0:
                    player.coins += total_coins
                player.battles_fought += 1
                player.enemies_defeated += 1

        if escaped:
            # При побеге НЕ восстанавливаем здоровье — враги остаются ранеными
            # (чтобы при возвращении бой продолжился с теми же HP)
            pass

    def prepare_defeat_state(self, from_rt=False):
        """Подготовить карту после поражения: стан врагам, бессмертие игроку."""
        if from_rt:
            # RT combat: станим ВСЕХ живых врагов
            for ent in self._entities:
                if ent.get("type") in ("enemy", "boss") and not ent["defeated"]:
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
            return

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
            self._player_invincible_timer = INVINCIBILITY_DURATION
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

        # При возврате из боя нужно удалить только побеждённого босса, остальных врагов не трогать
        if victory and self._current_battle_group:
            for ent in self._current_battle_group:
                if ent.get("type") == "boss":
                    ent["defeated"] = True
                    self._entities = [e for e in self._entities if e.get("type") != "boss"]
                    if hasattr(self, '_drawing_widget') and self._drawing_widget:
                        self._draw_game()
                    break

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
                etype = ent.get("type")
                r = ent["radius"]

                # --- RIP: отрисовка трупа ---
                if ent["defeated"]:
                    ex, ey = ent["x"], ent["y"]
                    Color(0.4, 0.4, 0.4, 0.6)
                    Ellipse(pos=(ex - r * 0.6, ey - r * 0.6), size=(r * 1.2, r * 1.2))
                    Color(0.3, 0.3, 0.3, 0.8)
                    Line(circle=(ex, ey, r * 0.6), width=1.5)
                    # Красный крест
                    cr = r * 0.5
                    Color(0.8, 0.1, 0.1, 0.7)
                    Line(points=[ex - cr, ey, ex + cr, ey], width=2)
                    Line(points=[ex, ey - cr, ex, ey + cr], width=2)
                    # Имя покойника
                    if not ent.get("_corpse_label"):
                        from kivy.uix.label import Label
                        lbl = Label(text=ent.get("name", "Труп"), font_size=dp(10),
                                    size_hint=(None, None), size=(dp(80), dp(16)),
                                    color=(0.5, 0.5, 0.5, 0.7), halign="center")
                        self.layout.add_widget(lbl)
                        ent["_corpse_label"] = lbl
                    else:
                        lbl = ent["_corpse_label"]
                        sx, sy = self._world_to_screen(ex, ey)
                        lbl.pos = (sx - dp(40), sy + dp(10))
                    continue

                # --- живые ---
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

                # Combat glow ring + HP bar для бойцов in_combat
                if ent.get("in_combat") and not ent.get("defeated") and etype in ("enemy", "boss"):
                    creature = ent.get("creature")
                    if creature:
                        hp_ratio = creature.health / max(1, creature.max_health)
                        hp_ratio = max(0, min(1, hp_ratio))
                        bar_w = r * 2.0
                        bar_h = dp(4)
                        bar_x = ent["x"] - r
                        bar_y = ent["y"] - r - bar_h - dp(2)
                        # Фон бара
                        Color(0.3, 0.1, 0.1, 0.8)
                        Rectangle(pos=(bar_x, bar_y), size=(bar_w, bar_h))
                        # Здоровье
                        if hp_ratio > 0.5:
                            Color(0.2, 0.8, 0.2, 0.9)
                        elif hp_ratio > 0.25:
                            Color(0.9, 0.7, 0.1, 0.9)
                        else:
                            Color(0.9, 0.1, 0.1, 0.9)
                        Rectangle(pos=(bar_x, bar_y), size=(bar_w * hp_ratio, bar_h))
                    # Combat aura
                    Color(1, 0.3, 0.1, 0.25 + 0.15 * math.sin(self._total_time * 4))
                    Ellipse(pos=(ent["x"] - r * 1.4, ent["y"] - r * 1.4), size=(r * 2.8, r * 2.8))

            pr = self._player_radius()
            px, py = self._player_pos
            player_ent = self._player_entity

            # Игрок теперь рисуется кружком, как и враги
            if self._is_player_sneaking():
                Color(0.3, 0.8, 0.4, 0.85)
            elif player_ent and player_ent.get("in_combat"):
                Color(0.3, 0.5, 1, 0.9)  # синий в бою
            else:
                Color(0.3, 0.6, 1, 0.8)  # обычный синий
            Ellipse(pos=(px - pr, py - pr), size=(pr * 2, pr * 2))
            Color(0.2, 0.4, 0.8, 1)
            Line(circle=(px, py, pr), width=2)

            # Боевая аура игрока (пульсирующая)
            if player_ent and player_ent.get("in_combat"):
                Color(0.2, 0.4, 1, 0.25 + 0.15 * math.sin(self._total_time * 4))
                Ellipse(pos=(px - pr * 1.4, py - pr * 1.4), size=(pr * 2.8, pr * 2.8))

            # Короткая метка имени над игроком
            if self._player_label:
                label_x, label_y = self._world_to_screen(self._player_pos[0], self._player_pos[1])
                screen_radius = pr * self._camera_zoom()
                self._player_label.pos = (
                    label_x - self._player_label.width / 2,
                    label_y + screen_radius + dp(5),
                )

        # --- PLAYER HP BAR (in combat) ---
        player_ent = self._player_entity
        if player_ent and player_ent.get("in_combat"):
            player_ref = player_ent.get("_player_ref")
            if player_ref:
                pr_actual = self._player_radius()
                hp_ratio = player_ref.health / max(1, player_ref.max_health)
                hp_ratio = max(0, min(1, hp_ratio))
                bar_w = pr_actual * 2.0
                bar_h = dp(5)
                bar_x = self._player_pos[0] - pr_actual
                bar_y = self._player_pos[1] - pr_actual - bar_h - dp(3)
                Color(0.3, 0.1, 0.1, 0.8)
                Rectangle(pos=(bar_x, bar_y), size=(bar_w, bar_h))
                if hp_ratio > 0.5:
                    Color(0.2, 0.8, 0.2, 0.9)
                elif hp_ratio > 0.25:
                    Color(0.9, 0.7, 0.1, 0.9)
                else:
                    Color(0.9, 0.1, 0.1, 0.9)
                Rectangle(pos=(bar_x, bar_y), size=(bar_w * hp_ratio, bar_h))

        # --- ATTACK LINES (кто кого бьёт) ---
        all_combat_ents = [e for e in self._entities if not e.get("defeated")] + \
            ([self._player_entity] if self._player_entity and not self._player_entity.get("defeated") else [])
        for ent in all_combat_ents:
            if ent.get("type") == "zone" or ent.get("type") == "npc":
                continue
            phase = ent.get("attack_phase", "idle")
            target = ent.get("combat_target")
            if not target or target.get("defeated"):
                continue
            if phase in ("windup", "strike"):
                ex, ey = ent["x"], ent["y"]
                tx, ty = target["x"], target["y"]
                if phase == "windup":
                    progress = min(1.0, ent.get("phase_timer", 0) / max(0.01, ent.get("phase_duration", 0.3)))
                    alpha = 0.3 + progress * 0.5
                    Color(1, 0.8, 0.1, alpha)
                    Line(points=[ex, ey, tx, ty], width=1.5 + progress)
                elif phase == "strike":
                    progress = min(1.0, ent.get("phase_timer", 0) / max(0.01, ent.get("phase_duration", 0.15)))
                    alpha = 0.5 + (1 - progress) * 0.4
                    Color(1, 0.2, 0.1, alpha)
                    Line(points=[ex, ey, tx, ty], width=2.5 - progress)

        # --- COMBAT VISUAL EFFECTS (над entity) ---
        combat_entities = [e for e in self._entities if not e.get("defeated")] + \
            ([self._player_entity] if self._player_entity and not self._player_entity.get("defeated") else [])
        for ent in combat_entities:
            if ent.get("type") == "zone" or ent.get("type") == "npc":
                continue
            cx, cy = ent["x"], ent["y"]
            er = ent["radius"]
            scx, scy = self._world_to_screen(cx, cy)

            # Readiness bar (под кружком, только в бою)
            if ent.get("in_combat"):
                read = ent.get("readiness", 0)
                if 0 < read < 1.0:
                    Color(0.3, 0.8, 1, 0.8)
                    bar_w = er * 1.6
                    bar_h = dp(3)
                    bar_x = cx - bar_w / 2
                    bar_y = cy - er - bar_h - dp(1)
                    Rectangle(pos=(bar_x, bar_y), size=(bar_w * read, bar_h))

            # Block flash (жёлтая вспышка)
            bft = ent.get("block_flash_timer", 0)
            if bft > 0:
                alpha = min(0.5, bft * 1.5)
                Color(1, 1, 0.4, alpha)
                Ellipse(pos=(cx - er * 0.8, cy - er * 0.8), size=(er * 1.6, er * 1.6))

            # Stagger (красный оттенок под кружком)
            if ent.get("staggered") and ent.get("stagger_timer", 0) > 0:
                Color(1, 0.2, 0.2, 0.3)
                Ellipse(pos=(cx - er, cy - er), size=(er * 2, er * 2))

            # Floating damage markers (только визуальные вспышки, текст через Label)
            for dn in ent.get("damage_numbers", []):
                alpha = max(0, min(1.0, dn["timer"] / 0.3))
                flash_r = dp(4 + abs(dn.get("float_y", 0)) / dp(15))
                Color(*dn["color"][:3], alpha * 0.5)
                Ellipse(pos=(cx - flash_r, cy + dn.get("float_y", 0) - flash_r), size=(flash_r * 2, flash_r * 2))
                if "⨯" in dn.get("text", ""):
                    Color(1, 1, 1, alpha * 0.5)
                    cr = dp(8)
                    fy = dn.get("float_y", 0)
                    Line(points=[cx - cr, cy - cr + fy, cx + cr, cy + cr + fy], width=1.5)
                    Line(points=[cx + cr, cy - cr + fy, cx - cr, cy + cr + fy], width=1.5)

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
        if player and self._is_ambush:
            player._ambush_defeated_set = set(self._defeated_enemies)

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
        self._clear_all_barks()
        self._hide_ambush_exit_block_notification()
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

        if self._is_ambush and not self._can_exit_ambush():
            self._show_ambush_exit_block_notification()
            return

        app = App.get_running_app()
        self._save_player_state()
        self._stop_loop()
        self._returning_from_battle = False
        self._player_invincible_timer = 0
        self._paused = False

        if self._is_ambush:
            self._is_ambush = False
            self._ambush_enemies_data = None
            app.return_to_local_location = False
            player = app.game.player if app.game else None
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
            return

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

    def _can_exit_ambush(self) -> bool:
        if self._ambush_total_enemies <= 0:
            return True
        defeated_count = len(self._defeated_enemies)
        return defeated_count >= self._ambush_total_enemies / 2

    def _show_ambush_exit_block_notification(self) -> None:
        if self._ambush_exit_block_label:
            return
        defeated_count = len(self._defeated_enemies)
        needed = max(1, self._ambush_total_enemies // 2)
        remaining = max(0, needed - defeated_count)
        self._ambush_exit_block_label = Label(
            text=f'⚠️ Чтобы покинуть засаду, уничтожьте ещё {remaining} врагов (нужно {needed}/{self._ambush_total_enemies})',
            size_hint=(None, None),
            size=(dp(400), dp(35)),
            pos_hint={'right': 0.98, 'y': 0.02},
            font_size=dp(13),
            color=COLORS.get("warning", (1, 0.6, 0, 1)),
            halign='right',
            valign='middle',
        )
        self.layout.add_widget(self._ambush_exit_block_label)
        Clock.schedule_once(lambda dt: self._hide_ambush_exit_block_notification(), 4.0)

    def _hide_ambush_exit_block_notification(self) -> None:
        if self._ambush_exit_block_label:
            try:
                self.layout.remove_widget(self._ambush_exit_block_label)
            except Exception:
                pass
            self._ambush_exit_block_label = None

    def _trigger_ambush_starting_barks(self) -> None:
        for entity in self._entities:
            if entity.get("type") != "enemy" or entity.get("defeated"):
                continue
            if AMBUSH_SEARCH_BARKS:
                text = random.choice(AMBUSH_SEARCH_BARKS)
                self._spawn_bark_with_text(entity, text, duration=BARK_DURATION)

    def _spawn_bark_with_text(self, entity, text: str, duration: float = 3.5, is_alert: bool = False):
        if entity.get("bark_label"):
            self._remove_bark(entity)
        bark_label = Label(
            text=text,
            font_size=dp(11),
            color=(1, 0.85, 0.6, 1) if not is_alert else (1, 0.2, 0.2, 1),
            bold=False,
            size_hint=(None, None),
            halign='center',
            valign='middle'
        )
        bark_label.texture_update()
        bark_label.size = (bark_label.texture_size[0] + dp(16), bark_label.texture_size[1] + dp(8))
        with bark_label.canvas.before:
            Color(0.1, 0.1, 0.1, 0.65)
            bark_label.bg_rect = RoundedRectangle(size=bark_label.size, pos=bark_label.pos, radius=[dp(6)])
        bark_label.bind(pos=lambda inst, val: setattr(inst.bg_rect, 'pos', val))
        self.add_widget(bark_label)
        entity["bark_label"] = bark_label
        screen_x = entity["x"] * self._cam_scale.x + self._cam_translate.x
        screen_y = entity["y"] * self._cam_scale.y + self._cam_translate.y
        r_offset = self._enemy_radius() * self._cam_scale.y
        bark_label.center_x = screen_x
        bark_label.y = screen_y + r_offset + dp(12)
        old_timer = entity.get("_bark_timer_event")
        if old_timer:
            old_timer.cancel()
        entity["_bark_timer_event"] = Clock.schedule_once(lambda dt: self._remove_bark(entity), duration)

    def _init_bark_system(self):
        """Инициализация таймера системы реплик."""
        self._bark_timer = 0.0

    def _update_barks(self, dt):
        """Обновление позиций активных реплик и проверка шанса появления новых."""
        if self._paused:
            return

        # 1. Сначала обновляем позиции уже существующих реплик, чтобы они следовали за врагами
        for entity in self._entities:
            bark_label = entity.get("bark_label")
            if bark_label:
                # Переводим мировые координаты врага в экранные с учетом камеры (_cam_scale и _cam_translate)
                screen_x = entity["x"] * self._cam_scale.x + self._cam_translate.x
                screen_y = entity["y"] * self._cam_scale.y + self._cam_translate.y
                
                # Радиус врага с учетом масштаба камеры
                r_offset = self._enemy_radius() * self._cam_scale.y
                
                # Центрируем текст над головой
                bark_label.center_x = screen_x
                bark_label.y = screen_y + r_offset + dp(12)

        # 2. Каждые BARK_CHECK_INTERVAL секунд пытаемся заставить случайного врага заговорить
        self._bark_timer += dt
        if self._bark_timer >= BARK_CHECK_INTERVAL:
            self._bark_timer = 0.0
            
            # Берем только тех врагов, у кого сейчас нет активной реплики
            silent_entities = [e for e in self._entities if e.get("type") == "enemy" and not e.get("bark_label") and not e.get("defeated")]
            if silent_entities and random.random() < BARK_CHANCE_PER_CHECK:
                lucky_entity = random.choice(silent_entities)
                self._spawn_bark(lucky_entity)

    def _spawn_bark(self, entity, is_alert=False):
        """Создает текстовое облако над врагом. Поддерживает мирные фразы и тревогу."""
        creature = entity.get("creature")
        if not creature:
            return

        # Если у врага УЖЕ висит какая-то фраза, принудительно удаляем её,
        # чтобы старый текст не перекрывал срочную тревогу
        if entity.get("bark_label"):
            self._remove_bark(entity)

        creature = entity.get("creature")
        e_type = (creature.enemy_type.lower() if creature and hasattr(creature, "enemy_type") else "") or entity.get("name", "").lower()
        if "shaman" in e_type:
            creature_type = "shaman"
        elif "goblin" in e_type or "bog" in e_type or "болотник" in e_type:
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
        elif "wolf" in e_type or "волк" in entity.get("name", "").lower():
            creature_type = "wolf"
        elif "marauder" in e_type or "разведчик" in entity.get("name", "").lower() or "дезертир" in entity.get("name", "").lower():
            creature_type = "marauder"
        else:
            creature_type = "bandit"

        # Выбираем пул фраз и длительность в зависимости от ситуации
        if is_alert:
            barks = ENEMY_ALERT_BARKS.get(creature_type, ["Ага! Кто тут?!"])
            duration = 2.0  # Боевой клич висит чуть меньше (2 сек), чтобы не засорять экран в бою
        else:
            barks = ENEMY_BARKS.get(creature_type, ["..."])
            duration = BARK_DURATION

        text = random.choice(barks)

        # Создаем Kivy Label (стилизуем под тип реплики)
        bark_label = Label(
            text=text,
            font_size=dp(11),
            color=(1, 0.2, 0.2, 1) if is_alert else (1, 1, 1, 1), # Красный текст для тревоги
            bold=is_alert,                                       # Жирный для тревоги
            size_hint=(None, None),
            halign='center',
            valign='middle'
        )
        bark_label.texture_update()
        bark_label.size = (bark_label.texture_size[0] + dp(16), bark_label.texture_size[1] + dp(8))

        # Рисуем подложку
        with bark_label.canvas.before:
            if is_alert:
                Color(0.4, 0.0, 0.0, 0.75) # Темно-красный фон для паники
            else:
                Color(0.1, 0.1, 0.1, 0.6)  # Обычный полупрозрачный черный
            bark_label.bg_rect = RoundedRectangle(size=bark_label.size, pos=bark_label.pos, radius=[dp(6)])
        
        bark_label.bind(pos=lambda inst, val: setattr(inst.bg_rect, 'pos', val))

        self.add_widget(bark_label)
        entity["bark_label"] = bark_label

        # Позиционируем над головой
        screen_x = entity["x"] * self._cam_scale.x + self._cam_translate.x
        screen_y = entity["y"] * self._cam_scale.y + self._cam_translate.y
        r_offset = self._enemy_radius() * self._cam_scale.y
        bark_label.center_x = screen_x
        bark_label.y = screen_y + r_offset + dp(12)

        # Отменяем старый таймер, если есть, чтобы избежать преждевременного удаления
        old_timer = entity.get("_bark_timer_event")
        if old_timer:
            old_timer.cancel()

        # Ставим таймер удаления
        entity["_bark_timer_event"] = Clock.schedule_once(lambda dt: self._remove_bark(entity), duration)

    def _remove_bark(self, entity):
        """Безопасное удаление реплики с экрана."""
        # Отменяем запланированный таймер, если он ещё не сработал
        timer = entity.pop("_bark_timer_event", None)
        if timer:
            timer.cancel()
        bark_label = entity.pop("bark_label", None)
        if bark_label:
            self.remove_widget(bark_label)
            
    def _clear_all_barks(self):
        """Уничтожение всех бабблов при выходе из локации."""
        for entity in self._entities:
            self._remove_bark(entity)