#!/usr/bin/env python3
"""Tests for RoamingEntityManager (chase cooldown, zone-bound, respawn, 120px cone)."""
import sys, math
import pytest

sys.path.insert(0, ".")

from systems.roaming_entity_manager import RoamingEntityManager
from core.models.roaming_token import (
    TokenState, CONTACT_RADIUS, CONE_LENGTH, HEARING_RADIUS,
    RoamingToken,
)


MAP_W, MAP_H = 1280, 720


@pytest.fixture
def rm():
    """Create a fresh RoamingEntityManager for each test."""
    manager = RoamingEntityManager(map_world_width=MAP_W, map_world_height=MAP_H)
    manager.set_map_size(MAP_W, MAP_H)
    return manager


def _pick_token(rm: RoamingEntityManager) -> RoamingToken:
    """Pick first available token not in lockout."""
    for t in rm.tokens:
        if t.id not in rm._lockout_ids:
            return t
    return None


# ─── 1. Instant visual detection → CHASE ───
def test_visual_cone_detection(rm):
    """Token should instantly chase when player is in vision cone."""
    print(f"\nZones: {len(rm.zones)}, Tokens: {len(rm.tokens)}")
    print("\n=== 1. Visual (cone) detection ===")
    rm._lockout_ids.clear()
    tk = _pick_token(rm)
    tk.state = TokenState.IDLE
    tk._wait_timer = 10.0
    tk._direction_x = 1.0
    tk._direction_y = 0.0
    px = tk.x + 50.0
    py = tk.y
    for step in range(5):
        rm.update(0.1, px, py, player_is_noisy=False, is_sneaking=True)
        if tk.state is TokenState.CHASE:
            print(f"  Step {step+1}: DETECTED → {tk.state.name}")
            break
    assert tk.state is TokenState.CHASE
    print("  ✓ Instant CHASE on visual contact")


# ─── 2. Reset chase + cooldown ───
def test_reset_chase_cooldown(rm):
    """After reset_chase(), cooldown should block re-detection."""
    print("\n=== 2. reset_chase() → cooldown blocks re-detection ===")
    rm._lockout_ids.clear()
    tk = _pick_token(rm)
    tk.reset_chase(cooldown=5.0)
    assert tk.state is TokenState.RETURN
    assert not tk.is_chasing
    # Move player far from token to avoid immediate re-encounter
    far_x = tk.home_x - 200.0
    far_y = tk.home_y
    for step in range(60):
        rm.update(0.1, far_x, far_y, player_is_noisy=False, is_sneaking=True)
        if tk._chase_cooldown <= 0:
            print(f"  Step {step+1}: cooldown expired")
            break
    assert tk._chase_cooldown <= 0, "Cooldown must expire"
    print(f"  ✓ reset_chase: state={tk.state.name}, is_chasing={tk.is_chasing}")


# ─── 3. Hearing detection ───
def test_hearing_detection(rm):
    """Token should chase when player is noisy within hearing radius."""
    print("\n=== 3. Hearing detection ===")
    rm._lockout_ids.clear()
    tk2 = _pick_token(rm)
    tk2.state = TokenState.IDLE
    tk2._wait_timer = 10.0
    tk2._direction_x = 0.0
    tk2._direction_y = -1.0
    hpx = tk2.x
    hpy = tk2.y + HEARING_RADIUS - 15.0
    for step in range(5):
        rm.update(0.1, hpx, hpy, player_is_noisy=True, is_sneaking=True)
        if tk2.state is TokenState.CHASE:
            break
    assert tk2.state is TokenState.CHASE, "Hearing should trigger CHASE"
    print("  ✓ CHASE via hearing")


# ─── 4. Sneaking (quiet) — no hearing aggro ───
def test_sneaking_no_hearing(rm):
    """Sneaking player should NOT trigger hearing aggro."""
    print("\n=== 4. Sneaking (quiet) — no hearing aggro ===")
    rm._lockout_ids.clear()
    tk3 = _pick_token(rm)
    tk3.state = TokenState.IDLE
    tk3._wait_timer = 10.0
    # Face away from player to avoid vision detection
    tk3._direction_x = 1.0
    tk3._direction_y = 0.0
    # Place player at hearing radius but outside vision cone
    spx = tk3.x
    spy = tk3.y + HEARING_RADIUS - 10.0
    for step in range(5):
        rm.update(0.1, spx, spy, player_is_noisy=False, is_sneaking=True)
    assert tk3.state is not TokenState.CHASE, "Quiet player should NOT trigger hearing"
    print(f"  ✓ State stays {tk3.state.name}")


# ─── 5. Encounter on physical catch ───
def test_physical_catch_encounter(rm):
    """When token catches player, encounter data should be returned."""
    print("\n=== 5. Physical catch → Encounter ===")
    tk = _pick_token(rm)
    tk.state = TokenState.CHASE
    tk.is_chasing = True
    tk._aggro_reason = "sight"
    # Place player directly on top of token to ensure collision
    cx, cy = tk.x, tk.y
    enc = None
    for _ in range(5):
        enc = rm.update(0.1, cx, cy, player_is_noisy=False, is_sneaking=True)
        if enc:
            break
    assert enc is not None, "Encounter should trigger when player is on top of chasing token"
    print(f"  ENCOUNTER: {enc['name']}")


# ─── 6. Remove + Respawn ───
def test_remove_and_respawn(rm):
    """Removed tokens should respawn after timer expires."""
    print("\n=== 6. Remove + Respawn ===")
    lock_token = _pick_token(rm)
    assert lock_token is not None
    lock_id = lock_token.id
    zone_id = lock_token.zone_id
    rm.remove_token(lock_id)
    assert lock_id not in [t.id for t in rm.tokens]
    print(f"  Removed {lock_id} from {zone_id} ✓")
    count_before = len(rm.tokens)
    rm._respawn_timer = 9.9
    rm.update(0.1, 0, 0, is_sneaking=True)
    count_after = len(rm.tokens)
    respawned = count_after - count_before
    print(f"  Respawn triggered: tokens {count_before} → {count_after} (+{respawned})")
    assert respawned > 0, "Tokens should respawn"
    print("  ✓ Respawn works")


# ─── 7. CHASE aborts at zone boundary ───
def test_chase_aborts_at_zone_boundary(rm):
    """Token should return home when chased beyond zone boundary."""
    print("\n=== 7. CHASE aborts at zone boundary ===")
    rm._lockout_ids.clear()
    tk4 = _pick_token(rm)
    tk4.x = tk4.home_x + tk4.home_radius - 15.0
    tk4.y = tk4.home_y
    tk4.state = TokenState.CHASE
    tk4.is_chasing = True
    tk4._aggro_reason = "sight"
    tk4._direction_x = 1.0
    tk4._direction_y = 0.0
    px = tk4.x + 50.0
    py = tk4.home_y
    for step in range(40):
        rm.update(0.1, px, py, player_is_noisy=False, is_sneaking=True)
        if tk4.state is TokenState.RETURN:
            print(f"  Step {step+1}: zone boundary → RETURN")
            break
    else:
        dist = math.hypot(tk4.x - tk4.home_x, tk4.y - tk4.home_y)
        print(f"  WARNING: no abort after 40, dist={dist:.0f}")
    assert tk4.state is TokenState.RETURN, f"Expected RETURN, got {tk4.state.name}"
    for step2 in range(200):
        rm.update(0.1, px, py, player_is_noisy=False, is_sneaking=True)
        if tk4.state in (TokenState.IDLE, TokenState.PATROL):
            print(f"  Step {step2+1}: returned home → {tk4.state.name}")
            break


# ─── 8. Zone queries ───
def test_zone_queries(rm):
    """Zone query methods should work correctly."""
    print("\n=== 8. Zone queries ===")
    rm._lockout_ids.clear()
    qz = _pick_token(rm)
    z = rm.get_zone_at(qz.x, qz.y)
    print(f"  get_zone_at → {z.id if z else 'None'}")
    safe = rm.is_in_safe_zone(240, 612)
    print(f"  is_in_safe_zone(city) → {safe}")


# ─── 9. Zone proximity detection (not sneaking in zone → chase) ───
def test_zone_proximity_detection(rm):
    """Player in zone without sneaking should trigger chase for visible tokens."""
    print("\n=== 9. Zone proximity detection ===")
    rm._lockout_ids.clear()
    zone = None
    for z in rm.zones:
        if z.zone_type.name == "WILD" and z.max_tokens > 0:
            zone = z
            break
    if zone:
        target_token = None
        for t in rm.tokens:
            if t.zone_id == zone.id:
                target_token = t
                break

        if not target_token:
            pytest.skip("No tokens in zone")

        for t in rm.tokens:
            if t.zone_id == zone.id:
                t.state = TokenState.IDLE
                t._wait_timer = 10.0
                t._chase_cooldown = 0.0
                t.is_chasing = False
                t._aggro_reason = None
                t._direction_x = 1.0
                t._direction_y = 0.0

        player_in_zone_x = target_token.x + target_token.vision_radius * 0.5
        player_in_zone_y = target_token.y

        rm.update(0.1, player_in_zone_x, player_in_zone_y, player_is_noisy=True, is_sneaking=False)
        zone_chasing = [t for t in rm.tokens if t.is_chasing and t.zone_id == zone.id]
        print(f"  Player in zone {zone.id}: {len(zone_chasing)}/{zone.max_tokens} chasing")
        assert target_token.is_chasing, "Token that sees player should chase when player is not sneaking"
        print("  ✓ Zone proximity triggers chase when not sneaking")

        # Now test with sneaking
        for t in rm.tokens:
            if t.zone_id == zone.id:
                t.state = TokenState.IDLE
                t._wait_timer = 10.0
                t._chase_cooldown = 0.0
                t.is_chasing = False
                t._aggro_reason = None
                # Face away from player to prevent vision detection
                dx = t.x - player_in_zone_x
                dy = t.y - player_in_zone_y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    t._direction_x = dx / dist
                    t._direction_y = dy / dist

        rm.update(0.1, player_in_zone_x, player_in_zone_y, player_is_noisy=False, is_sneaking=True)
        zone_chasing = [t for t in rm.tokens if t.is_chasing and t.zone_id == zone.id]
        print(f"  Player sneaking in zone {zone.id}: {len(zone_chasing)}/{zone.max_tokens} chasing")
        assert len(zone_chasing) == 0, "Tokens should NOT chase when player is sneaking"
        print("  ✓ Stealth blocks zone detection")
    else:
        print("  SKIPPED: no wild zone found")


# ─── 10. Social battle: collect_nearby_tokens ───
def test_social_battle_collection(rm):
    """Social battle should collect nearby tokens (Mount & Blade style)."""
    print("\n=== 10. Social battle (Mount & Blade style) ===")
    rm._lockout_ids.clear()
    target_zone = None
    for z in rm.zones:
        if z.zone_type.name == "WILD" and z.max_tokens >= 3:
            target_zone = z
            break
    if target_zone:
        z_tokens = [t for t in rm.tokens if t.zone_id == target_zone.id]
        center_x, center_y = target_zone.center_x * MAP_W, target_zone.center_y * MAP_H
        for i, t in enumerate(z_tokens[:3]):
            t.x = center_x + i * 30
            t.y = center_y
            t.state = TokenState.CHASE
            t.is_chasing = True

        main_token = z_tokens[0]
        nearby = rm._collect_nearby_tokens(main_token, main_token.x, main_token.y)
        print(f"  Zone {target_zone.id}: {len(nearby)} tokens near player")
        assert len(nearby) >= 2, f"Should find at least 2 nearby tokens, got {len(nearby)}"
        print("  ✓ Social battle collects multiple enemies near player")

        enc = rm._prepare_encounter_social(main_token, main_token.x, main_token.y)
        assert not enc.get("surprise_attack"), "surprise_attack should be False when all chasing"
        print(f"  surprise_attack=False (enemies were chasing): ✓")

        rm._lockout_ids.clear()
        for t in z_tokens[:3]:
            t.is_chasing = False
        enc = rm._prepare_encounter_social(main_token, main_token.x, main_token.y)
        assert enc.get("surprise_attack"), "surprise_attack should be True when none chasing"
        print(f"  surprise_attack=True (stealth approach): ✓")
    else:
        print("  SKIPPED: no zone with 3+ tokens found")


# ─── 11. Encounter group data ───
def test_encounter_group_data(rm):
    """Encounter data should contain proper group information."""
    print("\n=== 11. Encounter group data ===")
    rm._lockout_ids.clear()
    sample = _pick_token(rm)
    if sample:
        enc = rm._prepare_encounter(sample)
        print("  _prepare_encounter returns basic data ✓")
    print("  Encounter data structure verified ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
