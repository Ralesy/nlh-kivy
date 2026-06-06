#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Базовый экран проходимой локальной карты.

Поддерживает боевые локации (враги + боссы), город (зоны входа),
таверну (NPC) и магазин (торговец).
"""

import os
import random
from typing import Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
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
        self._update_event = None
        self._returning_from_battle = False
        self._active_zone = None
        self._move = {"up": False, "down": False, "left": False, "right": False}
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
        self._load_background()

        self._target_pos = None
        self._move = {"up": False, "down": False, "left": False, "right": False}
        self._entities = []
        self._current_entity = None
        self._active_zone = None
        self.btn_zone_action.opacity = 0
        self.btn_zone_action.text = "Войти"

        if self._returning_from_battle:
            pass
        else:
            player = app.game.player if app.game else None
            pos_key = self.scene_id
            if player and pos_key in getattr(player, "last_location_pos", {}):
                x_norm, y_norm = player.last_location_pos[pos_key]
                self._player_pos = [x_norm * self.width, y_norm * self.height]
            else:
                self._player_pos = [self.width * 0.5, self.height * 0.5]

        self._drawing_widget = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.layout.add_widget(self._drawing_widget)

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
            self.layout.add_widget(cover_background_image(bg_path))
        else:
            filler = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
            with filler.canvas.before:
                Color(*self._solid_background_color())
                filler._bg = Rectangle(pos=filler.pos, size=filler.size)
            filler.bind(
                pos=lambda w, v: setattr(filler._bg, "pos", w.pos),
                size=lambda w, v: setattr(filler._bg, "size", w.size),
            )
            self.layout.add_widget(filler)

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
                    "radius": dp(12),
                    "defeated": False,
                    "creature": creature,
                    "name": creature.name if creature else "Неизвестный",
                    "level": creature.level if creature else 1,
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
                "radius": dp(18),
                "defeated": False,
                "creature": boss_creature,
                "name": boss_cfg.name,
                "level": boss_creature.level,
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
                    "radius": dp(14),
                    "defeated": False,
                    "name": display_name,
                    "level": 0,
                }
            )

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

    def on_touch_down(self, touch):
        """Движение игрока и клики по UI."""
        if self._btn_exit and self._hit_widget(self._btn_exit, touch):
            self._on_exit_location()
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
        self._target_pos = [local_x, local_y]
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

    def _on_game_update(self, dt):
        """Игровой цикл: движение, столкновения, отрисовка."""
        if not self.scene_id:
            return

        self._sync_entity_positions()

        mx = (1 if self._move["right"] else 0) - (1 if self._move["left"] else 0)
        my = (1 if self._move["up"] else 0) - (1 if self._move["down"] else 0)
        if mx or my:
            self._target_pos = None
            length = (mx * mx + my * my) ** 0.5
            if length:
                speed = dp(200) * dt
                self._player_pos[0] += (mx / length) * speed
                self._player_pos[1] += (my / length) * speed
        elif self._target_pos:
            dx = self._target_pos[0] - self._player_pos[0]
            dy = self._target_pos[1] - self._player_pos[1]
            distance = (dx**2 + dy**2) ** 0.5
            if distance < dp(8):
                self._target_pos = None
            else:
                speed = dp(200) * dt
                move_dist = min(speed, distance)
                self._player_pos[0] += (dx / distance) * move_dist
                self._player_pos[1] += (dy / distance) * move_dist

        self._update_chasing_entities(dt)
        self._check_collisions()
        self._draw_game()

    def _update_chasing_entities(self, dt):
        """Враги медленно преследуют игрока."""
        speed = dp(30) * dt
        for ent in self._entities:
            if ent["defeated"] or ent.get("type") not in ("enemy",):
                continue
            dx = self._player_pos[0] - ent["x"]
            dy = self._player_pos[1] - ent["y"]
            dist = (dx**2 + dy**2) ** 0.5
            if dist > 0:
                step = min(speed, dist)
                ent["x"] += (dx / dist) * step
                ent["y"] += (dy / dist) * step
                ent["x_norm"] = ent["x"] / max(1, self.width)
                ent["y_norm"] = ent["y"] / max(1, self.height)

    def _check_collisions(self):
        """Столкновения игрока с сущностями."""
        player_r = dp(12)
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
                    self._start_battle(ent)
                    return

        if self._active_interact:
            ent = self._active_interact
            label = "Поговорить" if ent.get("action") == "dialogue" else "Открыть"
            self.btn_zone_action.text = f"{label}: {ent.get('name', '')}"
            self.btn_zone_action.opacity = 1
            self.btn_zone_action.pos = (
                ent["x"] - self.btn_zone_action.width / 2,
                ent["y"] + ent["radius"] + dp(10),
            )
        elif zone_near:
            self._active_zone = zone_near
            self.btn_zone_action.text = f"Войти: {zone_near.get('label', '...')}"
            self.btn_zone_action.opacity = 1
            self.btn_zone_action.pos = (
                zone_near["x"] - self.btn_zone_action.width / 2,
                zone_near["y"] + zone_near["radius"] + dp(10),
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
        self._save_player_state()
        self._stop_loop()
        from data.local_scenes import enter_local_scene

        enter_local_scene(app, target, parent_scene=self.scene_id)

    def _start_battle(self, entity):
        """Начать бой с врагом или боссом."""
        self._current_entity = entity
        self._returning_from_battle = True
        app = App.get_running_app()
        player = app.game.player if app.game else None

        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = []
            creatures = []
            for e in self._entities:
                if e.get("type") in ("enemy", "boss") and not e["defeated"]:
                    positions.append((e["x_norm"], e["y_norm"]))
                    creatures.append(e.get("creature"))
            if positions:
                player.last_enemy_positions[self.scene_id] = positions
                player.last_enemy_creatures[self.scene_id] = creatures

        self._stop_loop()
        creature = entity.get("creature")
        if not app.game or not player or not creature:
            return

        try:
            from systems.battle import Battlefield

            battlefield = Battlefield(player, [creature])
            app._battle_from_local_location = True
            app.battle_screen.from_local_location = True
            title = entity.get("name", creature.name)
            if entity.get("type") == "boss":
                title = f"👑 {title}"
            app.battle_screen.start_battle(battlefield, title)
            self.manager.current = "battle"
        except Exception:
            import traceback

            traceback.print_exc()

    def on_return_from_battle(self):
        """Возврат после боя."""
        app = App.get_running_app()
        player = app.game.player if app.game else None
        victory = (
            getattr(app, "battle_result", None) and app.battle_result.victory
        )

        if self._current_entity and victory:
            etype = self._current_entity.get("type")
            if etype == "boss":
                self._current_entity["defeated"] = True
                try:
                    if player and app.game:
                        app.game.autosave()
                except Exception:
                    pass
            elif etype == "enemy":
                self._current_entity["defeated"] = True
                self._defeated_enemies.add(self._current_entity["id"])

        self._current_entity = None
        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = [
                (e["x_norm"], e["y_norm"])
                for e in self._entities
                if e.get("type") in ("enemy", "boss") and not e["defeated"]
            ]
            if positions:
                player.last_enemy_positions[self.scene_id] = positions

        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self._on_game_update, 1 / 60)

    def _on_mouse_pos(self, window, pos):
        local_pos = self.to_local(*pos)
        for ent in self._entities:
            if ent["defeated"]:
                continue
            dx = local_pos[0] - ent["x"]
            dy = local_pos[1] - ent["y"]
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
                else:
                    Color(1, 0, 0, 0.7)
                    Ellipse(pos=(ent["x"] - r, ent["y"] - r), size=(r * 2, r * 2))
                    Color(0.8, 0, 0, 1)
                    Line(circle=(ent["x"], ent["y"], r), width=2)

            pr = dp(12)
            Color(1, 1, 0, 0.8)
            Ellipse(
                pos=(self._player_pos[0] - pr, self._player_pos[1] - pr),
                size=(pr * 2, pr * 2),
            )
            Color(1, 0.8, 0, 1)
            Line(circle=(self._player_pos[0], self._player_pos[1], pr), width=2)

            if self._player_label:
                self._player_label.pos = (
                    self._player_pos[0] - self._player_label.width / 2,
                    self._player_pos[1] + pr + dp(5),
                )

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
        app = App.get_running_app()
        player = app.game.player if app.game else None
        if player and self.scene_config and self.scene_config.scene_type == "combat":
            positions = [
                (e["x_norm"], e["y_norm"])
                for e in self._entities
                if e.get("type") in ("enemy", "boss") and not e["defeated"]
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

    def _on_exit_location(self, *_args):
        """Выход: на карту региона или в родительскую сцену."""
        app = App.get_running_app()
        self._save_player_state()
        self._stop_loop()

        if self.scene_config and self.scene_config.exit_target == "parent":
            parent = self.parent_scene_id or "city"
            from data.local_scenes import enter_local_scene

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

        self.scene_id = None
        self.location_id = None
        self._entities = []
        self._current_entity = None
        self._target_pos = None

        try:
            if player:
                app.game.autosave()
        except Exception:
            pass

        self.manager.current = "location_select"
