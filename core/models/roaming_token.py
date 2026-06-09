#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import Optional, Tuple

from kivy.graphics import Color, Ellipse, Line, Mesh


CONTACT_RADIUS = 18.0
HEARING_RADIUS = 65.0

CONE_ANGLE_DEG = 120
CONE_LENGTH = 120.0
CONE_ANGLE_RAD = math.radians(CONE_ANGLE_DEG)


class TokenState(Enum):
    IDLE = auto()
    PATROL = auto()
    CHASE = auto()
    RETURN = auto()


class TokenBehaviour(Enum):
    RANDOM_WALK = "random_walk"
    PATROL = "patrol"
    STATIONARY = "stationary"


class EncounterType(Enum):
    WILD_BEAST = "wild_beast"
    BANDIT = "bandit"
    FACTION_PATROL = "faction_patrol"
    BOSS = "boss"


class RoamingToken:
    def __init__(
        self,
        token_id: str,
        enemy_type: str,
        encounter_type: EncounterType,
        zone_id: str,
        x: float,
        y: float,
        home_x: float,
        home_y: float,
        home_radius: float,
        name: str = "Unknown",
        behaviour: TokenBehaviour = TokenBehaviour.RANDOM_WALK,
        faction_id: Optional[str] = None,
        color: Tuple[float, float, float, float] = (0.9, 0.2, 0.2, 1.0),
        vision_radius: float = CONE_LENGTH,
        vision_angle: float = CONE_ANGLE_RAD,
        hearing_radius: float = HEARING_RADIUS,
        patrol_speed: float = 20.0,
        chase_speed: float = 85.0,
    ):
        self.id = token_id
        self.enemy_type = enemy_type
        self.encounter_type = encounter_type
        self.zone_id = zone_id
        self.x = x
        self.y = y
        self.home_x = home_x
        self.home_y = home_y
        self.home_radius = home_radius
        self.name = name
        self.behaviour = behaviour
        self.faction_id = faction_id
        self.color = color
        self.vision_radius = vision_radius
        self.vision_angle = vision_angle
        self.hearing_radius = hearing_radius
        self.patrol_speed = patrol_speed
        self.chase_speed = chase_speed

        self.state: TokenState = TokenState.IDLE
        self.is_chasing: bool = False
        self._direction_x: float = 0.0
        self._direction_y: float = -1.0
        self._target_x: float = x
        self._target_y: float = y
        self._wait_timer: float = random.uniform(0.5, 2.0)
        self._patrol_pause_timer: float = 0.0
        self._aggro_reason: Optional[str] = None
        self._chase_cooldown: float = 0.0

        self._graphics_ready: bool = False
        self._hearing_circle_color: Optional[Color] = None
        self._hearing_circle_ell: Optional[Ellipse] = None
        self._hearing_border_color: Optional[Color] = None
        self._hearing_border_line: Optional[Line] = None
        self._cone_color: Optional[Color] = None
        self._cone_mesh: Optional[Mesh] = None
        self._cone_border_color: Optional[Color] = None
        self._cone_line_left: Optional[Line] = None
        self._cone_line_right: Optional[Line] = None
        self._cone_arc_line: Optional[Line] = None
        self._dot_color: Optional[Color] = None
        self._dot_ell: Optional[Ellipse] = None

        self.bark_label = None
        self._bark_timer_event = None

    def init_graphics(self, canvas) -> None:
        if self._graphics_ready:
            return
        with canvas:
            self._hearing_circle_color = Color(0.35, 0.65, 1.0, 0.06)
            self._hearing_circle_ell = Ellipse(pos=(0, 0), size=(1, 1))
            self._hearing_border_color = Color(0.35, 0.65, 1.0, 0.22)
            self._hearing_border_line = Line(circle=(0, 0, 1), width=1)

            self._cone_color = Color(1.0, 0.6, 0.0, 0.06)
            self._cone_mesh = Mesh(vertices=[], indices=[], mode='triangle_fan')
            self._cone_border_color = Color(1.0, 0.6, 0.0, 0.2)
            self._cone_line_left = Line(points=[], width=1)
            self._cone_line_right = Line(points=[], width=1)
            self._cone_arc_line = Line(points=[], width=1)

            self._dot_color = Color(*self.color)
            self._dot_ell = Ellipse(pos=(0, 0), size=(8, 8))
        self._graphics_ready = True

    def update_graphics(self, alerted: bool = False) -> None:
        if not self._graphics_ready:
            return

        hr = self.hearing_radius
        self._hearing_circle_ell.pos = (self.x - hr, self.y - hr)
        self._hearing_circle_ell.size = (hr * 2, hr * 2)
        self._hearing_border_line.circle = (self.x, self.y, hr)

        self._build_cone_mesh()

        dot_size = 8.0
        self._dot_ell.pos = (self.x - dot_size / 2, self.y - dot_size / 2)
        self._dot_ell.size = (dot_size, dot_size)

        if alerted:
            self._dot_color.rgba = (1.0, 0.2, 0.2, 1.0)
        else:
            self._dot_color.rgba = self.color

    def destroy_graphics(self, canvas) -> None:
        if not self._graphics_ready:
            return
        for instr in (
            self._hearing_circle_color, self._hearing_circle_ell,
            self._hearing_border_color, self._hearing_border_line,
            self._cone_color, self._cone_mesh,
            self._cone_border_color,
            self._cone_line_left, self._cone_line_right, self._cone_arc_line,
            self._dot_color, self._dot_ell,
        ):
            if instr is not None:
                try:
                    canvas.remove(instr)
                except (ValueError, AttributeError):
                    pass
        self._graphics_ready = False

    def _build_cone_mesh(self) -> None:
        if self.vision_angle <= 0 or self.vision_radius <= 0:
            self._cone_mesh.vertices = []
            return

        dir_norm = math.hypot(self._direction_x, self._direction_y)
        if dir_norm < 0.001:
            return
        base_angle = math.atan2(self._direction_y, self._direction_x)

        half_a = self.vision_angle * 0.5
        seg = 14
        verts = [self.x, self.y, 0, 0]
        indices = [0]
        for i in range(seg + 1):
            t = i / seg
            theta = base_angle - half_a + t * self.vision_angle
            px = self.x + math.cos(theta) * self.vision_radius
            py = self.y + math.sin(theta) * self.vision_radius
            verts.extend([px, py, 0, 0])
            indices.append(i + 1)
        self._cone_mesh.vertices = verts
        self._cone_mesh.indices = indices

        arc = []
        for i in range(seg + 1):
            t = i / seg
            theta = base_angle - half_a + t * self.vision_angle
            px = self.x + math.cos(theta) * self.vision_radius
            py = self.y + math.sin(theta) * self.vision_radius
            arc.extend([px, py])

        if len(arc) >= 4:
            self._cone_line_left.points = [self.x, self.y, arc[0], arc[1]]
            self._cone_line_right.points = [self.x, self.y, arc[-2], arc[-1]]
            self._cone_arc_line.points = arc

    def _enemy_sees_player(self, px: float, py: float) -> bool:
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)

        if dist <= 0 or dist > self.vision_radius:
            return False

        dir_norm = math.hypot(self._direction_x, self._direction_y)
        if dir_norm <= 0:
            return False

        cone_half = self.vision_angle * 0.5
        dot = (dx / dist) * (self._direction_x / dir_norm) + \
              (dy / dist) * (self._direction_y / dir_norm)
        return dot >= math.cos(cone_half)

    def update_ai(
        self,
        dt: float,
        player_x: float,
        player_y: float,
        player_is_noisy: bool = False,
    ) -> bool:
        dt = min(dt, 0.1)

        self._patrol_pause_timer = max(0.0, self._patrol_pause_timer - dt)
        self._wait_timer = max(0.0, self._wait_timer - dt)
        self._chase_cooldown = max(0.0, self._chase_cooldown - dt)

        can_detect = self._chase_cooldown <= 0
        sees_player = can_detect and self._enemy_sees_player(player_x, player_y)
        dist_to_player = math.hypot(player_x - self.x, player_y - self.y)
        hears_player = can_detect and player_is_noisy and dist_to_player <= self.hearing_radius

        if self.state is TokenState.CHASE and not can_detect and self._aggro_reason != "ally":
            self._reset_after_lost_player()

        if self.state is TokenState.IDLE:
            if sees_player or hears_player:
                self.state = TokenState.CHASE
                self.is_chasing = True
                if hears_player and not sees_player:
                    self._aggro_reason = "hearing"
                else:
                    self._aggro_reason = "sight"
            elif self._wait_timer <= 0 and self._patrol_pause_timer <= 0:
                self._pick_patrol_target()
                self.state = TokenState.PATROL

        elif self.state is TokenState.PATROL:
            if sees_player or hears_player:
                self.state = TokenState.CHASE
                self.is_chasing = True
                if hears_player and not sees_player:
                    self._aggro_reason = "hearing"
                else:
                    self._aggro_reason = "sight"
            elif self._patrol_pause_timer > 0:
                pass
            else:
                self._patrol_move(dt)

        elif self.state is TokenState.CHASE:
            if sees_player:
                target_x, target_y = player_x, player_y
            elif self._aggro_reason == "hearing" and dist_to_player <= self.hearing_radius:
                target_x, target_y = player_x, player_y
            elif self._aggro_reason == "ally":
                target_x, target_y = player_x, player_y
            elif self._aggro_reason == "sight" and dist_to_player <= self.vision_radius:
                target_x, target_y = player_x, player_y
            else:
                self._reset_after_lost_player()
                return False

            self._move_towards(target_x, target_y, self.chase_speed * dt)
            if self._clamp_to_zone():
                self._reset_after_lost_player()

        elif self.state is TokenState.RETURN:
            d_h = math.hypot(self.home_x - self.x, self.home_y - self.y)
            if d_h < 5.0:
                self._wait_timer = random.uniform(0.5, 2.0)
                self.state = TokenState.IDLE
            else:
                self._move_towards(self.home_x, self.home_y, self.patrol_speed * dt)
                self._clamp_to_zone()

        return sees_player or hears_player

    def _pick_patrol_target(self) -> None:
        angle = random.uniform(0.0, 6.2832)
        dist = random.uniform(20.0, self.home_radius * 0.55)
        self._target_x = self.home_x + math.cos(angle) * dist
        self._target_y = self.home_y + math.sin(angle) * dist

    def _patrol_move(self, dt: float) -> None:
        dx = self._target_x - self.x
        dy = self._target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < 3.0:
            self._patrol_pause_timer = random.uniform(1.0, 3.0)
            self.state = TokenState.IDLE
            return

        step = min(self.patrol_speed * dt, dist)
        target_dir_x = dx / dist
        target_dir_y = dy / dist
        rot_factor = min(1.0, dt * 4.0)
        self._direction_x += (target_dir_x - self._direction_x) * rot_factor
        self._direction_y += (target_dir_y - self._direction_y) * rot_factor
        dn = math.hypot(self._direction_x, self._direction_y)
        if dn > 0:
            self._direction_x /= dn
            self._direction_y /= dn

        self.x += (dx / dist) * step
        self.y += (dy / dist) * step
        self._clamp_to_zone()

    def _move_towards(self, tx: float, ty: float, step: float) -> None:
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            return
        ms = min(step, dist)
        self.x += (dx / dist) * ms
        self.y += (dy / dist) * ms
        self._direction_x = dx / dist
        self._direction_y = dy / dist

    def _clamp_to_zone(self) -> bool:
        dx = self.x - self.home_x
        dy = self.y - self.home_y
        dist = math.hypot(dx, dy)
        if dist > self.home_radius:
            if dist > 0:
                self.x = self.home_x + (dx / dist) * self.home_radius
                self.y = self.home_y + (dy / dist) * self.home_radius
            return True
        return False

    def _reset_after_lost_player(self) -> None:
        self.is_chasing = False
        self._aggro_reason = None
        self.state = TokenState.RETURN
        self._target_x = self.home_x
        self._target_y = self.home_y

    def reset_chase(self, cooldown: float = 10.0) -> None:
        self.is_chasing = False
        self._aggro_reason = None
        self._chase_cooldown = cooldown
        self.state = TokenState.RETURN
        self._target_x = self.home_x
        self._target_y = self.home_y

    def trigger_chase(self, target_x: float, target_y: float) -> None:
        if self._chase_cooldown > 0:
            return
        if self.state is TokenState.CHASE:
            return
        self.state = TokenState.CHASE
        self.is_chasing = True
        self._aggro_reason = "ally"

    def check_collision_encounter(self, player_x: float, player_y: float) -> bool:
        return (
            self.state is TokenState.CHASE
            and self.distance_to(player_x, player_y) < CONTACT_RADIUS
        )

    def check_physical_collision(self, player_x: float, player_y: float) -> bool:
        return self.distance_to(player_x, player_y) < CONTACT_RADIUS

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(x - self.x, y - self.y)

    @property
    def alerted(self) -> bool:
        return self.state is TokenState.CHASE

    @alerted.setter
    def alerted(self, value: bool) -> None:
        if value and self.state is not TokenState.CHASE:
            self.state = TokenState.CHASE
            self.is_chasing = True
            if self._aggro_reason is None:
                self._aggro_reason = "sight"
        elif not value and self.state is TokenState.CHASE:
            self._reset_after_lost_player()