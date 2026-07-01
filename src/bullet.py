"""
銃弾クラス
プレイヤーから発射され、z方向に直進する。
サイバー空間風のシアン/緑系の光弾。
"""
import pygame
from game_object import GameObject
from config import (
    BULLET_SPEED, BULLET_MAX_RANGE, COLOR_BULLET
)


class Bullet(GameObject):
    """銃弾クラス"""

    def __init__(self, x: float, z: float):
        super().__init__(x, z)
        self.speed = BULLET_SPEED
        self.start_z = z

    def update(self):
        """毎フレーム前進する"""
        self.z += self.speed

        # 最大射程を超えたら消滅
        if self.z - self.start_z > BULLET_MAX_RANGE:
            self.alive = False

    def draw(self, surface: pygame.Surface, player_x: float, player_z: float):
        """弾を描画する（サイバー風のネオン光弾）"""
        if not self.alive:
            return

        sx, sy = self.world_to_screen_relative(player_x, player_z)
        relative_z = self.z - player_z
        scale = self.get_scale_relative(relative_z)

        # 手前（プレイヤーより後ろ）は描画しない
        if relative_z < 0:
            return

        # 弾の大きさ（奥行きでスケーリング）
        radius = max(2, int(5 * scale))

        # 弾の光彩（外側のグロウ、サイバー風シアン/緑）
        glow_radius = radius + max(1, int(3 * scale))
        glow_surface = pygame.Surface((glow_radius * 4, glow_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surface, (0, 200, 150, 80),
            (glow_radius * 2, glow_radius * 2), glow_radius
        )
        surface.blit(glow_surface,
                      (sx - glow_radius * 2, sy - glow_radius * 2))

        # 弾本体
        pygame.draw.circle(surface, COLOR_BULLET, (sx, sy), radius)
        # 中心の白い光
        if radius > 2:
            pygame.draw.circle(surface, (200, 255, 240), (sx, sy), max(1, radius // 2))
