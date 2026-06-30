#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Боевое поле: раунды, атаки игрока и врагов, способности, побег.
"""

import random
from typing import List, Optional, Tuple

from core.combat.damage import (
    ENEMY_VARIANCE,
    apply_critical,
    apply_forced_critical,
    armor_ignore_bonus,
    player_crit_chance,
    resolve_hit,
    roll_raw_damage,
)
from core.combat.loot import BattleResult, LootDrop
from core.creatures import Creature, Player


class Battlefield:
    """Состояние одного боя: игрок, враги, раунд, флаги способностей."""

    def __init__(
        self,
        player: Player,
        enemies: List[Creature],
        surprise_attack: bool = False,
    ):
        """Инициализировать бой."""
        self.player = player
        self.enemies = list(enemies)
        self.round = 0
        self.ability_used_this_battle = False
        self.surprise_attack_ready = bool(surprise_attack)

    def alive_enemies(self) -> List[Creature]:
        """Список живых врагов."""
        return [enemy for enemy in self.enemies if enemy.is_alive]

    def is_over(self) -> bool:
        """True, если игрок мёртв или все враги повержены."""
        return not self.player.is_alive or not self.alive_enemies()

    def _select_target(
        self,
        enemy_index: Optional[int],
    ) -> Tuple[Optional[Creature], str]:
        """
        Выбрать цель атаки по индексу в списке живых врагов.

        Returns:
            (цель, сообщение об ошибке). При успехе ошибка пустая.
        """
        enemies = self.alive_enemies()
        if not enemies:
            return None, "Нет врагов!"

        if enemy_index is None:
            return random.choice(enemies), ""

        if enemy_index < 0 or enemy_index >= len(enemies):
            return None, "Неверная цель!"

        return enemies[enemy_index], ""

    def _apply_passive_abilities(self, damage: int) -> int:
        """Бонус от пассивных способностей оружия."""
        weapon = self.player.weapon
        if not weapon or not getattr(weapon, "ability", None):
            return damage

        ability = weapon.ability
        if not ability or ability.ability_type != "passive":
            return damage

        if hasattr(ability, "damage_per_hit"):
            damage += ability.damage_per_hit

        return damage

    def _get_armor_ignore_ratio(self) -> float:
        """Доля игнорируемой брони (топоры)."""
        weapon = self.player.weapon
        if not weapon or not getattr(weapon, "ability", None):
            return 0.0
        ability = weapon.ability
        return float(getattr(ability, "armor_ignore", 0.0) or 0.0)

    def _build_player_hit(
        self,
        target: Creature,
        damage_multiplier: float = 1.0,
        variance=(-3, 5),
    ) -> Tuple[int, bool, int, bool]:
        """
        Рассчитать удар игрока по цели.

        Returns:
            (фактический урон, был ли крит, проигнорированная броня, внезапный крит).
        """
        damage = roll_raw_damage(
            int(self.player.damage * damage_multiplier),
            variance=variance,
        )
        damage = self._apply_passive_abilities(damage)

        ignore_ratio = self._get_armor_ignore_ratio()
        ignored = armor_ignore_bonus(int(target.defense), ignore_ratio)
        damage += ignored

        surprise_critical = self.surprise_attack_ready
        if surprise_critical:
            damage = apply_forced_critical(damage)
            is_critical = True
            self.surprise_attack_ready = False
        else:
            damage, is_critical = apply_critical(
                damage,
                player_crit_chance(self.player),
            )
        dealt = resolve_hit(damage, target)
        return dealt, is_critical, ignored, surprise_critical

    def player_attack(
        self,
        enemy_index: Optional[int] = None,
    ) -> Tuple[str, bool]:
        """
        Атака игрока по выбранному или случайному врагу.

        Args:
            enemy_index: индекс в списке alive_enemies(); None — случайная цель.

        Returns:
            (сообщение в лог, враг убит).
        """
        target, error = self._select_target(enemy_index)
        if target is None:
            return error, False

        dealt, is_critical, armor_ignored, surprise_critical = self._build_player_hit(target)
        ignore_text = (
            f" (игнорируя {armor_ignored} ед. брони)"
            if armor_ignored > 0
            else ""
        )

        if surprise_critical:
            log = (
                f"Из засады! [Энергия] КРИТИЧЕСКИЙ УДАР! [Энергия] Вы наносите "
                f"{dealt} урона по {target.name}!{ignore_text}"
            )
        elif is_critical:
            log = (
                f"[Энергия] КРИТИЧЕСКИЙ УДАР! [Энергия] Вы наносите "
                f"{dealt} урона по {target.name}!{ignore_text}"
            )
        else:
            log = f"Вы наносите {dealt} урона по {target.name}.{ignore_text}"

        killed = not target.is_alive
        if killed:
            log += f" [Взрыв] {target.name} повержен!"
            from kivy.logger import Logger
            Logger.info(f"BATTLE: Enemy killed: '{target.name}'")
            self.player.update_quest_progress(target.name)

        return log, killed

    def use_weapon_ability(self) -> Tuple[bool, List[str]]:
        """Использовать активную способность экипированного оружия."""
        weapon = self.player.weapon
        if not weapon or not getattr(weapon, "ability", None):
            return False, ["Оружие не имеет активной способности."]

        ability = weapon.ability
        if ability.ability_type != "active":
            return False, ["Это пассивная способность, не активная."]

        if self.ability_used_this_battle:
            return False, ["Способность уже использована в этой битве!"]

        enemies = self.alive_enemies()
        if not enemies:
            return False, ["Нет врагов для атаки!"]

        logs: List[str] = []
        weapon_type = getattr(weapon, "weapon_type", "sword")

        if weapon_type == "sword":
            target = random.choice(enemies)
            total_damage = 0
            for hit in range(2):
                dealt, _, _, _ = self._build_player_hit(
                    target,
                    damage_multiplier=1.3,
                    variance=(-1, 3),
                )
                total_damage += dealt
                logs.append(
                    f"Удар {hit + 1}! Вы наносите {dealt} урона "
                    f"по {target.name}."
                )
                if not target.is_alive:
                    logs.append(f"[Взрыв] {target.name} повержен мечом!")
                    self.player.update_quest_progress(target.name)
                    break
            if target.is_alive:
                logs.append(f"[Энергия] Всего урона: {total_damage}!")

        elif weapon_type == "bow":
            targets = random.sample(enemies, min(2, len(enemies)))
            for i, target in enumerate(targets):
                dealt, _, _, _ = self._build_player_hit(
                    target,
                    variance=(-2, 2),
                )
                logs.append(
                    f"🏹 Выстрел {i + 1}! Вы наносите {dealt} урона "
                    f"по {target.name}."
                )
                if not target.is_alive:
                    logs.append(f"[Взрыв] {target.name} поражен стрелой!")
                    self.player.update_quest_progress(target.name)

        elif weapon_type == "staff":
            for target in list(enemies):
                if not target.is_alive:
                    continue
                dealt, _, _, _ = self._build_player_hit(
                    target,
                    variance=(-3, 2),
                )
                logs.append(
                    f"Магический взрыв наносит {dealt} урона "
                    f"по {target.name}!"
                )
                if not target.is_alive:
                    logs.append(f"[Взрыв] {target.name} повержен!")
                    self.player.update_quest_progress(target.name)

        self.ability_used_this_battle = True
        return True, logs

    def companion_turn(self) -> List[str]:
        """Ход спутников: каждый живой бьёт случайного врага."""
        logs: List[str] = []
        for companion in self.player.companions:
            if not companion.is_alive:
                continue
            enemies = self.alive_enemies()
            if not enemies:
                break

            target = random.choice(enemies)
            damage = roll_raw_damage(companion.damage, variance=(-1, 2))
            dealt = resolve_hit(damage, target)
            logs.append(
                f"{companion.name} наносит {dealt} урона по {target.name}."
            )

            if not target.is_alive:
                logs.append(f"[Взрыв] {target.name} повержен!")
                self.player.update_quest_progress(target.name)
                # Награда за убийство спутником — монеты игроку
                self.player.coins += target.coins

        return logs

    def enemy_turn(self) -> List[str]:
        """Ход всех живых врагов."""
        logs: List[str] = []
        for enemy in self.alive_enemies():
            possible_targets = [self.player] + [
                companion
                for companion in self.player.companions
                if companion.is_alive
            ]
            if not possible_targets:
                continue

            target = random.choice(possible_targets)
            damage = roll_raw_damage(enemy.damage, variance=ENEMY_VARIANCE)
            damage, is_critical = apply_critical(damage, 0.04)
            dealt = resolve_hit(damage, target)

            if target == self.player:
                if is_critical:
                    logs.append(
                        f"[Энергия] {enemy.name} наносит "
                        f"КРИТИЧЕСКИЙ УДАР! {dealt} урона вам!"
                    )
                else:
                    logs.append(f"{enemy.name} наносит {dealt} урона вам!")
                if not self.player.is_alive:
                    logs.append("Вы были повержены!")
            else:
                if is_critical:
                    logs.append(
                        f"[Энергия] {enemy.name} наносит "
                        f"КРИТИЧЕСКИЙ УДАР по {target.name}! "
                        f"{dealt} урона!"
                    )
                else:
                    logs.append(
                        f"{enemy.name} наносит {dealt} урона {target.name}!"
                    )
                if not target.is_alive:
                    logs.append(f"💔 {target.name} выбывает из боя!")

        return logs

    def attempt_escape(self) -> Tuple[bool, List[str]]:
        """
        Попытка побега (30% успех).

        Returns:
            (успех, список сообщений).
        """
        logs: List[str] = []
        if random.random() < 0.3:
            logs.append("Вы успешно сбежали!")
            return True, logs

        logs.append("Враги преследуют вас!")
        for enemy in self.alive_enemies():
            damage = max(1, enemy.damage // 2)
            dealt = self.player.take_damage(damage)
            logs.append(f"{enemy.name} наносит {dealt} урона!")
        return False, logs

    def generate_battle_loot(self) -> BattleResult:
        """Собрать лут, золото и XP с поверженных врагов."""
        loot_items: List[LootDrop] = []
        total_gold = 0
        total_xp = 0

        for enemy in self.enemies:
            if enemy.is_alive:
                continue

            total_gold += enemy.coins
            template = getattr(enemy, "_template", None)
            if template:
                total_xp += template.xp_reward
            else:
                total_xp += enemy.level * 30

            if getattr(enemy, "weapon", None):
                weapon_id = getattr(enemy.weapon, "id", None)
                if weapon_id:
                    loot_items.append(LootDrop(weapon_id, 1))

            if getattr(enemy, "armor", None):
                armor_id = getattr(enemy.armor, "id", None)
                if armor_id:
                    loot_items.append(LootDrop(armor_id, 1))

            if template and template.loot_table:
                player_luck = float(getattr(self.player, "luck", 1.0))
                bonus_chance = 0.15 * player_luck
                if random.random() < bonus_chance:
                    items = [item_id for item_id, _ in template.loot_table]
                    chances = [chance for _, chance in template.loot_table]
                    adj_chances = [max(0.0, c * player_luck) for c in chances]
                    bonus_item = random.choices(
                        items,
                        weights=adj_chances,
                        k=1,
                    )[0]
                    loot_items.append(LootDrop(bonus_item, 1))

        return BattleResult(
            victory=True,
            loot=loot_items,
            gold_earned=total_gold,
            xp_earned=total_xp,
        )
