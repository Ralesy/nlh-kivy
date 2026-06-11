#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from kivy.graphics import Color, Ellipse, Line

from core.models.roam_zone import RoamZone, ZoneType
from core.models.roaming_token import (
    CONE_ANGLE_RAD,
    CONE_LENGTH,
    CONTACT_RADIUS,
    HEARING_RADIUS,
    EncounterType,
    RoamingToken,
    TokenBehaviour,
    TokenState,
)


def _token_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:03d}"


def _build_all_zones() -> List[RoamZone]:
    return [
        # ── Forest (0.18, 0.45) ──
        RoamZone(
            id="forest_wild",
            zone_type=ZoneType.WILD,
            center_x=0.18, center_y=0.45,
            radius=0.18, location_id="forest",
            color=(0.6, 0.2, 0.08, 0.08),
            enemy_types=["enemy_forest_wolf", "enemy_forest_bandit", "enemy_forest_raider", "enemy_forest_scout"],
            max_tokens=6,
        ),
        # ── Swamp (0.50, 0.60) ──
        RoamZone(
            id="swamp_wild",
            zone_type=ZoneType.WILD,
            center_x=0.50, center_y=0.60,
            radius=0.16, location_id="swamp",
            color=(0.25, 0.50, 0.15, 0.08),
            enemy_types=["enemy_swamp_goblin", "enemy_swamp_toad", "enemy_swamp_shamanic"],
            max_tokens=6,
        ),
        # ── Mines (0.70, 0.20) ──
        RoamZone(
            id="mines_wild",
            zone_type=ZoneType.WILD,
            center_x=0.70, center_y=0.20,
            radius=0.15, location_id="mines",
            color=(0.4, 0.25, 0.1, 0.08),
            enemy_types=["enemy_mines_orc", "enemy_mines_draugr", "enemy_mines_golem", "enemy_mines_skeleton", "enemy_mines_greyling"],
            max_tokens=6,
        ),
        # ── Mountains (0.70, 0.90) ──
        RoamZone(
            id="mountains_wild",
            zone_type=ZoneType.WILD,
            center_x=0.70, center_y=0.90,
            radius=0.15, location_id="mountains",
            color=(0.55, 0.45, 0.35, 0.08),
            enemy_types=["enemy_mountains_dragon", "enemy_mountains_specter", "enemy_mountains_troll", "enemy_mountains_giant", "enemy_mountains_drake"],
            max_tokens=6,
        ),
        # ── Safe zones ──
        RoamZone(
            id="city_safe", zone_type=ZoneType.SAFE,
            center_x=0.19, center_y=0.85, radius=0.08,
            location_id="city", color=(0.3, 0.5, 0.2, 0.10), max_tokens=0,
        ),
        RoamZone(
            id="village_safe", zone_type=ZoneType.SAFE,
            center_x=0.73, center_y=0.52, radius=0.08,
            location_id="village", color=(0.3, 0.5, 0.2, 0.10), max_tokens=0,
        ),
    ]


_ENEMY_ENCOUNTER_MAP: Dict[str, Tuple[EncounterType, str, Tuple[float, float, float]]] = {
    "enemy_forest_wolf":     (EncounterType.WILD_BEAST, "Лесной волк",     (0.9, 0.3, 0.2)),
    "enemy_forest_bandit":   (EncounterType.BANDIT,     "Лесной бандит",   (0.8, 0.2, 0.1)),
    "enemy_forest_raider":   (EncounterType.BANDIT,     "Лесной мародёр",  (0.7, 0.2, 0.15)),
    "enemy_forest_scout":    (EncounterType.BANDIT,     "Лесной разведчик", (0.6, 0.15, 0.1)),
    "enemy_swamp_goblin":    (EncounterType.WILD_BEAST, "Болотный гоблин", (0.3, 0.6, 0.2)),
    "enemy_swamp_toad":      (EncounterType.WILD_BEAST, "Гигантская жаба", (0.4, 0.5, 0.2)),
    "enemy_swamp_shamanic":  (EncounterType.WILD_BEAST, "Шаман болот",     (0.3, 0.4, 0.5)),
    "enemy_mines_orc":       (EncounterType.WILD_BEAST, "Орк шахтёр",      (0.5, 0.3, 0.1)),
    "enemy_mines_draugr":    (EncounterType.WILD_BEAST, "Драугр-шахтёр",   (0.4, 0.5, 0.5)),
    "enemy_mines_golem":     (EncounterType.WILD_BEAST, "Каменный голем",  (0.5, 0.4, 0.3)),
    "enemy_mines_skeleton":  (EncounterType.WILD_BEAST, "Скелет-шахтёр",   (0.6, 0.6, 0.6)),
    "enemy_mines_greyling":  (EncounterType.WILD_BEAST, "Серый гремлин",   (0.4, 0.4, 0.4)),
    "enemy_mountains_troll": (EncounterType.WILD_BEAST, "Горный тролль",   (0.6, 0.4, 0.2)),
    "enemy_mountains_specter":(EncounterType.WILD_BEAST,"Ледяной призрак", (0.5, 0.6, 0.9)),
    "enemy_mountains_dragon":(EncounterType.WILD_BEAST, "Горный дракон",   (0.8, 0.3, 0.1)),
    "enemy_mountains_giant": (EncounterType.WILD_BEAST, "Горный великан",  (0.6, 0.5, 0.3)),
    "enemy_mountains_drake": (EncounterType.WILD_BEAST, "Ледяной дракон",  (0.4, 0.6, 0.8)),
}

_PATROL_SPEED = 20.0
_CHASE_SPEED = 85.0
_VISION_RADIUS = CONE_LENGTH
_VISION_ANGLE = CONE_ANGLE_RAD
_HEARING_RADIUS = HEARING_RADIUS
_ALLY_RADIUS = 100.0
_SOCIAL_COMBAT_RADIUS = 90.0


class RoamingEntityManager:
    def __init__(self, map_world_width: float = 1280, map_world_height: float = 720):
        self._map_w: float = map_world_width
        self._map_h: float = map_world_height

        self.zones: List[RoamZone] = []
        self.tokens: List[RoamingToken] = []
        self._lockout_ids: set = set()

        # Canvas references for zone graphics
        self._zone_gfx: Dict[str, Tuple[Color, Ellipse, Color, Line]] = {}
        self._gfx_canvas = None
        self._tokens_spawned: bool = False
        self._removed_per_zone: Dict[str, int] = {}
        self._respawn_timer: float = 0.0

        self._build_default_zones()

    # ──────────────────────────────────────────────
    #  Map resize
    # ──────────────────────────────────────────────

    def set_map_size(self, w: float, h: float) -> None:
        self._map_w = w
        self._map_h = h
        if not self._tokens_spawned:
            self._spawn_all_tokens()
            self._tokens_spawned = True

    def _norm_to_world(self, nx: float, ny: float) -> Tuple[float, float]:
        return nx * self._map_w, ny * self._map_h

    def _norm_r_to_world(self, nr: float) -> float:
        return nr * max(self._map_w, self._map_h)

    # ──────────────────────────────────────────────
    #  Zone / token building
    # ──────────────────────────────────────────────

    def _build_default_zones(self) -> None:
        self.zones.clear()
        self.zones.extend(_build_all_zones())

    def _spawn_all_tokens(self) -> None:
        self.tokens.clear()
        for zone in self.zones:
            self._spawn_zone_tokens(zone)

    def _spawn_zone_tokens(self, zone: RoamZone) -> None:
        if zone.max_tokens <= 0 or not zone.enemy_types:
            return

        home_wx, home_wy = self._norm_to_world(zone.center_x, zone.center_y)
        home_wr = self._norm_r_to_world(zone.radius)

        squad_size = random.randint(2, 3)
        num_squads = max(1, zone.max_tokens // squad_size)
        token_index = 0

        for squad_idx in range(num_squads):
            if token_index >= zone.max_tokens:
                break
            squad_id = f"{zone.id}_squad_{squad_idx:03d}"

            for member_idx in range(squad_size):
                if token_index >= zone.max_tokens:
                    break
                etype = random.choice(zone.enemy_types)
                meta = _ENEMY_ENCOUNTER_MAP.get(
                    etype, (EncounterType.WILD_BEAST, "Неизвестный", (0.5, 0.5, 0.5))
                )
                encounter_type, name, color = meta

                if member_idx == 0:
                    px, py = zone.random_point_in_zone()
                else:
                    angle = random.uniform(0.0, 6.2832)
                    offset = random.uniform(15.0, 40.0)
                    px = first_px + offset * math.cos(angle) / max(1.0, self._map_w)
                    py = first_py + offset * math.sin(angle) / max(1.0, self._map_h)
                    px = max(0.01, min(0.99, px))
                    py = max(0.01, min(0.99, py))

                wx, wy = self._norm_to_world(px, py)

                if member_idx == 0:
                    first_px, first_py = px, py

                token = RoamingToken(
                    token_id=_token_id(zone.id, token_index),
                    enemy_type=etype,
                    encounter_type=encounter_type,
                    zone_id=zone.id,
                    x=wx, y=wy,
                    home_x=home_wx, home_y=home_wy,
                    home_radius=home_wr,
                    name=name,
                    behaviour=TokenBehaviour.RANDOM_WALK,
                    color=(*color, 1.0),
                    vision_radius=_VISION_RADIUS,
                    vision_angle=_VISION_ANGLE,
                    hearing_radius=_HEARING_RADIUS,
                    patrol_speed=_PATROL_SPEED,
                    chase_speed=_CHASE_SPEED,
                    squad_id=squad_id,
                    is_squad_leader=(member_idx == 0),
                )
                self.tokens.append(token)
                token_index += 1

    # ──────────────────────────────────────────────
    #  Graphics lifecycle
    # ──────────────────────────────────────────────

    def init_graphics(self, canvas) -> None:
        self._gfx_canvas = canvas
        self._init_zone_graphics()
        for token in self.get_active_tokens():
            token.init_graphics(canvas)

    def _init_zone_graphics(self) -> None:
        if self._gfx_canvas is None:
            return
        for zone in self.zones:
            if zone.max_tokens <= 0:
                continue
            key = zone.id
            if key in self._zone_gfx:
                continue
            cx, cy = self._norm_to_world(zone.center_x, zone.center_y)
            r = self._norm_r_to_world(zone.radius)
            with self._gfx_canvas:
                fill_col = Color(*zone.color)
                fill_ell = Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                border_col = Color(zone.color[0], zone.color[1], zone.color[2], 0.18)
                border_line = Line(circle=(cx, cy, r), width=2)
            self._zone_gfx[key] = (fill_col, fill_ell, border_col, border_line)

    def update_graphics(self) -> None:
        self._update_zone_graphics()
        for token in self.get_active_tokens():
            token.update_graphics(alerted=token.is_chasing)

    def _update_zone_graphics(self) -> None:
        for zone in self.zones:
            pair = self._zone_gfx.get(zone.id)
            if pair is None:
                continue
            _, ell, _, border_line = pair
            cx, cy = self._norm_to_world(zone.center_x, zone.center_y)
            r = self._norm_r_to_world(zone.radius)
            ell.pos = (cx - r, cy - r)
            ell.size = (r * 2, r * 2)
            border_line.circle = (cx, cy, r)

    def destroy_graphics(self) -> None:
        if self._gfx_canvas is None:
            return
        for token in self.tokens:
            token.destroy_graphics(self._gfx_canvas)
        for fill_col, fill_ell, border_col, border_line in self._zone_gfx.values():
            try:
                self._gfx_canvas.remove(fill_col)
            except (ValueError, AttributeError):
                pass
            try:
                self._gfx_canvas.remove(fill_ell)
            except (ValueError, AttributeError):
                pass
            try:
                self._gfx_canvas.remove(border_col)
            except (ValueError, AttributeError):
                pass
            try:
                self._gfx_canvas.remove(border_line)
            except (ValueError, AttributeError):
                pass
        self._zone_gfx.clear()
        self._gfx_canvas = None

    # ──────────────────────────────────────────────
    #  AI update
    # ──────────────────────────────────────────────

    def update(
        self,
        dt: float,
        player_x: float,
        player_y: float,
        player_is_noisy: bool = False,
        is_sneaking: bool = False,
    ) -> Optional[dict]:
        ai_dt = min(dt, 0.1)
        self._update_ai(ai_dt, player_x, player_y, player_is_noisy)
        self._update_squad_movement(ai_dt)

        self._check_zone_proximity(player_x, player_y, is_sneaking)
        self._check_zone_exit_reset(player_x, player_y)

        self._respawn_timer += ai_dt
        if self._respawn_timer >= 10.0:
            self._respawn_timer = 0.0
            self._try_respawn()

        return self._check_encounter_collisions(player_x, player_y)

    def _update_ai(
        self,
        dt: float,
        player_x: float,
        player_y: float,
        player_is_noisy: bool,
    ) -> None:
        for token in self.tokens:
            if token.id in self._lockout_ids:
                continue
            try:
                token.update_ai(dt, player_x, player_y, player_is_noisy)
            except Exception:
                pass

    def _update_squad_movement(self, dt: float) -> None:
        followers_follow_distance = 30.0
        leader_lookup: dict = {}
        for token in self.tokens:
            if token.id in self._lockout_ids:
                continue
            if token.squad_id and token.is_squad_leader:
                leader_lookup[token.squad_id] = token

        for token in self.tokens:
            if token.id in self._lockout_ids:
                continue
            if not token.squad_id or token.is_squad_leader:
                continue
            if token.is_chasing:
                continue
            if token.state is TokenState.RETURN:
                continue
            leader = leader_lookup.get(token.squad_id)
            if not leader or leader.id in self._lockout_ids:
                continue
            if leader.is_chasing:
                token.trigger_chase(leader.x, leader.y)
                continue
            d = token.distance_to(leader.x, leader.y)
            if d > followers_follow_distance:
                step = min(token.patrol_speed * dt, d - followers_follow_distance)
                dx = leader.x - token.x
                dy = leader.y - token.y
                if d > 0:
                    token.x += (dx / d) * step
                    token.y += (dy / d) * step
                    token._direction_x = dx / d
                    token._direction_y = dy / d

    def _check_zone_proximity(
        self,
        player_x: float,
        player_y: float,
        is_sneaking: bool,
    ) -> None:
        if is_sneaking:
            return
        npx = player_x / max(1.0, self._map_w)
        npy = player_y / max(1.0, self._map_h)
        for zone in self.zones:
            if zone.zone_type != ZoneType.WILD:
                continue
            if not zone.contains_point(npx, npy):
                continue
            for token in self.tokens:
                if token.id in self._lockout_ids:
                    continue
                if token.is_chasing:
                    continue
                if token.zone_id != zone.id:
                    continue
                if token.sees_player(player_x, player_y):
                    token.trigger_chase(player_x, player_y)

    def _check_zone_exit_reset(self, player_x: float, player_y: float) -> None:
        npx = player_x / max(1.0, self._map_w)
        npy = player_y / max(1.0, self._map_h)
        for token in self.tokens:
            if not token.is_chasing:
                continue
            if token.id in self._lockout_ids:
                continue
            zone = self._zone_by_id(token.zone_id)
            if not zone:
                continue
            if not zone.contains_point(npx, npy):
                token.reset_chase(cooldown=0.0)

    def _check_encounter_collisions(
        self,
        player_x: float,
        player_y: float,
    ) -> Optional[dict]:
        for token in self.tokens:
            if token.id in self._lockout_ids:
                continue
            if token.check_collision_encounter(player_x, player_y):
                return self._prepare_encounter_social(token, player_x, player_y)
        return None

    def _collect_nearby_tokens(
        self,
        token: RoamingToken,
        player_x: float,
        player_y: float,
    ) -> List[RoamingToken]:
        collected: set = set()
        collected_ids: set = set()

        def _add_token(t: RoamingToken) -> None:
            if t.id in self._lockout_ids or t.id in collected_ids:
                return
            collected.add(t)
            collected_ids.add(t.id)

        _add_token(token)

        squad_ids_to_collect = set()
        if token.squad_id:
            squad_ids_to_collect.add(token.squad_id)

        for t in self.tokens:
            if t.id in self._lockout_ids or t.id == token.id:
                continue
            if not t.is_chasing:
                continue
            _add_token(t)
            if t.squad_id:
                squad_ids_to_collect.add(t.squad_id)

        for sid in squad_ids_to_collect:
            for t in self.tokens:
                if t.id in collected_ids or t.id in self._lockout_ids:
                    continue
                if t.squad_id == sid:
                    _add_token(t)

        for other in self.tokens:
            if other.id in collected_ids or other.id in self._lockout_ids:
                continue
            if other.zone_id != token.zone_id:
                continue
            d = other.distance_to(player_x, player_y)
            if d < _SOCIAL_COMBAT_RADIUS:
                _add_token(other)
                if other.squad_id:
                    for t in self.tokens:
                        if t.id in collected_ids or t.id in self._lockout_ids:
                            continue
                        if t.squad_id == other.squad_id:
                            _add_token(t)

        return list(collected)

    def _prepare_encounter_social(
        self,
        token: RoamingToken,
        player_x: float,
        player_y: float,
    ) -> dict:
        """Подготовить encounter с учётом социального боя и подкрадывания."""
        group = self._collect_nearby_tokens(token, player_x, player_y)
        for gt in group:
            self._lockout_ids.add(gt.id)

        surprise = not any(t.is_chasing for t in group)

        zone = self._zone_by_id(token.zone_id)
        main_data = self._prepare_encounter(token)

        group_data = []
        for gt in group:
            group_data.append({
                "token_id": gt.id,
                "enemy_type": gt.enemy_type,
                "name": gt.name,
            })

        main_data["surprise_attack"] = surprise
        main_data["group"] = group_data
        main_data["token_id"] = token.id
        return main_data

    # ──────────────────────────────────────────────
    #  Encounter data
    # ──────────────────────────────────────────────

    def _prepare_encounter(self, token: RoamingToken) -> dict:
        self._lockout_ids.add(token.id)
        zone = self._zone_by_id(token.zone_id)

        if token.encounter_type == EncounterType.WILD_BEAST:
            dialogue = f"{token.name} преграждает вам путь. Зверь явно голоден и готов к атаке."
            actions = [
                {"id": "fight", "label": "⚔️ Вступить в бой", "type": "fight"},
                {"id": "flee", "label": "🏃 Попытаться сбежать", "type": "flee", "chance": 0.6},
            ]
        elif token.encounter_type == EncounterType.BANDIT:
            dialogue = f"Эй, путник! Кошелёк или жизнь! — кричит {token.name}."
            actions = [
                {"id": "fight", "label": "⚔️ Атаковать", "type": "fight"},
                {"id": "bribe", "label": "💰 Откупиться (50 монет)", "type": "bribe", "cost": 50},
                {"id": "flee", "label": "🏃 Сбежать", "type": "flee", "chance": 0.4},
            ]
        else:
            dialogue = f"Вы столкнулись с {token.name}."
            actions = [
                {"id": "fight", "label": "⚔️ Вступить в бой", "type": "fight"},
                {"id": "flee", "label": "🏃 Сбежать", "type": "flee", "chance": 0.5},
            ]

        return {
            "token_id": token.id,
            "enemy_type": token.enemy_type,
            "name": token.name,
            "type": token.encounter_type.value,
            "dialogue": dialogue,
            "actions": actions,
            "zone_id": token.zone_id,
            "zone_name": zone.location_id if zone else "wild",
            "color": token.color,
        }

    # ──────────────────────────────────────────────
    #  Token lifecycle
    # ──────────────────────────────────────────────

    def remove_token(self, token_id: str) -> None:
        token = next((t for t in self.tokens if t.id == token_id), None)
        if token is not None:
            if self._gfx_canvas is not None:
                token.destroy_graphics(self._gfx_canvas)
            zone_id = token.zone_id
            self._removed_per_zone[zone_id] = self._removed_per_zone.get(zone_id, 0) + 1
        self.tokens = [t for t in self.tokens if t.id != token_id]
        self._lockout_ids.discard(token_id)

    def reset_token(self, token_id: str, cooldown: float = 10.0) -> None:
        token = next((t for t in self.tokens if t.id == token_id), None)
        if token is not None:
            self._lockout_ids.discard(token_id)
            token.reset_chase(cooldown=cooldown)

    def respawn_token(self, token_id: str) -> None:
        self._lockout_ids.discard(token_id)
        old = next((t for t in self.tokens if t.id == token_id), None)
        if not old:
            return
        zone = self._zone_by_id(old.zone_id)
        if not zone:
            return

        etype = random.choice(zone.enemy_types)
        meta = _ENEMY_ENCOUNTER_MAP.get(
            etype, (EncounterType.WILD_BEAST, "Неизвестный", (0.5, 0.5, 0.5))
        )
        encounter_type, name, color = meta

        px, py = zone.random_point_in_zone()
        wx, wy = self._norm_to_world(px, py)

        old.enemy_type = etype
        old.encounter_type = encounter_type
        old.name = name
        old.color = (*color, 1.0)
        old.x = wx
        old.y = wy
        old.state = TokenState.IDLE
        old.is_chasing = False
        old._wait_timer = random.uniform(0.5, 2.0)

    def _try_respawn(self) -> None:
        if not self._removed_per_zone:
            return
        for zone in self.zones:
            if zone.max_tokens <= 0:
                continue
            current_count = sum(1 for t in self.tokens if t.zone_id == zone.id)
            if current_count >= zone.max_tokens:
                continue
            needed = self._removed_per_zone.get(zone.id, 0)
            if needed <= 0:
                continue
            to_spawn = min(needed, zone.max_tokens - current_count)
            for _ in range(to_spawn):
                self._spawn_single_token(zone)
                self._removed_per_zone[zone.id] = max(0, self._removed_per_zone[zone.id] - 1)

    def _spawn_single_token(self, zone: RoamZone) -> None:
        etype = random.choice(zone.enemy_types)
        meta = _ENEMY_ENCOUNTER_MAP.get(
            etype, (EncounterType.WILD_BEAST, "Неизвестный", (0.5, 0.5, 0.5))
        )
        encounter_type, name, color = meta

        px, py = zone.random_point_in_zone()
        wx, wy = self._norm_to_world(px, py)
        home_wx, home_wy = self._norm_to_world(zone.center_x, zone.center_y)
        home_wr = self._norm_r_to_world(zone.radius)

        used_ids = {t.id for t in self.tokens}
        i = 0
        while True:
            tid = _token_id(zone.id, i)
            if tid not in used_ids:
                break
            i += 1

        token = RoamingToken(
            token_id=tid,
            enemy_type=etype,
            encounter_type=encounter_type,
            zone_id=zone.id,
            x=wx, y=wy,
            home_x=home_wx, home_y=home_wy,
            home_radius=home_wr,
            name=name,
            behaviour=TokenBehaviour.RANDOM_WALK,
            color=(*color, 1.0),
            vision_radius=_VISION_RADIUS,
            vision_angle=_VISION_ANGLE,
            hearing_radius=_HEARING_RADIUS,
            patrol_speed=_PATROL_SPEED,
            chase_speed=_CHASE_SPEED,
            squad_id=None,
            is_squad_leader=True,
        )
        if self._gfx_canvas is not None:
            token.init_graphics(self._gfx_canvas)
        self.tokens.append(token)

    # ──────────────────────────────────────────────
    #  Queries
    # ──────────────────────────────────────────────

    def get_tokens_near(self, x: float, y: float, radius: float) -> List[RoamingToken]:
        return [t for t in self.tokens if t.distance_to(x, y) < radius]

    def get_active_tokens(self) -> List[RoamingToken]:
        return [t for t in self.tokens if t.id not in self._lockout_ids]

    def get_chasing_tokens(self) -> List[RoamingToken]:
        return [t for t in self.tokens if t.is_chasing and t.id not in self._lockout_ids]

    def get_zone_at(self, x: float, y: float) -> Optional[RoamZone]:
        npx = x / max(1.0, self._map_w)
        npy = y / max(1.0, self._map_h)
        for zone in self.zones:
            if zone.contains_point(npx, npy):
                return zone
        return None

    def is_in_safe_zone(self, x: float, y: float) -> bool:
        zone = self.get_zone_at(x, y)
        return zone is not None and zone.zone_type == ZoneType.SAFE

    def _zone_by_id(self, zone_id: str) -> Optional[RoamZone]:
        for zone in self.zones:
            if zone.id == zone_id:
                return zone
        return None

    def find_nearby_hotspot(self, x: float, y: float) -> Optional[str]:
        npx = x / max(1.0, self._map_w)
        npy = y / max(1.0, self._map_h)
        for zone in self.zones:
            if zone.zone_type == ZoneType.SAFE and zone.contains_point(npx, npy):
                return zone.location_id
        return None