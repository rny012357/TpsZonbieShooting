"""
バフシステム
データ駆動設計のバフ管理。JSONからバフ種類を読み込み、
エリア番号に応じたレアリティ抽選を行う。
バフオーブ（ゾンビ撃破時に出現→プレイヤーへ飛行）の管理も行う。
"""
import json
import os
import random
import math
import pygame
from config import (
    RARITY_ORDER, RARITY_COLORS,
    RARITY_WEIGHTS_DEFAULT, RARITY_WEIGHTS_MID,
    RARITY_WEIGHTS_HIGH, RARITY_WEIGHTS_MAX,
    BUFF_ORB_FLY_TIME,
    PLAYER_SCREEN_X, SCREEN_HEIGHT,
    SCALE_FACTOR, MIN_SCALE
)
from game_object import GameObject


def load_buff_definitions() -> list[dict]:
    """buffs.jsonからバフ定義を読み込む"""
    json_path = os.path.join(os.path.dirname(__file__), "buffs.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_rarity_weights(area_number: int) -> dict[str, int]:
    """エリア番号に応じたレアリティ重みを取得する"""
    if area_number <= 3:
        return RARITY_WEIGHTS_DEFAULT
    elif area_number <= 6:
        return RARITY_WEIGHTS_MID
    elif area_number <= 9:
        return RARITY_WEIGHTS_HIGH
    else:
        return RARITY_WEIGHTS_MAX


def roll_buff(area_number: int, buff_defs: list[dict]) -> tuple[dict, str]:
    """バフを抽選する。

    Returns:
        (バフ定義dict, レアリティ文字列)
    """
    # バフ種類は均等確率
    buff_def = random.choice(buff_defs)

    # レアリティはエリア番号に応じた重み付け
    weights = get_rarity_weights(area_number)
    rarities = list(weights.keys())
    weight_values = list(weights.values())
    rarity = random.choices(rarities, weights=weight_values, k=1)[0]

    return buff_def, rarity


def get_buff_value(buff_def: dict, rarity: str):
    """バフ定義とレアリティからバフ値を取得する"""
    return buff_def["values"][rarity]


class BuffOrb:
    """バフオーブ: ゾンビ撃破時に出現→放物線でプレイヤーへ飛行→自動取得"""

    def __init__(self, world_x: float, world_z: float,
                 player_x: float, player_z: float,
                 buff_def: dict, rarity: str):
        self.start_world_x = world_x
        self.start_world_z = world_z
        self.buff_def = buff_def
        self.rarity = rarity
        self.color = RARITY_COLORS[rarity]
        self.alive = True
        self.collected = False

        # 画面座標での飛行計算
        rel_x = world_x - player_x
        rel_z = world_z - player_z
        scale = max(MIN_SCALE, 1.0 / (1.0 + rel_z * SCALE_FACTOR))
        self.start_sx = int(PLAYER_SCREEN_X + rel_x * scale)
        self.start_sy = GameObject.relative_z_to_screen_y(max(0, rel_z))

        # 目的地: プレイヤー位置（画面下部中央）
        self.end_sx = PLAYER_SCREEN_X
        self.end_sy = SCREEN_HEIGHT - 100

        self.spawn_time = pygame.time.get_ticks()
        self.fly_time = BUFF_ORB_FLY_TIME

        # 残像用の軌跡
        self.trail: list[tuple[int, int, int]] = []  # (x, y, alpha)

    def update(self) -> bool:
        """オーブを更新する。取得完了時Trueを返す。"""
        if not self.alive:
            return False

        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.fly_time:
            self.alive = False
            self.collected = True
            return True

        # 現在位置を計算（放物線）
        t = elapsed / self.fly_time
        sx, sy = self._get_position(t)

        # 残像に追加
        alpha = max(30, int(180 * (1.0 - t * 0.5)))
        self.trail.append((sx, sy, alpha))
        # 残像は最大8個
        if len(self.trail) > 8:
            self.trail.pop(0)

        return False

    def _get_position(self, t: float) -> tuple[int, int]:
        """補間パラメータtでの画面座標を計算（放物線）"""
        sx = int(self.start_sx + (self.end_sx - self.start_sx) * t)
        # 放物線（上に膨らんでから落ちる）
        arc_height = 120
        sy_linear = self.start_sy + (self.end_sy - self.start_sy) * t
        arc = -4 * arc_height * t * (t - 1)  # 0→peak→0
        sy = int(sy_linear - arc)
        return sx, sy

    def draw(self, surface: pygame.Surface):
        """オーブを描画する（発光＋残像）"""
        if not self.alive:
            return

        elapsed = pygame.time.get_ticks() - self.spawn_time
        t = min(1.0, elapsed / self.fly_time)
        sx, sy = self._get_position(t)

        # 残像描画
        for i, (tx, ty, alpha) in enumerate(self.trail):
            trail_size = max(2, 6 - (len(self.trail) - i))
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            trail_alpha = max(10, alpha // 2)
            pygame.draw.circle(trail_surf, (*self.color, trail_alpha),
                               (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (tx - trail_size, ty - trail_size))

        # グロー（外側の光）
        glow_size = 16
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 60),
                           (glow_size, glow_size), glow_size)
        surface.blit(glow_surf, (sx - glow_size, sy - glow_size))

        # 本体
        orb_size = 6
        pygame.draw.circle(surface, self.color, (sx, sy), orb_size)
        # 中心の白い光
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 3)
