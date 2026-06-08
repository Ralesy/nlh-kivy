#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
from enum import Enum
from typing import List, Tuple

from core.models.roaming_token import RoamingToken


class StealthMode(Enum):
    NORMAL = "normal"
    STEALTH = "stealth"
    RUNNING = "running"


class DetectionLevel(Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DETECTED = "detected"


_NOISE_RADII = {
    StealthMode.NORMAL: 60.0,
    StealthMode.STEALTH: 10.0,
    StealthMode.RUNNING: 120.0,
}

_ZOOM_VALUES = {
    StealthMode.NORMAL: 2.0,
    StealthMode.STEALTH: 3.5,
    StealthMode.RUNNING: 1.5,
}

_SPEED_MULTIPLIERS = {
    StealthMode.NORMAL: 1.0,
    StealthMode.STEALTH: 0.4,
    StealthMode.RUNNING: 1.8,
}


class StealthController:
    def __init__(self):
        self.mode: StealthMode = StealthMode.NORMAL
        self._noise_radius: float = _NOISE_RADII[StealthMode.NORMAL]
        self._camera_zoom: float = _ZOOM_VALUES[StealthMode.NORMAL]
        self.detection_level: DetectionLevel = DetectionLevel.SAFE
        self.speed_multiplier: float = _SPEED_MULTIPLIERS[StealthMode.NORMAL]
        self.stealth_bonus: float = 0.0
        self.speed_potion_active: bool = False

    def set_mode(self, mode: StealthMode) -> None:
        if self.speed_potion_active:
            return
        self.mode = mode
        self._noise_radius = _NOISE_RADII[mode]
        self._camera_zoom = _ZOOM_VALUES[mode]
        self.speed_multiplier = _SPEED_MULTIPLIERS[mode]

    def activate_speed_potion(self, duration: float = 5.0) -> None:
        self.speed_potion_active = True
        self._noise_radius = 0.0
        self.speed_multiplier = 2.5

    def deactivate_speed_potion(self) -> None:
        self.speed_potion_active = False
        self.set_mode(self.mode)

    def update(
        self,
        dt: float,
        tokens: List[RoamingToken],
        player_x: float,
        player_y: float,
    ) -> List[Tuple[RoamingToken, float]]:
        closest_threats: List[Tuple[RoamingToken, float]] = []
        highest_detection = DetectionLevel.SAFE

        for token in tokens:
            dist = token.distance_to(player_x, player_y)

            if dist > token.vision_radius + self._noise_radius:
                continue

            noise_range = self._noise_radius - self.stealth_bonus * 5.0
            if noise_range < 0:
                noise_range = 0.0

            if dist < token.vision_radius:
                dx = player_x - token.x
                dy = player_y - token.y
                angle_to_player = math.atan2(dy, dx)
                token_angle = math.atan2(token._direction_y, token._direction_x)
                diff = abs(angle_to_player - token_angle)
                if diff > math.pi:
                    diff = 2 * math.pi - diff

                if diff < token.vision_angle / 2:
                    closest_threats.append((token, dist))
                    if highest_detection == DetectionLevel.SAFE:
                        highest_detection = DetectionLevel.SUSPICIOUS

            if dist < noise_range and dist < token.vision_radius:
                closest_threats.append((token, dist))
                if highest_detection == DetectionLevel.SAFE:
                    highest_detection = DetectionLevel.SUSPICIOUS

            if token.alerted:
                highest_detection = DetectionLevel.DETECTED

        self.detection_level = highest_detection
        return closest_threats

    @property
    def noise_radius(self) -> float:
        return self._noise_radius

    @property
    def camera_zoom(self) -> float:
        return self._camera_zoom