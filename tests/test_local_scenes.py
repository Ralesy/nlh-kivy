#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Тесты конфигурации проходимых локальных сцен."""

from data.local_scenes import (
    COMBAT_SCENES,
    LOCATION_BOSSES,
    SCENE_BACKGROUND_FILES,
    build_scene_config,
    resolve_background,
    scene_background_path,
)


def test_combat_scenes_have_enemies():
    for scene_id in COMBAT_SCENES:
        cfg = build_scene_config(scene_id)
        assert cfg is not None
        assert cfg.scene_type == "combat"
        assert cfg.enemy_count >= 1
        assert cfg.enemy_location_id == scene_id


def test_city_has_zones():
    cfg = build_scene_config("city")
    assert cfg.scene_type == "city"
    assert len(cfg.zones) == 2
    targets = {z.target_scene for z in cfg.zones}
    assert targets == {"tavern", "shop"}


def test_city_uses_town_background():
    """Город использует bg_town из папки town."""
    cfg = build_scene_config("city")
    assert cfg.background_candidates == [scene_background_path("city")]
    assert cfg.background_candidates[0].endswith("bg_town.png")


def test_shop_has_no_background_image():
    """Магазин без отдельного фона — однотонная заливка."""
    cfg = build_scene_config("shop")
    assert cfg.background_candidates == []


def test_tavern_has_npcs():
    cfg = build_scene_config("tavern")
    assert cfg.scene_type == "tavern"
    assert len(cfg.npcs) >= 4


def test_bosses_mapped_to_locations():
    assert set(LOCATION_BOSSES.keys()) == COMBAT_SCENES
    assert LOCATION_BOSSES["forest"].boss_num == 1
    assert LOCATION_BOSSES["mountains"].boss_num == 4


def test_background_fallback():
    path = resolve_background("forest")
    assert path is not None
    assert path.endswith("bg_forest.png")


def test_all_combat_scenes_have_bg_mapping():
    for scene_id in COMBAT_SCENES:
        assert scene_id in SCENE_BACKGROUND_FILES
        assert resolve_background(scene_id) is not None


def test_enter_local_scene_reloads_when_already_active():
    """Переход city→tavern на том же экране должен вызвать on_leave/on_enter."""
    calls = []

    class FakeScreen:
        manager = None
        scene_id = "city"

        def setup_scene(self, scene_id, parent_scene=None):
            calls.append(("setup", scene_id, parent_scene))
            self.scene_id = scene_id

        def on_leave(self):
            calls.append(("leave", self.scene_id))

        def on_enter(self):
            calls.append(("enter", self.scene_id))

    class FakeMgr:
        current = "local_location"

    screen = FakeScreen()
    screen.manager = FakeMgr()
    app = type("App", (), {"local_location_screen": screen})()

    from data.local_scenes import enter_local_scene

    assert enter_local_scene(app, "tavern", parent_scene="city") is True
    assert calls == [
        ("leave", "city"),
        ("setup", "tavern", "city"),
        ("enter", "tavern"),
    ]
