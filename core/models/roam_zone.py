#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
import random

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ZoneType(Enum):
    WILD = "wild"
    FACTION = "faction"
    SAFE = "safe"
    INTEREST = "interest"


@dataclass
class RoamZone:
    id: str
    zone_type: ZoneType
    center_x: float
    center_y: float
    radius: float
    location_id: Optional[str] = None
    faction_id: Optional[str] = None
    color: tuple = (0.5, 0.2, 0.2, 0.12)
    enemy_types: List[str] = field(default_factory=list)
    token_count: int = 0
    max_tokens: int = 6

    def contains_point(self, x: float, y: float) -> bool:
        dx = x - self.center_x
        dy = y - self.center_y
        return (dx * dx + dy * dy) <= (self.radius * self.radius)

    def random_point_in_zone(self) -> tuple:
        angle = random.uniform(0.0, 6.2832)
        dist = random.uniform(0.0, self.radius * 0.85)
        return (self.center_x + dist * math.cos(angle),
                self.center_y + dist * math.sin(angle))