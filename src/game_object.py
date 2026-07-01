"""
ゲームオブジェクト基底クラス
全オブジェクトが共通で持つ座標変換・描画機能を提供する。
描画はプレイヤー基準の相対座標で行う。
透視変換により奥行き感を表現する（非線形）。
"""
import pygame
from config import (
    CENTER_X, GROUND_Y, HORIZON_Y,
    PERSPECTIVE_DEPTH, SCALE_FACTOR, MIN_SCALE,
    PLAYER_SCREEN_X
)


class GameObject:
    """全ゲームオブジェクトの基底クラス"""

    def __init__(self, x: float, z: float):
        self.x = x
        self.z = z
        self.alive = True

    def get_scale_relative(self, relative_z: float) -> float:
        """相対z座標に応じたスケール値を計算する"""
        if relative_z <= 0:
            return 1.0
        scale = 1.0 / (1.0 + relative_z * SCALE_FACTOR)
        return max(scale, MIN_SCALE)

    @staticmethod
    def perspective_t(relative_z: float) -> float:
        """相対z座標を透視変換パラメータ t (0.0〜1.0) に変換する。

        非線形変換: t = 1 - PERSPECTIVE_DEPTH / (PERSPECTIVE_DEPTH + relative_z)
        relative_z=0 → t=0（手前、GROUND_Y）
        relative_z=∞ → t→1.0（水平線、HORIZON_Y）
        奥へ行くほど t の変化量が小さくなり、横線が密集して見える。
        """
        if relative_z <= 0:
            return 0.0
        return 1.0 - PERSPECTIVE_DEPTH / (PERSPECTIVE_DEPTH + relative_z)

    @staticmethod
    def relative_z_to_screen_y(relative_z: float) -> int:
        """相対z座標から画面Y座標を計算する（透視変換）"""
        t = GameObject.perspective_t(relative_z)
        return int(GROUND_Y + (HORIZON_Y - GROUND_Y) * t)

    def world_to_screen_relative(self, player_x: float, player_z: float) -> tuple[int, int]:
        """プレイヤー基準の相対座標から画面座標に変換する

        透視変換により、奥ほど画面Y座標がHORIZON_Yに漸近的に近づく（非線形）。
        """
        relative_x = self.x - player_x
        relative_z = self.z - player_z

        # 手前のオブジェクト（プレイヤーより後ろ）は描画しない
        if relative_z < 0:
            return -1000, -1000  # 画面外

        scale = self.get_scale_relative(relative_z)

        # 画面X座標：中央 + 相対xをスケーリング
        screen_x = int(PLAYER_SCREEN_X + relative_x * scale)

        # 画面Y座標：透視変換による非線形補間
        screen_y = self.relative_z_to_screen_y(relative_z)

        return screen_x, screen_y

    def update(self):
        """毎フレーム更新（サブクラスでオーバーライド）"""
        pass

    def draw(self, surface: pygame.Surface, player_x: float, player_z: float):
        """描画（サブクラスでオーバーライド）"""
        pass
